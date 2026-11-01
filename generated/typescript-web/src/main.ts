export {};
type Meta = {key: 'state'; username: string|null; receive_cursor: number; next_local_order: number};
type Message = {message_id:string; sender:string; recipient:string; text:string; sequence:number};
type Outgoing = Omit<Message,'sequence'> & {local_order:number; state:'queued'|'accepted'|'failed'; server_sequence:number|null; error:string|null};
type User = {username:string; online:boolean};
const el = <T extends HTMLElement = HTMLElement>(id:string) => document.querySelector<T>(`[data-testid="${id}"]`)!;
const input = (id:string) => el<HTMLInputElement>(id);
const defaults = ():Meta => ({key:'state',username:null,receive_cursor:0,next_local_order:1});
let db:IDBDatabase, meta=defaults(), outgoing:Outgoing[]=[], incoming:Message[]=[];
let ready=false, busy=false, resetting=false, closed=false, paused=false, generation=0;
let worker:Promise<void>|null=null, timer:ReturnType<typeof setTimeout>|undefined, wakePending=false;
let controller:AbortController|null=null, users:User[]=[], directory='loading', receipt='unknown', featureDetail='';
let localError='', syncError='', connection='unknown';
const online=()=>el<HTMLSelectElement>('transport-mode').value==='online';
const active=(g:number)=>g===generation&&!resetting&&!closed;
const canSync=(g:number)=>active(g)&&!!meta.username&&!paused&&online();
const describe=(e:unknown)=>e instanceof Error?e.message:String(e);
const username=(v:unknown):v is string=>typeof v==='string'&&/^[a-z][a-z0-9_]{0,31}$/.test(v)&&!v.includes('\n');
const integer=(v:unknown,min=0):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=min;
const uuid=(v:unknown):v is string=>typeof v==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(v)&&!v.includes('\n');
function textValid(v:unknown):v is string {
  if(typeof v!=='string'||!v.length)return false;
  for(const c of v){const n=c.codePointAt(0)!;if(n>=0xd800&&n<=0xdfff)return false;}
  return new TextEncoder().encode(v).length<=4096;
}
function exact(v:unknown,keys:string[]):v is Record<string,unknown>{return !!v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join('|')===[...keys].sort().join('|');}
function requireProtocol(ok:unknown):asserts ok {if(!ok)throw new Error('PROTOCOL_ERROR: Invalid server response.');}
function req<T>(r:IDBRequest<T>):Promise<T>{return new Promise((resolve,reject)=>{r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});}
async function transaction<T>(names:string[],mode:IDBTransactionMode,fn:(tx:IDBTransaction)=>Promise<T>):Promise<T>{
  const tx=db.transaction(names,mode);
  const done=new Promise<void>((resolve,reject)=>{tx.oncomplete=()=>resolve();tx.onabort=()=>reject(tx.error??new Error('Transaction aborted'));tx.onerror=()=>{};});
  try{const value=await fn(tx);await done;return value;}catch(e){try{tx.abort();}catch{}await done.catch(()=>{});throw e;}
}
async function snapshot(g=generation){
 const value=await transaction(['metadata','outbox','inbox'],'readonly',async tx=>{
 const m=req<Meta>(tx.objectStore('metadata').get('state'));
 const o=req<Outgoing[]>(tx.objectStore('outbox').index('by_order').getAll());
 const i=req<Message[]>(tx.objectStore('inbox').index('by_sequence').getAll());
 return {m:await m,o:await o,i:await i};});
 if(!active(g))return;
 if(!value.m||!integer(value.m.receive_cursor)||!integer(value.m.next_local_order,1)||(value.m.username!==null&&!username(value.m.username)))throw new Error('Unsupported metadata schema');
 meta=value.m;outgoing=value.o;incoming=value.i;render();
}
function child(id:string,text:string){const n=document.createElement('div');n.dataset.testid=id;n.textContent=text;return n;}
function renderDirectory(){
 const list=el('user-directory');list.replaceChildren();const filter=input('user-filter').value.toLowerCase();
 for(const user of users.filter(u=>u.username!==meta.username&&u.username.toLowerCase().includes(filter))){
 const b=document.createElement('button');b.type='button';b.dataset.testid='user-item';b.dataset.username=user.username;
 b.append(child('user-name',user.username),child('user-presence',user.online?'recently seen':'not recently seen'));
 b.disabled=!meta.username||paused||resetting;
 b.setAttribute('aria-pressed',String(input('recipient-input').value===user.username));
 b.onclick=()=>{input('recipient-input').value=user.username;renderDirectory();};list.append(b);}
 el('directory-status').textContent=directory;el('receipt-status').textContent=receipt;
 document.getElementById('feature-detail')!.textContent=featureDetail;
}
function render(){
 el('app-ready').dataset.ready=String(ready&&!resetting);
 document.getElementById('login-form')!.hidden=!!meta.username;
 input('username-input').disabled=!ready||busy||resetting||closed;
 el<HTMLButtonElement>('login-button').disabled=!ready||busy||resetting||closed;
 el('current-user').textContent=meta.username??'';
 for(const id of ['recipient-input','message-input','send-button'])el<HTMLInputElement>(id).disabled=!ready||!meta.username||paused||busy||resetting||closed;
 el('error-message').textContent=paused?syncError:(localError||syncError);
 el('connection-status').dataset.state=connection;el('connection-status').textContent=connection;
 const inbox=el('inbox');inbox.replaceChildren();
 for(const m of incoming){const row=child('inbox-item','');row.dataset.messageId=m.message_id;row.dataset.sender=m.sender;row.dataset.sequence=String(m.sequence);row.append(child('message-sender',m.sender),child('message-text',m.text));inbox.append(row);}
 if(!incoming.length)inbox.textContent='No messages received yet.';
 const outbox=el('outbox');outbox.replaceChildren();
 for(const m of outgoing){const row=child('outbox-item','');row.dataset.messageId=m.message_id;row.dataset.state=m.state;row.dataset.localOrder=String(m.local_order);row.append(child('message-recipient',m.recipient),child('message-text',m.text),child('message-state',m.state==='accepted'?'accepted by server':m.state),child('message-error',m.error??''));outbox.append(row);}
 if(!outgoing.length)outbox.textContent='No outgoing messages yet.';
 renderDirectory();
}
function storageError(e:unknown){localError=`STORAGE_UNAVAILABLE: ${describe(e)}. Check browser storage and try again.`;render();}
async function openStore(){
 db=await new Promise<IDBDatabase>((resolve,reject)=>{
 const r=indexedDB.open('reusable-spec-messenger',1);let blocked=false;
 r.onblocked=()=>{blocked=true;reject(new Error('Storage upgrade blocked. Close other tabs and reopen.'));};
 r.onerror=()=>reject(r.error);
 r.onupgradeneeded=()=>{const d=r.result;d.createObjectStore('metadata',{keyPath:'key'}).add(defaults());const o=d.createObjectStore('outbox',{keyPath:'message_id'});o.createIndex('by_order','local_order',{unique:true});const i=d.createObjectStore('inbox',{keyPath:['sender','message_id']});i.createIndex('by_sequence','sequence',{unique:true});};
 r.onsuccess=()=>{if(blocked){r.result.close();return;}resolve(r.result);};});
 db.onversionchange=()=>{closed=true;generation++;controller?.abort();clearTimeout(timer);db.close();ready=false;localError='Storage version changed. Close this page and reopen.';render();};
 await transaction(['metadata','outbox','inbox'],'readonly',async tx=>{
 for(const [name,key,index,indexKey] of [['metadata','key','',''],['outbox','message_id','by_order','local_order'],['inbox',['sender','message_id'],'by_sequence','sequence']] as const){
 const s=tx.objectStore(name);if(JSON.stringify(s.keyPath)!==JSON.stringify(key)||s.autoIncrement)throw new Error('Unsupported database schema');
 if(index){const i=s.index(index);if(i.keyPath!==indexKey||!i.unique||i.multiEntry)throw new Error('Unsupported index schema');}}
 });
 await snapshot();ready=true;render();wake();
}
async function login(){
 if(busy||!ready||resetting)return;localError='';const name=input('username-input').value;
 if(!username(name)){localError='INVALID_USERNAME: Use 1–32 lowercase letters, digits or underscores, starting with a letter.';render();return;}
 busy=true;render();const g=generation;
 try{await transaction(['metadata'],'readwrite',async tx=>{const s=tx.objectStore('metadata');const m:Meta=await req(s.get('state'));if(m.username&&m.username!==name)throw new Error('Reset before changing identity');s.put({...m,username:name});});await snapshot(g);}catch(e){if(active(g))storageError(e);}finally{busy=false;render();wake();}
}
async function enqueue(){
 if(busy||!ready||!meta.username||paused||resetting)return;
 localError='';const recipient=input('recipient-input').value,text=el<HTMLTextAreaElement>('message-input').value;
 if(!username(recipient))localError='INVALID_USERNAME: Enter a valid recipient.';
 else if(recipient===meta.username)localError='SELF_SEND: Choose a different recipient.';
 else if(!textValid(text))localError='INVALID_TEXT: Enter 1–4096 UTF-8 bytes of Unicode scalar text.';
 if(localError){render();return;}
 busy=true;render();const g=generation;
 try{await transaction(['metadata','outbox'],'readwrite',async tx=>{
 const ms=tx.objectStore('metadata'),os=tx.objectStore('outbox');const m:Meta=await req(ms.get('state'));
 if(!integer(m.next_local_order,1)||m.next_local_order>=Number.MAX_SAFE_INTEGER)throw new Error('LOCAL_ORDER_EXHAUSTED');
 let id=crypto.randomUUID();while(await req(os.get(id)))id=crypto.randomUUID();
 os.add({message_id:id,sender:m.username,recipient,text,local_order:m.next_local_order,state:'queued',server_sequence:null,error:null});ms.put({...m,next_local_order:m.next_local_order+1});
 });if(active(g)){el<HTMLTextAreaElement>('message-input').value='';await snapshot(g);}}catch(e){if(active(g))storageError(e);}finally{busy=false;render();wake();}
}
type Reply={status:number; body:unknown; valid:boolean};
async function request(path:string,body:unknown|undefined,timeout:number,g:number):Promise<Reply>{
 if(!canSync(g))throw new Error('TRANSPORT_ERROR: Offline or inactive.');
 const c=new AbortController();controller=c;const deadline=setTimeout(()=>c.abort(),timeout);
 try{
 const response=await fetch(path,{method:body===undefined?'GET':'POST',body:body===undefined?undefined:JSON.stringify(body),headers:body===undefined?{}:{'Content-Type':'application/json'},cache:'no-store',redirect:'error',signal:c.signal});
 let parsed:unknown=null,valid=false;
 try{const bytes=await response.arrayBuffer();const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes);parsed=JSON.parse(raw);valid=/^application\/json(?:\s*;\s*charset\s*=\s*utf-8)?\s*$/i.test(response.headers.get('Content-Type')??'')&&!(response.headers.get('Content-Encoding'));}catch{}
 if(!active(g))throw new Error('Inactive response');
 if(c.signal.aborted&&!(response.status>=400&&response.status<500&&response.status!==408&&response.status!==429))throw new Error('Request deadline expired.');
 return {status:response.status,body:parsed,valid};
 }catch(e){throw new Error(`TRANSPORT_ERROR: ${describe(e)}. Retrying while online.`);}finally{clearTimeout(deadline);if(controller===c)controller=null;}
}
const errorCodes=new Set(['INVALID_REQUEST','INVALID_JSON','INVALID_FIELDS','INVALID_MESSAGE_ID','INVALID_USERNAME','SELF_SEND','INVALID_TEXT','INVALID_QUERY','NOT_FOUND','METHOD_NOT_ALLOWED','IDEMPOTENCY_CONFLICT','CURSOR_INVALID','PAYLOAD_TOO_LARGE','UNSUPPORTED_MEDIA_TYPE','SEQUENCE_EXHAUSTED','INTERNAL_ERROR','INVALID_RECEIPT']);
function wireError(r:Reply):{code:string;message:string;field:unknown}|null {
 if(!r.valid||!exact(r.body,['error'])||!exact(r.body.error,['code','message','field']))return null;
 const e=r.body.error;if(typeof e.code!=='string'||!errorCodes.has(e.code)||typeof e.message!=='string'||!e.message.length||![null,'message_id','sender','recipient','text','after','username','through'].includes(e.field as string|null))return null;
 return {code:e.code,message:e.message,field:e.field};
}
function httpError(r:Reply){const e=wireError(r);return e?`${e.code}: ${e.message}`:`HTTP_ERROR: Server returned HTTP ${r.status}.`;}
async function sendOne(g:number){
 const m=outgoing.find(x=>x.state==='queued');if(!m)return;
 let state:Outgoing['state']='queued',sequence:number|null=null,error:string|null=null;
 try{const r=await request('/api/v1/messages',{message_id:m.message_id,sender:m.sender,recipient:m.recipient,text:m.text},5000,g);
 if(r.status===200||r.status===201){const b=r.body;requireProtocol(r.valid&&exact(b,['message_id','sender','recipient','sequence'])&&b.message_id===m.message_id&&b.sender===m.sender&&b.recipient===m.recipient&&integer(b.sequence,1));state='accepted';sequence=b.sequence as number;}
 else {error=httpError(r);if(r.status>=400&&r.status<500&&r.status!==408&&r.status!==429)state='failed';}
 }catch(e){error=describe(e);}
 if(!active(g))return;
 if(error){connection=error.startsWith('TRANSPORT_ERROR')?'offline':'error';syncError=error;}
 try{await transaction(['outbox'],'readwrite',async tx=>{const s=tx.objectStore('outbox');const current:Outgoing=await req(s.get(m.message_id));if(current&&current.state==='queued')s.put({...current,state,server_sequence:sequence,error});});await snapshot(g);}catch(e){if(active(g))storageError(e);}
}
function page(r:Reply,after:number,name:string):{messages:Message[];next_after:number}{
 const b=r.body;requireProtocol(r.status===200&&r.valid&&exact(b,['messages','next_after'])&&Array.isArray(b.messages)&&b.messages.length<=100&&integer(b.next_after));
 const seen=new Set<string>();let expected=after;
 for(const m of b.messages){requireProtocol(exact(m,['message_id','sender','recipient','text','sequence'])&&uuid(m.message_id)&&username(m.sender)&&m.sender!==name&&m.recipient===name&&textValid(m.text)&&integer(m.sequence,1)&&m.sequence===++expected);
 const key=`${m.sender}:${m.message_id}`;requireProtocol(!seen.has(key));seen.add(key);}
 requireProtocol(b.next_after===expected);return b as unknown as {messages:Message[];next_after:number};
}
async function receive(g:number){
 const after=meta.receive_cursor,name=meta.username!;
 try{const r=await request(`/api/v1/messages?recipient=${encodeURIComponent(name)}&after=${after}`,undefined,5000,g);if(!active(g))return;
 const err=wireError(r);if(r.status===409&&err?.code==='CURSOR_INVALID'&&err.field==='after'){paused=true;connection='error';syncError='CURSOR_INVALID: Reset local store for this server session.';render();return;}
 if(r.status!==200)throw new Error(httpError(r));
 const p=page(r,after,name);
 await transaction(['metadata','inbox'],'readwrite',async tx=>{
 const ms=tx.objectStore('metadata'),is=tx.objectStore('inbox');const current:Meta=await req(ms.get('state'));
 requireProtocol(current.username===name&&current.receive_cursor===after&&active(g));
 for(const m of p.messages){const old:Message|undefined=await req(is.get([m.sender,m.message_id]));const seq:Message|undefined=await req(is.index('by_sequence').get(m.sequence));
 requireProtocol(!old||(old.recipient===m.recipient&&old.text===m.text&&old.sequence===m.sequence));requireProtocol(!seq||(seq.sender===m.sender&&seq.message_id===m.message_id));if(!old)is.add(m);}
 ms.put({...current,receive_cursor:p.next_after});}).catch(e=>{if(describe(e).startsWith('PROTOCOL_ERROR'))throw e;throw new Error(`STORAGE_UNAVAILABLE: ${describe(e)}. Receive transaction did not commit.`);});
 if(!active(g))return;if(p.next_after>after)receipt='pending';await snapshot(g);
 if(!syncError)connection='online';
 }catch(e){if(!active(g))return;const message=describe(e);connection=message.startsWith('TRANSPORT_ERROR')?'offline':'error';syncError=message;render();}
}
async function auxiliary(g:number){
 const name=meta.username!,through=meta.receive_cursor;
 try{const r=await request('/api/v1/receipts',{recipient:name,through},2000,g);const b=r.body;requireProtocol(r.status===200&&r.valid&&exact(b,['recipient','through'])&&b.recipient===name&&integer(b.through)&&b.through>=through);if(active(g))receipt='confirmed';}
 catch(e){if(active(g)){receipt='error';featureDetail=`Receipt: ${describe(e)}`;}}
 if(!canSync(g))return;
 let announcement=true,dirFailure='';
 try{const r=await request('/api/v1/users',{username:name},2000,g);requireProtocol(r.status===200&&r.valid&&exact(r.body,['username'])&&r.body.username===name);}
 catch(e){announcement=false;dirFailure=describe(e).startsWith('TRANSPORT_ERROR')?'stale':'error';if(active(g))featureDetail=`Directory announcement: ${describe(e)}`;}
 if(!canSync(g))return;
 try{const r=await request('/api/v1/users',undefined,2000,g);const b=r.body;requireProtocol(r.status===200&&r.valid&&exact(b,['users'])&&Array.isArray(b.users));
 let previous='';for(const u of b.users){requireProtocol(exact(u,['username','online'])&&username(u.username)&&typeof u.online==='boolean'&&u.username>previous);previous=u.username;}
 if(active(g)){users=b.users as User[];directory=online()?(announcement?'current':dirFailure):'stale';if(announcement&&receipt==='confirmed')featureDetail='';}}
 catch(e){if(active(g)){directory=describe(e).startsWith('TRANSPORT_ERROR')?'stale':'error';featureDetail=`Directory: ${describe(e)}`;}}
 if(active(g)){if(!online())directory='stale';render();}
}
async function cycle(g:number){
 if(!canSync(g))return;syncError='';
 await snapshot(g);if(!canSync(g))return;await sendOne(g);
 if(!canSync(g))return;await receive(g);
 if(!canSync(g))return;await auxiliary(g);
 if(active(g))render();
}
function wake(){
 if(!ready||resetting||closed||paused||!meta.username)return;
 clearTimeout(timer);if(worker){wakePending=true;return;}
 if(!online()){connection='offline';directory='stale';render();return;}
 const g=generation;worker=cycle(g).catch(e=>{if(active(g))storageError(e);}).finally(()=>{
 worker=null;if(active(g)){const delay=wakePending?0:1000;wakePending=false;timer=setTimeout(wake,delay);}
 });
}
async function reset(){
 if(resetting||!ready)return;resetting=true;generation++;clearTimeout(timer);controller?.abort();render();
 try{
 await worker;
 await transaction(['metadata','outbox','inbox'],'readwrite',async tx=>{tx.objectStore('metadata').clear();tx.objectStore('outbox').clear();tx.objectStore('inbox').clear();tx.objectStore('metadata').put(defaults());});
 meta=defaults();outgoing=[];incoming=[];users=[];directory='loading';receipt='unknown';featureDetail='';paused=false;connection='unknown';localError='';syncError='';
 for(const id of ['username-input','recipient-input','message-input','user-filter'])input(id).value='';
 el<HTMLSelectElement>('transport-mode').value='online';document.getElementById('reset-panel')!.hidden=true;
 }catch(e){storageError(e);}finally{resetting=false;wakePending=false;await snapshot().catch(storageError);render();wake();}
}
document.getElementById('login-form')!.addEventListener('submit',e=>{e.preventDefault();void login();});
document.getElementById('compose')!.addEventListener('submit',e=>{e.preventDefault();void enqueue();});
el('reset-button').onclick=()=>{document.getElementById('reset-panel')!.hidden=false;};
document.getElementById('reset-cancel')!.onclick=()=>{document.getElementById('reset-panel')!.hidden=true;};
el('reset-confirm').onclick=()=>{void reset();};
el('transport-mode').onchange=()=>{if(!online()){directory='stale';connection='offline';controller?.abort();render();}wake();};
el('user-refresh').onclick=wake;input('user-filter').oninput=renderDirectory;
window.addEventListener('online',wake);window.addEventListener('offline',()=>{connection='offline';directory='stale';render();});window.addEventListener('focus',wake);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')wake();});
render();void openStore().catch(e=>{ready=false;closed=true;storageError(e);});
