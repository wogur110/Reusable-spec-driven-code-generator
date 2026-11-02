// Keep client declarations scoped to this browser ES module.
export {};

type Meta = {key: 'state'; username: string | null; receive_cursor: number; next_local_order: number};
type Message = {message_id: string; sender: string; recipient: string; text: string; sequence: number};
type Outgoing = Omit<Message, 'sequence'> & {local_order: number; state: 'queued'|'accepted'|'failed'; server_sequence: number|null; error: string|null};
type User = {username: string; online: boolean};
const el = <T extends HTMLElement = HTMLElement>(id: string): T => document.querySelector(`[data-testid="${id}"]`)!;
const input = (id: string) => el<HTMLInputElement>(id);
const defaults = (): Meta => ({key:'state',username:null,receive_cursor:0,next_local_order:1});
const userValid = (v: unknown): v is string => typeof v === 'string' && /^[a-z][a-z0-9_]{0,31}$/.test(v);
const uuidValid = (v: unknown): v is string => typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(v);
const integer = (v: unknown, min=0): v is number => typeof v === 'number' && Number.isSafeInteger(v) && v >= min;
const textValid = (v: unknown): v is string => {
  if (typeof v !== 'string' || !v.length || new TextEncoder().encode(v).length > 4096) return false;
  for (let i=0;i<v.length;i++) { const c=v.charCodeAt(i); if(c>=0xd800 && c<=0xdbff){const n=v.charCodeAt(++i);if(!(n>=0xdc00&&n<=0xdfff))return false;}else if(c>=0xdc00&&c<=0xdfff)return false; }
  return true;
};
function exact(v: unknown, keys: string[]): v is Record<string, any> { return !!v && typeof v==='object' && !Array.isArray(v) && Object.keys(v).length===keys.length && keys.every(k=>Object.hasOwn(v,k)); }
function ensure(ok: unknown, message='PROTOCOL_ERROR: Invalid server response'): asserts ok { if (!ok) throw new Error(message); }
function req<T>(r: IDBRequest<T>): Promise<T> { return new Promise((resolve,reject)=>{r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);}); }
function completed(tx: IDBTransaction): Promise<void> { return new Promise((resolve,reject)=>{tx.oncomplete=()=>resolve();tx.onabort=()=>reject(tx.error || new Error('Transaction aborted'));tx.onerror=()=>{};}); }
let db: IDBDatabase;
let meta=defaults(), outgoing: Outgoing[]=[], incoming: Message[]=[];
let ready=false, busy=false, resetting=false, paused=false, stopped=false;
let generation=0, revision=0, mode='online', presenceIntent=false;
let directory: User[]=[], selectedUser='', selectedInbox='', selectedOutbox='';
let running=false, timer: ReturnType<typeof setTimeout>|undefined, wakePending=false;
let active: AbortController|undefined;
const localError = (s: string) => {el('error-message').textContent=s;};
const connection = (s: string) => {el('connection-status').textContent=s;el('connection-status').dataset.state=s;};
const status = (id: string,s: string) => {el(id).textContent=s;};
function controls(){
  const enabled=ready&&!resetting&&!stopped;
  el('app-ready').dataset.ready=String(enabled);
  (document.getElementById('login') as HTMLElement).hidden=!!meta.username;
  el<HTMLButtonElement>('login-button').disabled=!enabled||busy;
  input('username-input').disabled=!enabled||busy;
  el('current-user').textContent=meta.username||'';
  for(const id of ['recipient-input','message-input','send-button']) (el(id) as HTMLInputElement).disabled=!enabled||!meta.username||paused||busy;
  el<HTMLButtonElement>('reset-button').disabled=!enabled;
}
function td(row: HTMLTableRowElement, value: string, testid?: string){ const c=document.createElement('td');c.textContent=value;if(testid)c.dataset.testid=testid;row.append(c); }
function renderMessages(){
  const ib=el('inbox'), ob=el('outbox');ib.replaceChildren();ob.replaceChildren();
  for(const m of incoming){const row=document.createElement('tr');const key=m.sender+':'+m.message_id;row.dataset.testid='inbox-item';row.dataset.messageId=m.message_id;row.dataset.sender=m.sender;row.dataset.sequence=String(m.sequence);row.tabIndex=0;row.classList.toggle('selected',selectedInbox===key);
    td(row,m.message_id);td(row,m.sender,'message-sender');td(row,m.text,'message-text');td(row,String(m.sequence));
    const select=()=>{selectedInbox=key;el('inbox-detail').textContent=m.text;renderMessages();};row.onclick=select;row.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};ib.append(row);
  }
  for(const m of outgoing){const row=document.createElement('tr');row.dataset.testid='outbox-item';row.dataset.messageId=m.message_id;row.dataset.state=m.state;row.dataset.localOrder=String(m.local_order);row.tabIndex=0;row.classList.toggle('selected',selectedOutbox===m.message_id);
    td(row,m.message_id);td(row,m.recipient,'message-recipient');td(row,m.text,'message-text');td(row,m.state==='accepted'?'accepted by server':m.state,'message-state');td(row,m.error||'','message-error');td(row,String(m.local_order));
    const select=()=>{selectedOutbox=m.message_id;el('outbox-detail').textContent=m.text;renderMessages();};row.onclick=select;row.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};ob.append(row);
  }
  document.getElementById('inbox-empty')!.hidden=incoming.length>0;document.getElementById('outbox-empty')!.hidden=outgoing.length>0;
}
function renderDirectory(){const container=el('user-directory');container.replaceChildren();const filter=input('user-filter').value.toLowerCase();for(const u of directory){if(u.username===meta.username||!u.username.toLowerCase().includes(filter))continue;const b=document.createElement('button');b.type='button';b.dataset.testid='user-item';b.dataset.username=u.username;b.setAttribute('aria-pressed',String(selectedUser===u.username));const name=document.createElement('span');name.dataset.testid='user-name';name.textContent=u.username;const p=document.createElement('span');p.dataset.testid='user-presence';p.textContent=u.online?'recently seen':'not recently seen';b.append(name,p);b.onclick=()=>{selectedUser=u.username;input('recipient-input').value=u.username;renderDirectory();};container.append(b);}}
async function snapshot(token=generation){const tx=db.transaction(['metadata','outbox','inbox'],'readonly'),done=completed(tx);const values=await Promise.all([req(tx.objectStore('metadata').get('state')),req(tx.objectStore('outbox').getAll()),req(tx.objectStore('inbox').getAll())]);await done;if(token!==generation||resetting)return;meta=values[0];outgoing=(values[1] as Outgoing[]).sort((a,b)=>a.local_order-b.local_order);incoming=(values[2] as Message[]).sort((a,b)=>a.sequence-b.sequence);renderMessages();controls();}
async function openStore(){ db=await new Promise<IDBDatabase>((resolve,reject)=>{const r=indexedDB.open('reusable-spec-messenger',1);r.onupgradeneeded=()=>{const d=r.result;const m=d.createObjectStore('metadata',{keyPath:'key'});m.put(defaults());const o=d.createObjectStore('outbox',{keyPath:'message_id'});o.createIndex('by_order','local_order',{unique:true});const i=d.createObjectStore('inbox',{keyPath:['sender','message_id']});i.createIndex('by_sequence','sequence',{unique:true});};r.onerror=()=>reject(r.error);r.onblocked=()=>reject(new Error('Database upgrade blocked; close other tabs and reopen.'));r.onsuccess=()=>resolve(r.result);});
  db.onversionchange=()=>{stopped=true;generation++;active?.abort();db.close();ready=false;localError('STORAGE_UNAVAILABLE: Database changed. Close this tab and reopen.');controls();};
  ensure(db.objectStoreNames.length===3 && ['metadata','outbox','inbox'].every(n=>db.objectStoreNames.contains(n)),'STORAGE_UNAVAILABLE: Unsupported database schema');
  const tx=db.transaction(['metadata','outbox','inbox'],'readonly'),done=completed(tx);const m=tx.objectStore('metadata'),o=tx.objectStore('outbox'),i=tx.objectStore('inbox');
  ensure(m.keyPath==='key'&&o.keyPath==='message_id'&&JSON.stringify(i.keyPath)===JSON.stringify(['sender','message_id'])&&o.index('by_order').unique&&o.index('by_order').keyPath==='local_order'&&i.index('by_sequence').unique&&i.index('by_sequence').keyPath==='sequence','STORAGE_UNAVAILABLE: Unsupported database schema');
  const state=await req(m.get('state'));await done;ensure(exact(state,['key','username','receive_cursor','next_local_order'])&&state.key==='state'&&(state.username===null||userValid(state.username))&&integer(state.receive_cursor)&&integer(state.next_local_order,1),'STORAGE_UNAVAILABLE: Invalid metadata');
  await snapshot();ready=true;controls();if(meta.username&&mode==='online'){presenceIntent=true;status('presence-status','pending');wake();}
}
async function login(){if(!ready||busy||meta.username)return;const username=input('username-input').value;if(!userValid(username)){localError('INVALID_USERNAME: Use 1–32 lowercase ASCII letters, digits or underscores, beginning with a letter.');return;}busy=true;controls();try{const tx=db.transaction('metadata','readwrite'),done=completed(tx);const m=await req(tx.objectStore('metadata').get('state')) as Meta;m.username=username;tx.objectStore('metadata').put(m);await done;localError('');await snapshot();if(mode==='online'){presenceIntent=true;status('presence-status','pending');wake();}}catch(e){storageError(e);}finally{busy=false;controls();}}
function storageError(e: unknown){localError('STORAGE_UNAVAILABLE: '+String(e));}
async function enqueue(){if(!ready||busy||paused||!meta.username)return;const recipient=input('recipient-input').value,text=input('message-input').value;if(!userValid(recipient)){localError('INVALID_USERNAME: Enter a valid recipient.');return;}if(recipient===meta.username){localError('SELF_SEND: Choose a different recipient.');return;}if(!textValid(text)){localError('INVALID_TEXT: Enter scalar Unicode text containing 1–4096 UTF-8 bytes.');return;}busy=true;controls();const token=generation;
  try{const tx=db.transaction(['metadata','outbox'],'readwrite'),done=completed(tx);let issue='';try{const s=tx.objectStore('metadata'),o=tx.objectStore('outbox'),m=await req(s.get('state')) as Meta;if(m.next_local_order===Number.MAX_SAFE_INTEGER){issue='LOCAL_ORDER_EXHAUSTED: Reset the store before sending.';tx.abort();}else{let id=crypto.randomUUID();while(await req(o.get(id)))id=crypto.randomUUID();o.add({message_id:id,sender:m.username,recipient,text,local_order:m.next_local_order,state:'queued',server_sequence:null,error:null});m.next_local_order++;s.put(m);}}catch(e){issue=String(e);tx.abort();}await done.catch(e=>{throw new Error(issue||String(e));});if(token!==generation)return;input('message-input').value='';localError('');await snapshot(token);wake();}catch(e){if(String(e).includes('LOCAL_ORDER_EXHAUSTED'))localError(String(e));else storageError(e);}finally{busy=false;controls();}}
interface Reply {status:number; body:unknown; valid:boolean; transport?:boolean; reason?:string}
async function request(path:string,body:unknown|undefined,timeout:number):Promise<Reply>{const c=new AbortController();active=c;const t=setTimeout(()=>c.abort(),timeout);let code=0;try{const response=await fetch('/api/v1/'+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:c.signal,cache:'no-store',redirect:'error'});code=response.status;const mime=response.headers.get('content-type')||'',encoding=response.headers.get('content-encoding');const bytes=await response.arrayBuffer();ensure(/^application\/json(?:\s*;\s*charset\s*=\s*utf-8)?\s*$/i.test(mime)&&(!encoding||encoding.toLowerCase()==='identity'));const text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);ensure(!text.startsWith('\ufeff'));return {status:code,body:JSON.parse(text),valid:true};}catch(e){return {status:code,body:null,valid:false,transport:code===0||c.signal.aborted,reason:code===0||c.signal.aborted?'TRANSPORT_ERROR: API unavailable or request timed out.':'PROTOCOL_ERROR: Invalid or incomplete response.'};}finally{clearTimeout(t);if(active===c)active=undefined;}}
const codes: Record<string,{status:number;fields:(string|null)[]}>={INVALID_REQUEST:{status:400,fields:[null]},INVALID_JSON:{status:400,fields:[null]},INVALID_FIELDS:{status:400,fields:[null]},INVALID_MESSAGE_ID:{status:400,fields:['message_id']},INVALID_USERNAME:{status:400,fields:['sender','recipient','username']},INVALID_RECEIPT:{status:400,fields:['through']},INVALID_PRESENCE:{status:400,fields:['online']},SELF_SEND:{status:400,fields:['recipient']},INVALID_TEXT:{status:400,fields:['text']},INVALID_QUERY:{status:400,fields:['after',null]},NOT_FOUND:{status:404,fields:[null]},METHOD_NOT_ALLOWED:{status:405,fields:[null]},IDEMPOTENCY_CONFLICT:{status:409,fields:['message_id']},CURSOR_INVALID:{status:409,fields:['after','through']},PAYLOAD_TOO_LARGE:{status:413,fields:[null]},UNSUPPORTED_MEDIA_TYPE:{status:415,fields:[null]},SEQUENCE_EXHAUSTED:{status:503,fields:[null]},INTERNAL_ERROR:{status:500,fields:[null]}};
function wireError(r:Reply):Record<string,any>|null{const b=r.body;if(!r.valid||!exact(b,['error'])||!exact(b.error,['code','message','field']))return null;const e=b.error,c=codes[e.code];return c&&c.status===r.status&&c.fields.includes(e.field)&&typeof e.message==='string'&&e.message.length?e:null;}
function reason(r:Reply){const e=wireError(r);return e?`${e.code}: ${e.message}`:r.status>=400&&r.status<500?`HTTP_ERROR: Server returned HTTP ${r.status}.`:r.reason||`HTTP_ERROR: Server returned HTTP ${r.status}.`;}
// Keep each messaging direction's observation: a healthy GET cannot hide a
// queued POST timeout. Auxiliary requests never change these observations.
type CoreState = 'unknown'|'online'|'offline'|'error';
let sendState: CoreState='unknown', receiveState: CoreState='unknown';
function coreStatus(){
  const states=[sendState,receiveState];
  connection(mode==='offline'||states.includes('offline')?'offline':states.includes('error')?'error':states.includes('online')?'online':'unknown');
}
function coreFailure(r:Reply,direction:'send'|'receive'){
  const state=r.transport||[408,429].includes(r.status)||r.status>=500?'offline':'error';
  if(direction==='send')sendState=state;else receiveState=state;
  coreStatus();
}
async function outcome(m:Outgoing,state:Outgoing['state'],sequence:number|null,error:string|null,token:number){if(token!==generation)return;const tx=db.transaction('outbox','readwrite'),done=completed(tx);const store=tx.objectStore('outbox');const current=await req(store.get(m.message_id)) as Outgoing|undefined;if(current&&current.state==='queued'){store.put({...current,state,server_sequence:sequence,error});}await done;if(token===generation)await snapshot(token);}
async function sendHead(token:number){const m=outgoing.find(v=>v.state==='queued');if(!m){sendState='unknown';return;}const r=await request('messages',{message_id:m.message_id,sender:m.sender,recipient:m.recipient,text:m.text},5000);if(token!==generation)return;let state:Outgoing['state']='queued',sequence:number|null=null,error:string|null=reason(r);const b=r.body;
  if((r.status===200||r.status===201)&&r.valid&&exact(b,['message_id','sender','recipient','sequence'])&&b.message_id===m.message_id&&b.sender===m.sender&&b.recipient===m.recipient&&integer(b.sequence,1)){state='accepted';sequence=b.sequence;error=null;sendState='online';coreStatus();}
  else{if(r.status>=400&&r.status<500&&r.status!==408&&r.status!==429)state='failed';coreFailure(r,'send');if(r.status===200||r.status===201)error='PROTOCOL_ERROR: Invalid acceptance receipt; retrying the original message.';}
  try{await outcome(m,state,sequence,error,token);}catch(e){storageError(e);}
}
function validatePage(b:unknown,after:number,username:string): {messages:Message[];next_after:number}{ensure(exact(b,['messages','next_after'])&&Array.isArray(b.messages)&&b.messages.length<=100&&integer(b.next_after));const keys=new Set<string>();let seq=after;for(const m of b.messages){ensure(exact(m,['message_id','sender','recipient','text','sequence'])&&uuidValid(m.message_id)&&userValid(m.sender)&&userValid(m.recipient)&&textValid(m.text)&&integer(m.sequence,1)&&m.recipient===username&&m.sender!==username&&m.sequence===seq+1);const key=m.sender+':'+m.message_id;ensure(!keys.has(key));keys.add(key);seq=m.sequence;}ensure(b.next_after===seq);return b as {messages:Message[];next_after:number};}
async function commitPage(page:{messages:Message[];next_after:number},after:number,token:number){if(token!==generation)return;const tx=db.transaction(['metadata','inbox'],'readwrite'),done=completed(tx);let failure:unknown;try{const s=tx.objectStore('metadata'),i=tx.objectStore('inbox');const m=await req(s.get('state')) as Meta;ensure(m.receive_cursor===after,'PROTOCOL_ERROR: Stale receive page');for(const message of page.messages){const old=await req(i.get([message.sender,message.message_id])) as Message|undefined;if(old)ensure(['sender','message_id','recipient','text','sequence'].every(k=>old[k as keyof Message]===message[k as keyof Message]),'PROTOCOL_ERROR: Conflicting incoming message');else i.add(message);}m.receive_cursor=page.next_after;s.put(m);}catch(e){failure=e;tx.abort();}await done.catch(e=>{throw failure||e;});if(token===generation){if(page.next_after>after)status('receipt-status','pending');await snapshot(token);}}
async function receive(token:number){const after=meta.receive_cursor,user=meta.username!;const r=await request(`messages?recipient=${encodeURIComponent(user)}&after=${after}`,undefined,5000);if(token!==generation)return;const err=wireError(r);if(r.status===409&&err?.code==='CURSOR_INVALID'&&err.field==='after'){paused=true;presenceIntent=false;connection('error');localError('CURSOR_INVALID: Server session changed. Reset this client store to continue.');controls();return;}if(r.status!==200||!r.valid){coreFailure(r,'receive');return;}try{const page=validatePage(r.body,after,user);await commitPage(page,after,token);if(token!==generation)return;receiveState='online';coreStatus();}catch(e){if(token!==generation)return;receiveState='error';coreStatus();if(!String(e).includes('PROTOCOL_ERROR'))storageError(e);}}
function eligible(token:number,rev:number){return token===generation&&rev===revision&&!!meta.username&&mode==='online'&&!paused&&!resetting&&!stopped;}
async function notifyPresence(token:number){const rev=revision,online=mode==='online',username=meta.username!;presenceIntent=false;status('presence-status','pending');const r=await request('presence',{username,online},2000);if(token!==generation||rev!==revision)return;const b=r.body,ok=r.status===200&&r.valid&&exact(b,['username','online'])&&b.username===username&&b.online===online;status('presence-status',ok?'confirmed':'error');if(!ok&&online)presenceIntent=true;}
async function auxiliaries(token:number,rev:number){const username=meta.username!,through=meta.receive_cursor;const receipt=await request('receipts',{recipient:username,through},2000);if(token!==generation)return;const b=receipt.body;status('receipt-status',receipt.status===200&&receipt.valid&&exact(b,['recipient','through'])&&b.recipient===username&&integer(b.through)&&b.through>=through?'confirmed':'error');if(!eligible(token,rev))return;
  const announce=await request('users',{username},2000);if(token!==generation)return;const a=announce.body;const announced=announce.status===200&&announce.valid&&exact(a,['username'])&&a.username===username;if(!eligible(token,rev))return;
  const result=await request('users',undefined,2000);if(token!==generation)return;let good=false;try{const d=result.body;ensure(result.status===200&&result.valid&&exact(d,['users'])&&Array.isArray(d.users));let last='';for(const u of d.users){ensure(exact(u,['username','online'])&&userValid(u.username)&&typeof u.online==='boolean'&&u.username>last);last=u.username;}directory=d.users;good=true;renderDirectory();}catch{}
  status('directory-status',mode==='offline'?'stale':announced&&good?'current':announce.transport||result.transport?'stale':'error');
}
function wake(){wakePending=true;if(timer){clearTimeout(timer);timer=undefined;}if(!running)void run();}
async function run(){if(running||!ready||!meta.username||resetting||stopped||paused)return;running=true;wakePending=false;try{const token=generation, startRevision=revision;if(presenceIntent)await notifyPresence(token);const rev=revision;if(startRevision===rev&&eligible(token,rev)){await sendHead(token);if(eligible(token,rev))await receive(token);if(eligible(token,rev))await auxiliaries(token,rev);}}catch(e){if(!resetting&&!stopped)storageError(e);}finally{running=false;if(!ready||!meta.username||resetting||stopped||paused)return;if(wakePending||(mode==='offline'&&presenceIntent)){wakePending=false;void run();}else if(mode==='online'){timer=setTimeout(()=>{timer=undefined;void run();},1000);}}}
function changeMode(){const next=el<HTMLSelectElement>('transport-mode').value;if(next===mode)return;mode=next;revision++;if(meta.username&&!paused){presenceIntent=true;status('presence-status','pending');}if(mode==='offline'){connection('offline');status('directory-status','stale');}else connection('unknown');wake();}
async function reset(){if(resetting||!ready)return;resetting=true;generation++;revision++;presenceIntent=false;wakePending=false;if(timer)clearTimeout(timer);active?.abort();controls();try{const tx=db.transaction(['metadata','outbox','inbox'],'readwrite'),done=completed(tx);for(const name of ['metadata','outbox','inbox'])tx.objectStore(name).clear();tx.objectStore('metadata').put(defaults());await done;meta=defaults();outgoing=[];incoming=[];directory=[];selectedUser=selectedInbox=selectedOutbox='';input('username-input').value='';input('recipient-input').value='';input('message-input').value='';input('user-filter').value='';el('inbox-detail').textContent='';el('outbox-detail').textContent='';renderMessages();renderDirectory();mode='online';el<HTMLSelectElement>('transport-mode').value='online';paused=false;sendState=receiveState='unknown';connection('unknown');status('presence-status','unknown');status('receipt-status','unknown');status('directory-status','loading');localError('');document.getElementById('reset-panel')!.hidden=true;}catch(e){storageError(e);}finally{resetting=false;controls();}}
document.getElementById('login')!.onsubmit=e=>{e.preventDefault();void login();};
document.getElementById('compose')!.onsubmit=e=>{e.preventDefault();void enqueue();};
el('transport-mode').onchange=changeMode;
el('user-filter').oninput=renderDirectory;
el('user-refresh').onclick=wake;
el('reset-button').onclick=()=>{document.getElementById('reset-panel')!.hidden=false;};
document.getElementById('reset-cancel')!.onclick=()=>{document.getElementById('reset-panel')!.hidden=true;};
el('reset-confirm').onclick=()=>void reset();
window.addEventListener('online',wake);window.addEventListener('focus',wake);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')wake();});
window.addEventListener('offline',()=>{connection('offline');status('directory-status','stale');});
void openStore().catch(e=>{ready=false;stopped=true;localError('STORAGE_UNAVAILABLE: '+String(e));controls();});
