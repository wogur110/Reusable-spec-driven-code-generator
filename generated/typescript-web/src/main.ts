// Independent browser implementation. All UI operations use the durable store
// and the single serialized scheduler below; there is no test-only transport.
type State = 'queued' | 'accepted' | 'failed';
type Observation = 'unknown' | 'pending' | 'confirmed' | 'error';
interface Meta { key: 'state'; username: string | null; receive_cursor: number; next_local_order: number }
interface Message { message_id: string; sender: string; recipient: string; text: string; sequence: number }
interface Outgoing { message_id: string; sender: string; recipient: string; text: string; local_order: number; state: State; server_sequence: number | null; error: string | null }
interface User { username: string; online: boolean }
interface Snapshot { meta: Meta; inbox: Message[]; outbox: Outgoing[] }
const fresh = (): Meta => ({key:'state', username:null, receive_cursor:0, next_local_order:1});
const MAX = Number.MAX_SAFE_INTEGER;
const username = (v: unknown): v is string => typeof v === 'string' && /^[a-z][a-z0-9_]{0,31}(?![\s\S])/.test(v);
const uuid = (v: unknown): v is string => typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?![\s\S])/.test(v);
const integer = (v: unknown, min=0): v is number => typeof v === 'number' && Number.isSafeInteger(v) && v >= min;
function validText(v: unknown): v is string {
  if (typeof v !== 'string' || !v.length) return false;
  for (let i=0;i<v.length;i++) {
    const c=v.charCodeAt(i);
    if (c>=0xd800 && c<=0xdbff) {
      const low=v.charCodeAt(++i);
      if (!(low>=0xdc00 && low<=0xdfff)) return false;
    } else if (c>=0xdc00 && c<=0xdfff) return false;
  }
  return new TextEncoder().encode(v).length<=4096;
}
function exact(v: unknown, keys: string[]): v is Record<string, unknown> {
  return typeof v==='object' && v!==null && !Array.isArray(v) && Object.keys(v).length===keys.length && keys.every(k=>Object.hasOwn(v,k));
}
function check(condition: unknown, description='Invalid response schema.'): asserts condition {
  if (!condition) throw new Failure('PROTOCOL_ERROR',description);
}
class Failure extends Error {
  constructor(public code: string, message: string, public status=0, public transport=false) { super(`${code}: ${message}`); }
}
const reason = (e: unknown): string => e instanceof Error ? e.message : String(e);
function request<T>(r: IDBRequest<T>): Promise<T> {
  return new Promise((resolve,reject)=>{ r.onsuccess=()=>resolve(r.result); r.onerror=()=>reject(r.error); });
}
function done(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve,reject)=>{tx.oncomplete=()=>resolve();tx.onabort=()=>reject(tx.error??new Error('Transaction aborted.'));tx.onerror=()=>{ /* abort reports the final transaction outcome */ };});
}
let database: IDBDatabase;
async function transaction<T>(stores: string[], mode: IDBTransactionMode, body:(tx:IDBTransaction)=>Promise<T>): Promise<T> {
  const tx=database.transaction(stores,mode);
  const completion=done(tx);
  try { const value=await body(tx); await completion; return value; }
  catch(e) { try { tx.abort(); } catch { /* already complete */ } await completion.catch(()=>{}); throw e; }
}
function openStore(): Promise<IDBDatabase> {
  return new Promise((resolve,reject)=>{
    const r=indexedDB.open('reusable-spec-messenger',1);
    let rejected=false;
    r.onblocked=()=>{rejected=true;reject(new Error('Database upgrade blocked. Close other tabs and reopen.'));};
    r.onerror=()=>reject(r.error);
    r.onupgradeneeded=event=>{
      if (event.oldVersion!==0) { r.transaction?.abort(); return; }
      const db=r.result;
      db.createObjectStore('metadata',{keyPath:'key'}).put(fresh());
      db.createObjectStore('outbox',{keyPath:'message_id'}).createIndex('by_order','local_order',{unique:true});
      db.createObjectStore('inbox',{keyPath:['sender','message_id']}).createIndex('by_sequence','sequence',{unique:true});
    };
    r.onsuccess=()=>{
      const db=r.result;
      if(rejected){db.close();return;}
      try {
        if(db.version!==1 || [...db.objectStoreNames].sort().join(',')!=='inbox,metadata,outbox') throw new Error('Unsupported database schema.');
        const tx=db.transaction(['metadata','outbox','inbox']);
        const meta=tx.objectStore('metadata'), out=tx.objectStore('outbox'), inbox=tx.objectStore('inbox');
        if(meta.keyPath!=='key'||out.keyPath!=='message_id'||JSON.stringify(inbox.keyPath)!=='["sender","message_id"]'||!out.index('by_order').unique||out.index('by_order').keyPath!=='local_order'||!inbox.index('by_sequence').unique||inbox.index('by_sequence').keyPath!=='sequence'||meta.autoIncrement||out.autoIncrement||inbox.autoIncrement||meta.indexNames.length!==0||out.indexNames.length!==1||inbox.indexNames.length!==1||out.index('by_order').multiEntry||inbox.index('by_sequence').multiEntry) throw new Error('Unsupported database schema.');
        resolve(db);
      } catch(e){db.close();reject(e);}
    };
  });
}
async function snapshot(): Promise<Snapshot> {
  return transaction(['metadata','inbox','outbox'],'readonly',async tx=>{
    const mr=request(tx.objectStore('metadata').get('state'));
    const ir=request(tx.objectStore('inbox').index('by_sequence').getAll());
    const or=request(tx.objectStore('outbox').index('by_order').getAll());
    const [meta,inbox,outbox]=await Promise.all([mr,ir,or]);
    if(!exact(meta,['key','username','receive_cursor','next_local_order'])||meta.key!=='state'||!(meta.username===null||username(meta.username))||!integer(meta.receive_cursor)||!integer(meta.next_local_order,1)) throw new Error('Unsupported or corrupt metadata. Reopen the application; data was preserved.');
    return {meta:meta as unknown as Meta,inbox:inbox as Message[],outbox:outbox as Outgoing[]};
  });
}
const el = <T extends HTMLElement=HTMLElement>(id:string):T => {
  const node=document.querySelector<T>(`[data-testid="${id}"]`);
  if(!node) throw new Error(`Missing UI control ${id}`);
  return node;
};
const byId=(id:string):HTMLElement=>document.getElementById(id)!;
const root=el('app-ready');
const nameInput=el<HTMLInputElement>('username-input'), recipientInput=el<HTMLInputElement>('recipient-input'), draft=el<HTMLTextAreaElement>('message-input');
const modeControl=el<HTMLSelectElement>('transport-mode');
let data:Snapshot={meta:fresh(),inbox:[],outbox:[]};
let ready=false, closing=false, resetting=false, paused=false, busy=false;
let generation=0, revision=0, online=true;
let connection:'unknown'|'online'|'offline'|'error'='unknown';
let formError='', syncError='', storeError='';
let directory:User[]=[], directoryState='loading', receiptState:Observation='unknown', presenceState:Observation='unknown';
let directoryError='', receiptError='', presenceError='';
let selectedIncoming='', selectedOutgoing='', selectedUser='';
let presencePending=false, presenceConfirmed=false;
let activeAbort:AbortController|null=null;
let running=false, wakePending=false, timer:ReturnType<typeof setTimeout>|null=null;
const live=(g:number)=>g===generation&&!closing&&!resetting;
const ordinary=(g:number,r:number)=>live(g)&&ready&&!paused&&online&&r===revision&&!!data.meta.username;
function controls():void {
  root.dataset.ready=String(ready&&!resetting);
  const logged=!!data.meta.username;
  byId('login-form').hidden=logged;
  byId('identity').hidden=!logged;
  el('current-user').textContent=data.meta.username??'';
  nameInput.disabled=!ready||busy||resetting;
  el<HTMLButtonElement>('login-button').disabled=!ready||busy||resetting;
  recipientInput.disabled=!ready||!logged||paused||resetting;
  draft.disabled=!ready||!logged||paused||resetting;
  el<HTMLButtonElement>('send-button').disabled=!ready||!logged||paused||busy||resetting;
  el<HTMLButtonElement>('reset-button').disabled=!ready||resetting;
  el<HTMLButtonElement>('reset-confirm').disabled=resetting;
  el('connection-status').textContent=connection;
  el('connection-status').dataset.state=connection;
  el('error-message').textContent=[formError,storeError,syncError].filter(Boolean).join('\n');
  el('directory-status').textContent=directoryState;
  el('receipt-status').textContent=receiptState;
  el('presence-status').textContent=presenceState;
  byId('feature-error').textContent=[directoryError,receiptError,presenceError].filter(Boolean).join(' | ');
}
function cell(row:HTMLTableRowElement,text:string,testid?:string):void {
  const td=document.createElement('td'); td.textContent=text;
  if(testid) td.dataset.testid=testid;
  row.append(td);
}
function messageKey(m:Message):string { return `${m.sender}:${m.message_id}`; }
function renderMessages():void {
  const inbox=el('inbox'), outbox=el('outbox');
  const inFragment=document.createDocumentFragment(), outFragment=document.createDocumentFragment();
  for(const m of data.inbox){
    const row=document.createElement('tr'); row.tabIndex=0;
    row.dataset.testid='inbox-item';row.dataset.messageId=m.message_id;row.dataset.sender=m.sender;row.dataset.sequence=String(m.sequence);
    const key=messageKey(m); row.classList.toggle('selected',selectedIncoming===key);row.setAttribute('aria-selected',String(selectedIncoming===key));
    cell(row,m.message_id);cell(row,m.sender,'message-sender');cell(row,m.text,'message-text');cell(row,String(m.sequence));
    const select=()=>{selectedIncoming=key;selectRows('inbox',key);el('inbox-detail').textContent=m.text;};
    row.onclick=select;row.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};inFragment.append(row);
  }
  for(const m of data.outbox){
    const row=document.createElement('tr');row.tabIndex=0;
    row.dataset.testid='outbox-item';row.dataset.messageId=m.message_id;row.dataset.state=m.state;row.dataset.localOrder=String(m.local_order);
    row.classList.toggle('selected',selectedOutgoing===m.message_id);row.setAttribute('aria-selected',String(selectedOutgoing===m.message_id));
    cell(row,m.message_id);cell(row,m.recipient,'message-recipient');cell(row,m.text,'message-text');cell(row,m.state==='accepted'?'accepted by server':m.state,'message-state');cell(row,m.error??'','message-error');cell(row,String(m.local_order));
    const select=()=>{selectedOutgoing=m.message_id;selectRows('outbox',m.message_id);el('outbox-detail').textContent=m.text;};
    row.onclick=select;row.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};outFragment.append(row);
  }
  inbox.replaceChildren(inFragment);outbox.replaceChildren(outFragment);
  byId('inbox-empty').hidden=data.inbox.length>0;byId('outbox-empty').hidden=data.outbox.length>0;
  el('inbox-detail').textContent=data.inbox.find(m=>messageKey(m)===selectedIncoming)?.text??'';
  el('outbox-detail').textContent=data.outbox.find(m=>m.message_id===selectedOutgoing)?.text??'';
}
function selectRows(container:string,key:string):void {
  for(const row of el(container).querySelectorAll<HTMLElement>('tr')){
    const match=container==='inbox'?`${row.dataset.sender}:${row.dataset.messageId}`===key:row.dataset.messageId===key;
    row.classList.toggle('selected',match);row.setAttribute('aria-selected',String(match));
  }
}
function renderDirectory():void {
  const filter=el<HTMLInputElement>('user-filter').value.toLowerCase();
  const fragment=document.createDocumentFragment();
  for(const user of directory){
    if(user.username===data.meta.username||!user.username.toLowerCase().includes(filter))continue;
    const button=document.createElement('button');button.type='button';button.dataset.testid='user-item';button.dataset.username=user.username;
    button.classList.toggle('selected',selectedUser===user.username);
    const name=document.createElement('span');name.dataset.testid='user-name';name.textContent=user.username;
    const presence=document.createElement('span');presence.dataset.testid='user-presence';presence.textContent=user.online?'recently seen':'not recently seen';
    button.append(name,presence);button.disabled=!data.meta.username||paused||resetting;
    button.onclick=()=>{recipientInput.value=user.username;selectedUser=user.username;renderDirectory();};fragment.append(button);
  }
  el('user-directory').replaceChildren(fragment);
}
async function refreshSnapshot(g=generation):Promise<void> {
  const value=await snapshot(); if(!live(g)) return;
  data=value;renderMessages();controls();
}
function storageFailure(e:unknown):void { storeError=`STORAGE_UNAVAILABLE: ${reason(e)} Data has not been cleared; retry or reopen.`;controls(); }
async function login():Promise<void> {
  if(!ready||busy||resetting||data.meta.username)return;
  const name=nameInput.value;
  formError='';
  if(!username(name)){formError='INVALID_USERNAME: Use 1–32 lowercase ASCII letters, digits or underscores, starting with a letter.';controls();return;}
  const g=generation;busy=true;controls();
  try {
    await transaction(['metadata'],'readwrite',async tx=>{
      const store=tx.objectStore('metadata');const meta:Meta=await request(store.get('state'));
      if(meta.username!==null&&meta.username!==name)throw new Error('Reset is required to change identity.');
      meta.username=name;await request(store.put(meta));
    });
    if(!live(g))return;
    storeError='';await refreshSnapshot(g);
    if(!live(g))return;
    directoryState=online?'loading':'stale';
    if(online){presencePending=true;presenceConfirmed=false;presenceState='pending';}
    wake();
  }catch(e){if(live(g))storageFailure(e);}finally{if(g===generation){busy=false;controls();}}
}
async function enqueue():Promise<void> {
  if(!ready||busy||resetting||paused||!data.meta.username)return;
  const recipient=recipientInput.value,text=draft.value,sender=data.meta.username;
  formError='';
  if(!username(recipient))formError='INVALID_USERNAME: Enter a valid lowercase recipient username.';
  else if(recipient===sender)formError='SELF_SEND: Choose a different recipient.';
  else if(!validText(text))formError='INVALID_TEXT: Enter 1–4,096 UTF-8 bytes of Unicode scalar text.';
  if(formError){controls();return;}
  const g=generation;busy=true;controls();
  try {
    await transaction(['metadata','outbox'],'readwrite',async tx=>{
      const ms=tx.objectStore('metadata'), out=tx.objectStore('outbox');
      const meta:Meta=await request(ms.get('state'));
      if(meta.username!==sender)throw new Error('Identity changed.');
      if(!integer(meta.next_local_order,1)||meta.next_local_order>=MAX)throw new Error('LOCAL_ORDER_EXHAUSTED: Reset the demo store before sending.');
      let id=crypto.randomUUID();
      while(await request(out.get(id)))id=crypto.randomUUID();
      const row:Outgoing={message_id:id,sender,recipient,text,local_order:meta.next_local_order,state:'queued',server_sequence:null,error:null};
      meta.next_local_order++;
      await request(out.add(row));await request(ms.put(meta));
    });
    if(!live(g))return;
    if(draft.value===text)draft.value='';storeError='';await refreshSnapshot(g);wake();
  }catch(e){if(live(g))storageFailure(e);}finally{if(g===generation){busy=false;controls();}}
}
const errors:Record<string,{status:number;fields:(string|null)[]}>= {
  INVALID_REQUEST:{status:400,fields:[null]},INVALID_JSON:{status:400,fields:[null]},INVALID_FIELDS:{status:400,fields:[null]},
  INVALID_MESSAGE_ID:{status:400,fields:['message_id']},INVALID_USERNAME:{status:400,fields:['sender','recipient','username']},SELF_SEND:{status:400,fields:['recipient']},INVALID_TEXT:{status:400,fields:['text']},INVALID_QUERY:{status:400,fields:['after',null]},
  NOT_FOUND:{status:404,fields:[null]},METHOD_NOT_ALLOWED:{status:405,fields:[null]},IDEMPOTENCY_CONFLICT:{status:409,fields:['message_id']},CURSOR_INVALID:{status:409,fields:['after','through']},PAYLOAD_TOO_LARGE:{status:413,fields:[null]},UNSUPPORTED_MEDIA_TYPE:{status:415,fields:[null]},SEQUENCE_EXHAUSTED:{status:503,fields:[null]},INTERNAL_ERROR:{status:500,fields:[null]},INVALID_RECEIPT:{status:400,fields:['through']},INVALID_PRESENCE:{status:400,fields:['online']}
};
interface Reply {status:number; value:unknown; parseError:string; wireError: {code:string;message:string;field:string|null}|null}
async function fetchJSON(path:string,body:unknown|undefined,deadline:number,g:number):Promise<Reply> {
  if(!live(g))throw new Failure('CANCELED','Identity changed.');
  const controller=new AbortController();activeAbort=controller;
  const alarm=setTimeout(()=>controller.abort(),deadline);
  let status=0;
  try {
    const response=await fetch(path,{method:body===undefined?'GET':'POST',body:body===undefined?undefined:JSON.stringify(body),headers:body===undefined?{'Accept':'application/json'}:{'Accept':'application/json','Content-Type':'application/json'},cache:'no-store',redirect:'error',signal:controller.signal});
    status=response.status;
    let value:unknown,parseError='';
    try {
      const bytes=await response.arrayBuffer();
      if(!/^application\/json(?:\s*;\s*charset\s*=\s*utf-8)?\s*$/i.test(response.headers.get('Content-Type')??''))throw new Error('Response must be UTF-8 application/json.');
      if(response.headers.get('Content-Encoding') && response.headers.get('Content-Encoding')!=='identity')throw new Error('Unsupported response encoding.');
      if(bytes.byteLength>=3){const b=new Uint8Array(bytes);if(b[0]===239&&b[1]===187&&b[2]===191)throw new Error('Unexpected UTF-8 BOM.');}
      value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
    }catch(e){parseError=reason(e);}
    if(!live(g))throw new Failure('CANCELED','Identity changed.');
    let wireError:Reply['wireError']=null;
    if(exact(value,['error'])&&exact(value.error,['code','message','field'])){
      const e=value.error;
      if(typeof e.code==='string'&&typeof e.message==='string'&&e.message.length>0&&(typeof e.field==='string'||e.field===null)&&errors[e.code]?.status===status&&errors[e.code].fields.includes(e.field))wireError=e as unknown as NonNullable<Reply['wireError']>;
    }
    return {status,value,parseError,wireError};
  }catch(e){
    // An observed permanent HTTP rejection stays permanent even if body reading fails.
    if(status>=400&&status<500&&status!==408&&status!==429)return {status,value:undefined,parseError:reason(e),wireError:null};
    if(e instanceof Failure)throw e;
    throw new Failure('TRANSPORT_ERROR','API unavailable or request timed out. Queued messages will retry.',status,true);
  }finally{clearTimeout(alarm);if(activeAbort===controller)activeAbort=null;}
}
function ensureSuccess(reply:Reply,statuses:number[]=[200]):unknown {
  if(!statuses.includes(reply.status))throw new Failure(reply.wireError?.code??'HTTP_ERROR',reply.wireError?.message??`HTTP ${reply.status}; retry later.`,reply.status);
  if(reply.parseError)throw new Failure('PROTOCOL_ERROR',reply.parseError,reply.status);
  return reply.value;
}
async function outcome(m:Outgoing,state:State,sequence:number|null,error:string|null,g:number):Promise<void> {
  if(!live(g))return;
  await transaction(['outbox'],'readwrite',async tx=>{
    const store=tx.objectStore('outbox');const row:Outgoing|undefined=await request(store.get(m.message_id));
    if(!live(g)||!row||row.sender!==m.sender||row.state!=='queued')return;
    await request(store.put({...row,state,server_sequence:sequence,error}));
  });
}
async function sendHead(g:number,r:number):Promise<string> {
  let failure='';
  const snap=await snapshot();if(!ordinary(g,r))return '';
  const head=snap.outbox.find(m=>m.state==='queued');if(!head)return '';
  let state:State='queued',seq:number|null=null;
  try {
    const reply=await fetchJSON('/api/v1/messages',{message_id:head.message_id,sender:head.sender,recipient:head.recipient,text:head.text},5000,g);
    if(!live(g))return '';
    if(reply.status>=400&&reply.status<500&&reply.status!==408&&reply.status!==429){state='failed';failure=`${reply.wireError?.code??'HTTP_ERROR'}: ${reply.wireError?.message??`HTTP ${reply.status}; correct the problem and submit a new message.`}`;}
    else {
      const value=ensureSuccess(reply,[200,201]);
      check(exact(value,['message_id','sender','recipient','sequence'])&&value.message_id===head.message_id&&value.sender===head.sender&&value.recipient===head.recipient&&integer(value.sequence,1),'Invalid or mismatched send receipt; retrying the original message.');
      state='accepted';seq=value.sequence as number;
    }
  }catch(e){if(!live(g))return '';failure=reason(e);}
  if(!live(g))return '';
  try {await outcome(head,state,seq,failure||null,g);await refreshSnapshot(g);}catch(e){if(live(g))storageFailure(e);failure=`STORAGE_UNAVAILABLE: ${reason(e)}`;}
  return failure;
}
function validatePage(value:unknown,who:string,after:number):{messages:Message[];next_after:number} {
  check(exact(value,['messages','next_after'])&&Array.isArray(value.messages)&&value.messages.length<=100&&integer(value.next_after),'Invalid incoming page.');
  const seen=new Set<string>();
  for(let i=0;i<value.messages.length;i++){
    const m:unknown=value.messages[i];
    check(exact(m,['message_id','sender','recipient','text','sequence'])&&uuid(m.message_id)&&username(m.sender)&&m.sender!==who&&m.recipient===who&&validText(m.text)&&integer(m.sequence,1)&&m.sequence===after+i+1,'Invalid incoming message or noncontiguous sequence.');
    const key=`${m.sender}:${m.message_id}`;check(!seen.has(key),'Repeated message in page.');seen.add(key);
  }
  check(value.next_after===after+value.messages.length,'Invalid page cursor.');
  return value as unknown as {messages:Message[];next_after:number};
}
async function receive(g:number,r:number):Promise<string> {
  try {
    const snap=await snapshot();if(!ordinary(g,r))return '';
    const who=snap.meta.username!,after=snap.meta.receive_cursor;
    const reply=await fetchJSON(`/api/v1/messages?recipient=${encodeURIComponent(who)}&after=${after}`,undefined,5000,g);
    if(!live(g))return '';
    if(reply.status===409&&reply.wireError?.code==='CURSOR_INVALID'&&reply.wireError.field==='after'){
      paused=true;connection='error';return 'CURSOR_INVALID: Server session changed. Reset local store before continuing.';
    }
    const page=validatePage(ensureSuccess(reply),who,after);
    try {
      await transaction(['metadata','inbox'],'readwrite',async tx=>{
        const ms=tx.objectStore('metadata'),inbox=tx.objectStore('inbox');
        const meta:Meta=await request(ms.get('state'));
        if(!live(g)||meta.username!==who)throw new Error('Identity changed.');
        check(meta.receive_cursor===after,'Stale incoming page.');
        for(const m of page.messages){
          const old:Message|undefined=await request(inbox.get([m.sender,m.message_id]));
          const sameSequence:Message|undefined=await request(inbox.index('by_sequence').get(m.sequence));
          if(old)check(old.recipient===m.recipient&&old.text===m.text&&old.sequence===m.sequence,'Conflicting stored message.');
          if(sameSequence)check(sameSequence.sender===m.sender&&sameSequence.message_id===m.message_id,'Conflicting stored sequence.');
          if(!old)await request(inbox.add(m));
        }
        meta.receive_cursor=page.next_after;await request(ms.put(meta));
      });
    }catch(e){if(e instanceof Failure)throw e;throw new Failure('STORAGE_UNAVAILABLE',reason(e));}
    if(!live(g))return '';
    if(page.next_after>after)receiptState='pending';
    await refreshSnapshot(g);return '';
  }catch(e){return live(g)?reason(e):'';}
}
async function reportReceipt(g:number,r:number):Promise<void> {
  try {
    const snap=await snapshot();if(!ordinary(g,r))return;
    const recipient=snap.meta.username!,through=snap.meta.receive_cursor;
    const value=ensureSuccess(await fetchJSON('/api/v1/receipts',{recipient,through},2000,g));
    check(exact(value,['recipient','through'])&&value.recipient===recipient&&integer(value.through)&&value.through>=through,'Invalid receipt report reply.');
    if(live(g)){receiptState='confirmed';receiptError='';}
  }catch(e){if(live(g)){receiptState='error';receiptError=reason(e);}}
  controls();
}
async function updateDirectory(g:number,r:number):Promise<void> {
  let announcementOK=false, problem='', transport=false;
  try {
    const value=ensureSuccess(await fetchJSON('/api/v1/users',{username:data.meta.username},2000,g));
    check(exact(value,['username'])&&value.username===data.meta.username,'Invalid announcement reply.');announcementOK=true;
  }catch(e){problem=reason(e);transport=e instanceof Failure&&e.transport;}
  if(!ordinary(g,r))return;
  try {
    const value=ensureSuccess(await fetchJSON('/api/v1/users',undefined,2000,g));
    check(exact(value,['users'])&&Array.isArray(value.users),'Invalid directory response.');
    let previous='';
    for(const user of value.users){check(exact(user,['username','online'])&&username(user.username)&&typeof user.online==='boolean'&&user.username>previous,'Invalid, duplicate or unordered directory user.');previous=user.username;}
    if(ordinary(g,r)){directory=value.users as User[];renderDirectory();}
  }catch(e){problem=[problem,reason(e)].filter(Boolean).join(' | ');transport=transport||(e instanceof Failure&&e.transport);}
  if(!ordinary(g,r))return;
  directoryState=problem?(transport?'stale':'error'):(announcementOK?'current':'error');directoryError=problem;controls();
}
async function notifyPresence(g:number,r:number):Promise<void> {
  const desired=online,who=data.meta.username!;
  presencePending=false;presenceState='pending';controls();
  try {
    const value=ensureSuccess(await fetchJSON('/api/v1/presence',{username:who,online:desired},2000,g));
    check(exact(value,['username','online'])&&value.username===who&&typeof value.online==='boolean'&&value.online===desired,'Invalid presence reply.');
    if(live(g)&&r===revision){presenceConfirmed=desired;presenceState='confirmed';presenceError='';}
  }catch(e){if(live(g)&&r===revision){presenceConfirmed=false;presenceState='error';presenceError=`Presence report failed: ${reason(e)}`;}}
  if(live(g))controls();
}
function wake():void {
  wakePending=true;
  if(timer!==null){clearTimeout(timer);timer=null;}
  if(!running)void worker();
}
async function worker():Promise<void> {
  if(running)return;
  running=true;
  try {
    while(ready&&!closing&&!resetting&&!paused&&data.meta.username){
      wakePending=false;
      const g=generation,r=revision;
      if(presencePending||(online&&!presenceConfirmed))await notifyPresence(g,r);
      if(!live(g)||paused)break;
      if(revision!==r)continue;
      if(!online)break;
      const sendError=await sendHead(g,r);
      if(!ordinary(g,r)){if(live(g)&&!paused&&revision!==r)continue;break;}
      const receiveError=await receive(g,r);
      if(live(g)){
        syncError=[sendError,receiveError].filter(Boolean).join('\n');
        if(online)connection=syncError?(syncError.includes('TRANSPORT_ERROR')?'offline':'error'):'online';
        controls();
      }
      if(!ordinary(g,r)){if(live(g)&&!paused&&revision!==r)continue;break;}
      await reportReceipt(g,r);
      if(!ordinary(g,r)){if(live(g)&&!paused&&revision!==r)continue;break;}
      await updateDirectory(g,r);
      if(!live(g)||paused)break;
      if(revision!==r)continue;
      if(wakePending)continue;
      break;
    }
  }catch(e){if(!resetting&&!closing){storageFailure(e);connection='error';controls();}}
  finally {
    running=false;
    if(ready&&!closing&&!resetting&&!paused&&data.meta.username){
      if(wakePending||presencePending) {timer=setTimeout(()=>{timer=null;void worker();},0);}
      else if(online){timer=setTimeout(()=>{timer=null;void worker();},1000);}
    }
  }
}
function setMode():void {
  const desired=modeControl.value==='online';if(desired===online)return;
  online=desired;revision++;presenceConfirmed=false;presenceError='';
  connection=online?'unknown':'offline';
  directoryState=online?(directory.length?'stale':'loading'):'stale';
  if(data.meta.username&&!paused){presencePending=true;presenceState='pending';}else{presencePending=false;presenceState='unknown';}
  controls();wake();
}
async function reset():Promise<void> {
  if(!ready||resetting)return;
  resetting=true;generation++;revision++;presencePending=false;presenceConfirmed=false;wakePending=false;
  if(timer!==null){clearTimeout(timer);timer=null;}activeAbort?.abort();controls();
  try {
    // This transaction is queued behind all earlier operations on these stores.
    await transaction(['metadata','inbox','outbox'],'readwrite',async tx=>{
      await Promise.all(['metadata','inbox','outbox'].map(name=>request(tx.objectStore(name).clear())));
      await request(tx.objectStore('metadata').put(fresh()));
    });
    data={meta:fresh(),inbox:[],outbox:[]};directory=[];
    selectedIncoming='';selectedOutgoing='';selectedUser='';
    nameInput.value='';recipientInput.value='';draft.value='';el<HTMLInputElement>('user-filter').value='';
    online=true;modeControl.value='online';connection='unknown';paused=false;
    formError='';syncError='';storeError='';directoryError='';receiptError='';presenceError='';
    directoryState='loading';receiptState='unknown';presenceState='unknown';busy=false;
    // Clear old rows and details before enabling login in the same event turn.
    renderMessages();renderDirectory();byId('reset-panel').hidden=true;
  }catch(e){storageFailure(e);presenceState='unknown';if(online&&data.meta.username)presencePending=true;}
  finally{resetting=false;busy=false;controls();wake();}
}
byId('login-form').addEventListener('submit',e=>{e.preventDefault();void login();});
byId('compose-form').addEventListener('submit',e=>{e.preventDefault();void enqueue();});
modeControl.addEventListener('change',setMode);
el('reset-button').onclick=()=>{byId('reset-panel').hidden=false;};
byId('reset-cancel').onclick=()=>{byId('reset-panel').hidden=true;};
el('reset-confirm').onclick=()=>{void reset();};
el('user-filter').addEventListener('input',renderDirectory);
el('user-refresh').onclick=wake;
window.addEventListener('focus',wake);window.addEventListener('online',wake);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)wake();});
window.addEventListener('offline',()=>{if(online){connection='offline';directoryState='stale';controls();}wake();});
window.addEventListener('pagehide',()=>{closing=true;generation++;activeAbort?.abort();if(timer!==null)clearTimeout(timer);database?.close();});
async function start():Promise<void> {
  controls();renderMessages();
  try {
    database=await openStore();
    database.onversionchange=()=>{closing=true;generation++;activeAbort?.abort();database.close();ready=false;storeError='STORAGE_UNAVAILABLE: Database version changed. Close this tab and reopen.';controls();};
    data=await snapshot();renderMessages();renderDirectory();ready=true;
    if(data.meta.username&&online){presencePending=true;presenceState='pending';}
    controls();wake();
  }catch(e){ready=false;storeError=`STORAGE_UNAVAILABLE: ${reason(e)} Unsupported or unavailable store; existing data was preserved.`;controls();}
}
void start();
