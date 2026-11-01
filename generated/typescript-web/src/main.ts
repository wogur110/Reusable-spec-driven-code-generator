type Meta = { key: 'state'; username: string | null; receive_cursor: number; next_local_order: number };
type Send = { message_id: string; sender: string; recipient: string; text: string };
type Message = Send & { sequence: number };
type Problem = { code: string; message: string; field: string | null };
type Outgoing = Send & { local_order: number; state: 'queued' | 'accepted' | 'failed'; server_sequence: number | null; error: Problem | null };
type Snapshot = { meta: Meta; inbox: Message[]; outbox: Outgoing[] };
type Connection = 'unknown' | 'online' | 'offline' | 'error';
const MAX = Number.MAX_SAFE_INTEGER;
const initial = (): Meta => ({ key: 'state', username: null, receive_cursor: 0, next_local_order: 1 });
const el = <T extends HTMLElement = HTMLElement>(id: string): T => document.querySelector(`[data-testid="${id}"]`)!;
const root = el('app-ready'), errorLabel = el('error-message');
const usernameInput = el<HTMLInputElement>('username-input'), recipientInput = el<HTMLInputElement>('recipient-input');
const messageInput = el<HTMLTextAreaElement>('message-input'), mode = el<HTMLSelectElement>('transport-mode');
const loginForm = document.querySelector<HTMLFormElement>('#login-form')!;
const sendForm = document.querySelector<HTMLFormElement>('#send-form')!;
const resetPanel = document.querySelector<HTMLElement>('#reset-panel')!;
let db: IDBDatabase;
let snapshot: Snapshot = { meta: initial(), inbox: [], outbox: [] };
let ready = false, busy = false, resetting = false, paused = false, stopped = false;
let generation = 0, running = false, wakePending = false;
let timer: ReturnType<typeof setTimeout> | undefined;
let controller: AbortController | undefined;
let connection: Connection = 'unknown';
const transactions = new Set<Promise<unknown>>();
function problem(code: string, message: string, field: string | null = null): Problem { return { code, message, field }; }
function describe(e: unknown): string { return e instanceof Error ? e.message : String(e); }
function failLocal(e: unknown) { errorLabel.textContent = describe(e); }
function nameValid(x: unknown): x is string { return typeof x === 'string' && /^[a-z][a-z0-9_]{0,31}(?![\s\S])/.test(x); }
function integer(x: unknown, min = 0): x is number { return typeof x === 'number' && Number.isSafeInteger(x) && x >= min; }
function textValid(x: unknown): x is string {
  if (typeof x !== 'string' || !x.length) return false;
  for (const c of x) { const n = c.codePointAt(0)!; if (n >= 0xd800 && n <= 0xdfff) return false; }
  return new TextEncoder().encode(x).length <= 4096;
}
function uuid(x: unknown): x is string { return typeof x === 'string' && x.length === 36 && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(x); }
function exact(x: unknown, keys: string[]): x is Record<string, unknown> {
  return !!x && typeof x === 'object' && !Array.isArray(x) && Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x, k));
}
function messageValid(x: unknown): x is Message {
  return exact(x, ['message_id','sender','recipient','text','sequence']) && uuid(x.message_id) && nameValid(x.sender) && nameValid(x.recipient) && x.sender !== x.recipient && textValid(x.text) && integer(x.sequence, 1);
}
const errorMap: Record<string, { status: number; fields: (string | null)[] }> = {
  INVALID_REQUEST:{status:400,fields:[null]}, INVALID_JSON:{status:400,fields:[null]}, INVALID_FIELDS:{status:400,fields:[null]},
  INVALID_MESSAGE_ID:{status:400,fields:['message_id']}, INVALID_USERNAME:{status:400,fields:['sender','recipient']},
  SELF_SEND:{status:400,fields:['recipient']}, INVALID_TEXT:{status:400,fields:['text']}, INVALID_QUERY:{status:400,fields:['after',null]},
  NOT_FOUND:{status:404,fields:[null]}, METHOD_NOT_ALLOWED:{status:405,fields:[null]}, IDEMPOTENCY_CONFLICT:{status:409,fields:['message_id']},
  CURSOR_INVALID:{status:409,fields:['after']}, PAYLOAD_TOO_LARGE:{status:413,fields:[null]}, UNSUPPORTED_MEDIA_TYPE:{status:415,fields:[null]},
  SEQUENCE_EXHAUSTED:{status:503,fields:[null]}, INTERNAL_ERROR:{status:500,fields:[null]}
};
function wireProblem(body: unknown, status: number): Problem | null {
  if (!exact(body, ['error']) || !exact(body.error, ['code','message','field'])) return null;
  const e = body.error;
  if (typeof e.code !== 'string' || typeof e.message !== 'string' || !e.message.length || !(e.field === null || typeof e.field === 'string')) return null;
  const rule = errorMap[e.code];
  return rule && rule.status === status && rule.fields.includes(e.field) ? e as Problem : null;
}
function request<T>(r: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => { r.onsuccess = () => resolve(r.result); r.onerror = () => reject(r.error); });
}
async function transact<T>(stores: string[], access: IDBTransactionMode, work: (tx: IDBTransaction) => Promise<T>): Promise<T> {
  const tx = db.transaction(stores, access);
  const complete = new Promise<void>((resolve, reject) => {
    tx.oncomplete = () => resolve(); tx.onabort = () => reject(tx.error ?? new Error('Transaction aborted')); tx.onerror = () => {};
  });
  // Attach immediately so an aborted transaction never produces an unhandled rejection.
  const guarded = complete.catch(() => {});
  transactions.add(guarded);
  try {
    const result = await work(tx);
    await complete;
    return result;
  } catch (e) {
    try { tx.abort(); } catch { /* Already completed or aborted. */ }
    await guarded;
    throw e;
  } finally { transactions.delete(guarded); }
}
async function openStore(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    let abandoned = false;
    const r = indexedDB.open('reusable-spec-messenger', 1);
    r.onupgradeneeded = event => {
      if (event.oldVersion !== 0) { r.transaction!.abort(); return; }
      const d = r.result;
      d.createObjectStore('metadata', { keyPath: 'key' }).add(initial());
      d.createObjectStore('outbox', { keyPath: 'message_id' }).createIndex('by_order','local_order',{unique:true});
      d.createObjectStore('inbox', { keyPath: ['sender','message_id'] }).createIndex('by_sequence','sequence',{unique:true});
    };
    r.onblocked = () => { abandoned = true; reject(new Error('STORAGE_UNAVAILABLE: Database open blocked. Close other tabs and reopen.')); };
    r.onerror = () => reject(new Error(`STORAGE_UNAVAILABLE: Unsupported database version or unavailable storage: ${r.error?.message}`));
    r.onsuccess = () => {
      if (abandoned) { r.result.close(); return; }
      const d = r.result;
      try {
        if (d.version !== 1 || Array.from(d.objectStoreNames).sort().join(',') !== 'inbox,metadata,outbox') throw new Error('Unsupported database schema');
        const tx = d.transaction(['metadata','outbox','inbox']);
        for (const [store, key, index, indexKey] of [
          ['metadata', 'key', '', ''], ['outbox', 'message_id', 'by_order', 'local_order'], ['inbox', ['sender','message_id'], 'by_sequence', 'sequence']
        ] as const) {
          const s = tx.objectStore(store);
          if (JSON.stringify(s.keyPath) !== JSON.stringify(key) || s.autoIncrement) throw new Error('Unsupported database schema');
          if (index && (!s.indexNames.contains(index) || s.index(index).keyPath !== indexKey || !s.index(index).unique || s.index(index).multiEntry)) throw new Error('Unsupported database index');
        }
        resolve(d);
      } catch (e) { d.close(); reject(e); }
    };
  });
}
async function readSnapshot(): Promise<Snapshot> {
  return transact(['metadata','inbox','outbox'], 'readonly', async tx => {
    const [meta, inbox, outbox] = await Promise.all([
      request<Meta>(tx.objectStore('metadata').get('state')),
      request<Message[]>(tx.objectStore('inbox').index('by_sequence').getAll()),
      request<Outgoing[]>(tx.objectStore('outbox').index('by_order').getAll())
    ]);
    if (!meta || meta.key !== 'state' || !(meta.username === null || nameValid(meta.username)) || !integer(meta.receive_cursor) || !integer(meta.next_local_order,1)) throw new Error('Unsupported or corrupt stored metadata');
    return { meta, inbox, outbox };
  });
}
function controls() {
  const enabled = ready && !stopped && !resetting;
  loginForm.hidden = snapshot.meta.username !== null;
  document.querySelector<HTMLElement>('#identity')!.hidden = snapshot.meta.username === null;
  el('current-user').textContent = snapshot.meta.username ?? '';
  (el<HTMLButtonElement>('login-button')).disabled = !enabled || busy;
  usernameInput.disabled = !enabled || busy;
  recipientInput.disabled = !enabled || !snapshot.meta.username || paused;
  messageInput.disabled = recipientInput.disabled;
  el<HTMLButtonElement>('send-button').disabled = recipientInput.disabled || busy;
  el<HTMLButtonElement>('reset-button').disabled = !enabled;
  el<HTMLButtonElement>('reset-confirm').disabled = !enabled || busy;
  root.dataset.ready = String(ready && !stopped);
}
function connectionView(state: Connection, detail = '') {
  connection = state;
  const label = el('connection-status'); label.dataset.state = state;
  label.textContent = `${state[0].toUpperCase()}${state.slice(1)}${detail ? ': ' + detail : ''}`;
}
function child(parent: HTMLElement, id: string, value: string) { const p = document.createElement('p'); p.dataset.testid = id; p.textContent = value; parent.append(p); }
function render() {
  controls();
  const inbox = el('inbox'), outbox = el('outbox'); inbox.replaceChildren(); outbox.replaceChildren();
  for (const m of snapshot.inbox) {
    const row = document.createElement('article'); Object.assign(row.dataset, { testid:'inbox-item', messageId:m.message_id, sender:m.sender, sequence:String(m.sequence) });
    child(row,'message-sender',m.sender); child(row,'message-text',m.text); inbox.append(row);
  }
  for (const m of snapshot.outbox) {
    const row = document.createElement('article'); Object.assign(row.dataset, { testid:'outbox-item', messageId:m.message_id, state:m.state, localOrder:String(m.local_order) });
    child(row,'message-recipient',m.recipient); child(row,'message-text',m.text);
    child(row,'message-state',m.state === 'accepted' ? 'accepted by server' : m.state);
    child(row,'message-error',m.error ? `${m.error.code}: ${m.error.message}` : ''); outbox.append(row);
  }
  if (!snapshot.inbox.length) inbox.textContent = 'No received messages yet.';
  if (!snapshot.outbox.length) outbox.textContent = 'No outgoing messages yet.';
}
async function refresh(token = generation) { const s = await readSnapshot(); if (token === generation) { snapshot = s; render(); } }
function storageError(e: unknown) { failLocal(new Error(`STORAGE_UNAVAILABLE: ${describe(e)}`)); connectionView('error', 'Local storage unavailable'); }
function active(token: number) { return token === generation && !stopped && !resetting; }

// All requests, including the development offline control, use this transport.
async function transport(path: string, payload?: Send): Promise<{ status: number; body: unknown; validJSON: boolean }> {
  if (mode.value === 'offline') throw new Error('OFFLINE: Development transport is offline. Reconnect to retry.');
  const abort = new AbortController(); controller = abort;
  const deadline = setTimeout(() => abort.abort(), 5000);
  let status: number | undefined;
  try {
    const response = await fetch(path, { method: payload ? 'POST' : 'GET', headers: payload ? {'Content-Type':'application/json'} : {}, body: payload ? JSON.stringify(payload) : undefined, cache:'no-store', redirect:'error', signal:abort.signal });
    status = response.status;
    const media = response.headers.get('content-type') ?? '';
    const encoding = response.headers.get('content-encoding');
    const validMedia = /^application\/json(?:\s*;\s*charset\s*=\s*utf-8)?\s*$/i.test(media) && !encoding;
    const bytes = await response.arrayBuffer();
    let body: unknown = null, validJSON = false;
    if (validMedia) {
      try {
        const raw = new TextDecoder('utf-8', { fatal:true, ignoreBOM:true }).decode(bytes);
        body = JSON.parse(raw); validJSON = true;
      } catch { /* The known status still determines permanent send rejection. */ }
    }
    return { status, body, validJSON };
  } catch (e) {
    if (status !== undefined) return { status, body:null, validJSON:false };
    throw new Error(abort.signal.aborted ? 'TIMEOUT: Request exceeded five seconds; retrying.' : `NETWORK_ERROR: ${describe(e)}; retrying.`);
  } finally { clearTimeout(deadline); if (controller === abort) controller = undefined; }
}
async function sendHead(token: number): Promise<Connection> {
  const s = await readSnapshot();
  if (!active(token) || paused) return 'unknown';
  const head = s.outbox.find(m => m.state === 'queued'); if (!head) return 'unknown';
  const payload: Send = {message_id:head.message_id,sender:head.sender,recipient:head.recipient,text:head.text};
  let state: Outgoing['state'] = 'queued', sequence: number | null = null, error: Problem | null = null;
  let observation: Connection = 'online';
  try {
    const response = await transport('/api/v1/messages', payload);
    if (!active(token)) return 'unknown';
    const { status, body, validJSON } = response;
    if (status === 200 || status === 201) {
      if (validJSON && exact(body,['message_id','sender','recipient','sequence']) && body.message_id === head.message_id && body.sender === head.sender && body.recipient === head.recipient && integer(body.sequence,1)) { state = 'accepted'; sequence = body.sequence; }
      else { error = problem('PROTOCOL_ERROR','Invalid receipt; retrying the same message.'); observation = 'error'; }
    } else {
      error = (validJSON && wireProblem(body,status)) || problem('HTTP_ERROR',`Server returned HTTP ${status}.`);
      if (status >= 400 && status < 500 && status !== 408 && status !== 429) state = 'failed';
      else if (!(status === 408 || status === 429 || status >= 500 && status < 600)) error = problem('PROTOCOL_ERROR',`Unexpected HTTP ${status}; retrying.`);
      observation = 'error';
    }
  } catch (e) { error = problem('NETWORK_ERROR',describe(e)); observation = 'offline'; }
  if (!active(token)) return 'unknown';
  await transact(['outbox'],'readwrite', async tx => {
    const store = tx.objectStore('outbox'); const current: Outgoing | undefined = await request(store.get(head.message_id));
    if (!active(token) || !current || current.state !== 'queued') return;
    await request(store.put({...current,state,server_sequence:sequence,error}));
  });
  return observation;
}
function validatePage(body: unknown, username: string, after: number): { messages: Message[]; next_after: number } {
  if (!exact(body,['messages','next_after']) || !Array.isArray(body.messages) || body.messages.length > 100 || !integer(body.next_after)) throw new Error('Invalid page schema');
  const keys = new Set<string>(); let expected = after;
  for (const m of body.messages) {
    if (!messageValid(m) || m.recipient !== username || m.sequence !== expected + 1) throw new Error('Invalid incoming message or noncontiguous sequence');
    const key = `${m.sender}/${m.message_id}`; if (keys.has(key)) throw new Error('Repeated message key'); keys.add(key); expected = m.sequence;
  }
  if (body.next_after !== expected) throw new Error('Invalid next_after');
  return body as { messages: Message[]; next_after: number };
}
async function receivePage(token: number): Promise<Connection> {
  const s = await readSnapshot(), user = s.meta.username, after = s.meta.receive_cursor;
  if (!user || !active(token) || paused) return 'unknown';
  let response: Awaited<ReturnType<typeof transport>>;
  try { response = await transport(`/api/v1/messages?recipient=${encodeURIComponent(user)}&after=${after}`); }
  catch (e) { if (active(token)) connectionView('offline',describe(e)); return 'offline'; }
  if (!active(token)) return 'unknown';
  const err = response.validJSON ? wireProblem(response.body,response.status) : null;
  if (err?.code === 'CURSOR_INVALID') {
    paused = true; failLocal(new Error('CURSOR_INVALID: Server session changed. Reset local store before continuing.')); controls(); return 'error';
  }
  if (response.status !== 200 || !response.validJSON) { connectionView('error',err ? `${err.code}: ${err.message}` : 'PROTOCOL_ERROR: Invalid incoming response; retrying.'); return 'error'; }
  let page: ReturnType<typeof validatePage>;
  try { page = validatePage(response.body,user,after); }
  catch (e) { connectionView('error',`PROTOCOL_ERROR: ${describe(e)}; retrying.`); return 'error'; }
  try {
    await transact(['metadata','inbox'],'readwrite', async tx => {
      const metadata = tx.objectStore('metadata'), inbox = tx.objectStore('inbox');
      const meta: Meta = await request(metadata.get('state'));
      if (!active(token) || meta.username !== user || meta.receive_cursor !== after) return;
      for (const m of page.messages) {
        const existing: Message | undefined = await request(inbox.get([m.sender,m.message_id]));
        const bySequence: Message | undefined = await request(inbox.index('by_sequence').get(m.sequence));
        if (existing && (existing.recipient !== m.recipient || existing.text !== m.text || existing.sequence !== m.sequence)) throw new Error('PROTOCOL_ERROR: Conflicting incoming message');
        if (bySequence && (bySequence.sender !== m.sender || bySequence.message_id !== m.message_id)) throw new Error('PROTOCOL_ERROR: Conflicting incoming sequence');
        if (!existing) await request(inbox.add(m));
      }
      if (!active(token)) { tx.abort(); return; }
      await request(metadata.put({...meta, receive_cursor:page.next_after}));
    });
  } catch (e) {
    if (describe(e).startsWith('PROTOCOL_ERROR')) connectionView('error',describe(e)); else storageError(e);
    return 'error';
  }
  return 'online';
}
function wake() {
  if (!ready || !snapshot.meta.username || stopped || resetting || paused) return;
  if (running) { wakePending = true; return; }
  clearTimeout(timer); timer = setTimeout(() => { void cycle(); },0);
}
async function cycle() {
  if (running || !ready || !snapshot.meta.username || stopped || resetting || paused) return;
  running = true; wakePending = false; const token = generation;
  let outgoing: Connection = 'unknown', incoming: Connection = 'unknown';
  try {
    try { outgoing = await sendHead(token); } catch (e) { if (active(token)) storageError(e); outgoing = 'error'; }
    if (active(token) && !paused) {
      try { incoming = await receivePage(token); } catch (e) { storageError(e); incoming = 'error'; }
    }
    if (active(token)) {
      const state: Connection = outgoing === 'error' || incoming === 'error' ? 'error' : outgoing === 'offline' || incoming === 'offline' ? 'offline' : 'online';
      if (state !== connection || state === 'online') connectionView(state, paused ? 'Reset required' : '');
      await refresh(token);
    }
  } catch (e) { if (active(token)) storageError(e); }
  finally {
    running = false;
    if (ready && snapshot.meta.username && !stopped && !resetting && !paused) {
      timer = setTimeout(() => { void cycle(); }, wakePending ? 0 : 1000);
    }
  }
}
loginForm.addEventListener('submit', event => {
  event.preventDefault(); if (!ready || busy || resetting || stopped) return;
  const user = usernameInput.value;
  if (!nameValid(user)) { failLocal(new Error('INVALID_USERNAME: Use 1–32 lowercase ASCII letters, digits or underscores, starting with a letter.')); return; }
  busy = true; controls(); const token = generation;
  void (async () => {
    try {
      await transact(['metadata'],'readwrite', async tx => {
        const store = tx.objectStore('metadata'), meta: Meta = await request(store.get('state'));
        if (meta.username && meta.username !== user) throw new Error('Reset the local store to change identity.');
        if (!active(token)) throw new Error('Identity action canceled');
        await request(store.put({...meta, username:user}));
      });
      if (active(token)) { errorLabel.textContent = ''; await refresh(token); wake(); }
    } catch (e) { if (active(token)) storageError(e); }
    finally { busy = false; controls(); }
  })();
});
sendForm.addEventListener('submit', event => {
  event.preventDefault(); if (!ready || busy || resetting || stopped || paused || !snapshot.meta.username) return;
  const user = snapshot.meta.username, recipient = recipientInput.value, text = messageInput.value;
  if (!nameValid(recipient)) { failLocal(new Error('INVALID_USERNAME: Enter a valid recipient.')); return; }
  if (user === recipient) { failLocal(new Error('SELF_SEND: Choose a different recipient.')); return; }
  if (!textValid(text)) { failLocal(new Error('INVALID_TEXT: Enter 1–4096 UTF-8 bytes of valid Unicode text.')); return; }
  const token = generation; busy = true; controls();
  void (async () => {
    try {
      await transact(['metadata','outbox'],'readwrite', async tx => {
        const metadata = tx.objectStore('metadata'), outbox = tx.objectStore('outbox');
        const meta: Meta = await request(metadata.get('state'));
        if (!active(token) || meta.username !== user) throw new Error('Enqueue canceled');
        if (!integer(meta.next_local_order,1) || meta.next_local_order === MAX) throw new Error('LOCAL_ORDER_EXHAUSTED: Reset local store to allocate more messages.');
        let id: string;
        do { id = crypto.randomUUID(); } while (await request(outbox.get(id)));
        const record: Outgoing = {message_id:id,sender:user,recipient,text,local_order:meta.next_local_order,state:'queued',server_sequence:null,error:null};
        await request(outbox.add(record)); await request(metadata.put({...meta,next_local_order:meta.next_local_order+1}));
      });
      if (active(token)) { if (messageInput.value === text) messageInput.value = ''; errorLabel.textContent = ''; await refresh(token); wake(); }
    } catch (e) { if (active(token)) storageError(e); }
    finally { busy = false; controls(); }
  })();
});
el('reset-button').addEventListener('click', () => { resetPanel.hidden = false; });
el('reset-cancel').addEventListener('click', () => { resetPanel.hidden = true; });
el('reset-confirm').addEventListener('click', () => {
  if (!ready || resetting || busy || stopped) return;
  resetting = true; generation++; clearTimeout(timer); controller?.abort(); controls();
  void (async () => {
    try {
      await Promise.all([...transactions]);
      await transact(['metadata','inbox','outbox'],'readwrite', async tx => {
        await Promise.all(['metadata','inbox','outbox'].map(name => request(tx.objectStore(name).clear())));
        await request(tx.objectStore('metadata').put(initial()));
      });
      paused = false; mode.value = 'online'; connectionView('unknown'); errorLabel.textContent = '';
      usernameInput.value = ''; recipientInput.value = ''; messageInput.value = ''; resetPanel.hidden = true;
      await refresh();
    } catch (e) { storageError(e); }
    finally { resetting = false; controls(); wake(); }
  })();
});
mode.addEventListener('change', () => {
  if (mode.value === 'offline') connectionView('offline','Development transport is offline');
  wake();
});
window.addEventListener('online',wake);
window.addEventListener('offline',() => { connectionView('offline','Browser reports offline'); wake(); });
window.addEventListener('focus',wake);
document.addEventListener('visibilitychange',() => { if (document.visibilityState === 'visible') wake(); });
window.addEventListener('pagehide',() => { stopped = true; generation++; clearTimeout(timer); controller?.abort(); db?.close(); });
window.addEventListener('pageshow',event => { if (event.persisted) location.reload(); });
void (async () => {
  try {
    db = await openStore();
    db.onversionchange = () => {
      stopped = true; generation++; clearTimeout(timer); controller?.abort(); db.close();
      failLocal(new Error('STORAGE_UNAVAILABLE: Database version changed. Close this tab and reopen.')); connectionView('error'); controls();
    };
    snapshot = await readSnapshot(); ready = true; render(); wake();
  } catch (e) { failLocal(new Error(`STORAGE_UNAVAILABLE: ${describe(e)}`)); connectionView('error','Cannot open local store'); controls(); }
})();
