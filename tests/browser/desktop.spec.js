const {test,expect}=require('@playwright/test');
const {fixture,accepted,received,seed,ROOT,PYTHON,stop}=require('./fixtures');
const {spawn,execFileSync}=require('node:child_process');
const fs=require('node:fs/promises');
const path=require('node:path');
let f;
test.beforeEach(async({browser})=>{f=await fixture(browser);});
test.afterEach(async()=>{if(f)await f.close();});
const widget=async(c,name)=>(await c.snapshot()).widgets[name];

for(const desktopAlice of [true,false]) {
  test(`GUI-02 fixed scenario using desktop controls (${desktopAlice?'desktop':'browser'} Alice)`,async()=>{
    const alice=await f.client(desktopAlice?'gui':'web','alice'),bob=await f.client(desktopAlice?'web':'gui','bob');
    let id=await alice.send('bob','Hi Bob, I have something important to tell you');await accepted(alice,id);await received(bob,'Hi Bob, I have something important to tell you');
    id=await bob.send('alice','What is it?');await accepted(bob,id);await received(alice,'What is it?');
    alice.proxy.mode.offline=true;const a=await alice.send('bob','Alice queued while offline');
    await expect.poll(()=>alice.proxy.history.filter(x=>x.method==='POST'&&x.failed&&x.body.includes(a)).length).toBeGreaterThan(0);
    expect((await alice.outbox()).find(x=>x.message_id===a).state).toBe('queued');
    bob.proxy.mode.offline=true;const b=await bob.send('alice','Bob queued while offline');
    await expect.poll(()=>bob.proxy.history.filter(x=>x.method==='POST'&&x.failed&&x.body.includes(b)).length).toBeGreaterThan(0);
    alice.proxy.mode.offline=false;await accepted(alice,a);expect((await bob.outbox()).find(x=>x.message_id===b).state).toBe('queued');
    alice.proxy.mode.offline=true;bob.proxy.mode.offline=false;await received(bob,'Alice queued while offline');await accepted(bob,b);
    alice.proxy.mode.offline=false;await received(alice,'Bob queued while offline');
    expect((await alice.inbox()).map(x=>x.text)).toEqual(['What is it?','Bob queued while offline']);
    expect((await bob.inbox()).map(x=>x.text)).toEqual(['Hi Bob, I have something important to tell you','Alice queued while offline']);
    for(const c of [alice,bob])expect((await c.outbox()).map(x=>x.state)).toEqual(['accepted','accepted']);
  });
}

test('GUI-01 actual controls, invalid drafts, Unicode and exact detail panes',async()=>{
  const c=await f.client('gui');await expect.poll(async()=> (await c.snapshot()).ready).toBe(true);
  await c.fill('username-input','Alice');await c.click('login-button');
  expect((await widget(c,'current-user')).text).toBe('');expect((await widget(c,'error-message')).text).not.toBe('');
  await c.login('alice');await c.transport('offline');
  for(const [recipient,text] of [['Bob','draft'],['alice','self'],['bob',''],['bob','a'.repeat(4097)],['bob','😀'.repeat(1025)]]) {
    await c.fill('recipient-input',recipient);await c.fill('message-input',text);await c.click('send-button');
    await expect.poll(async()=> (await widget(c,'error-message')).text).not.toBe('');
    expect((await widget(c,'message-input')).text).toBe(text);expect(await c.outbox()).toEqual([]);
  }
  expect(c.proxy.history.filter(x=>x.method==='POST')).toHaveLength(0);
  const text='  한글 😀\nsecond line  ';const id=await c.send('bob',text);
  expect((await widget(c,'message-input')).text).toBe('');
  await c.action('row',{widget:'outbox',iid:id});await expect.poll(async()=> (await widget(c,'outbox-detail')).text).toBe(text);
  await c.transport('online');await accepted(c,id);expect((await c.outbox())[0].visible_state).toBe('accepted by server');
  const row=await seed(f.backend.origin,'alice',text);await received(c,text);
  await c.action('row',{widget:'inbox',iid:'seeder:'+row.message_id});await expect.poll(async()=> (await widget(c,'inbox-detail')).text).toBe(text);
});

test('GUI-03 close and reopen preserves queued ID and delivers once',async()=>{
  const c=await f.client('gui','alice');c.proxy.mode.offline=true;
  const id=await c.send('bob','Desktop restart queue');await c.quit();await c.start();
  await expect.poll(async()=> (await widget(c,'current-user')).text).toBe('alice');
  expect((await c.outbox()).map(x=>[x.message_id,x.text,x.state])).toEqual([[id,'Desktop restart queue','queued']]);
  c.proxy.mode.offline=false;await accepted(c,id);const web=await f.client('web','bob');await received(web,'Desktop restart queue');
  await seed(f.backend.origin,'alice','Persist incoming');await received(c,'Persist incoming');const cursor=await c.cursor();
  await c.quit();await c.start();await received(c,'Persist incoming');expect(await c.cursor()).toBe(cursor);
  expect((await web.inbox()).filter(x=>x.message_id===id)).toHaveLength(1);
});

test('GUI-03 opens specified pre-GUI SQLite version 1 without loss or migration',async()=>{
  const c=await f.client('gui');await c.quit();
  // Build a fixture independently from the written schema, never copy old client code.
  execFileSync(PYTHON,['-c',`import sqlite3,sys,os
p=sys.argv[1]; os.unlink(p)
with sqlite3.connect(p) as d:
 d.executescript('''PRAGMA user_version=1;
 CREATE TABLE metadata(id INTEGER PRIMARY KEY,username TEXT,server_origin TEXT,receive_cursor INTEGER DEFAULT 0,next_local_order INTEGER DEFAULT 1);
 CREATE TABLE outbox(message_id TEXT PRIMARY KEY,sender TEXT NOT NULL,recipient TEXT NOT NULL,text TEXT NOT NULL,local_order INTEGER UNIQUE,state TEXT CHECK(state IN ('queued','accepted','failed')),server_sequence INTEGER,error_code TEXT,error_message TEXT);
 CREATE TABLE inbox(sender TEXT,message_id TEXT,recipient TEXT NOT NULL,text TEXT NOT NULL,sequence INTEGER UNIQUE,PRIMARY KEY(sender,message_id));''')
 d.execute('INSERT INTO metadata VALUES(1,?,?,1,4)',('alice',sys.argv[2]))
 for n,state in enumerate(['queued','accepted','failed'],1):
  d.execute('INSERT INTO outbox VALUES(?,?,?,?,?,?,?,?,?)',(f'11111111-1111-4111-8111-{n:012d}','alice','bob','legacy '+state,n,state,1 if state=='accepted' else None,'INVALID_TEXT' if state=='failed' else None,'legacy rejection' if state=='failed' else None))
 d.execute('INSERT INTO inbox VALUES(?,?,?,?,?)',('bob','22222222-2222-4222-8222-222222222222','alice','legacy incoming',1))`,path.join(c.state,'messages.sqlite3'),c.origin]);
  await fs.writeFile(path.join(c.state,'unrelated.txt'),'keep');await c.start(true);
  await expect.poll(async()=> (await widget(c,'current-user')).text).toBe('alice');
  expect((await c.outbox()).map(x=>[x.message_id,x.text,x.state,x.local_order])).toEqual(['queued','accepted','failed'].map((s,i)=>[`11111111-1111-4111-8111-${String(i+1).padStart(12,'0')}`,'legacy '+s,s,i+1]));
  expect((await c.inbox())[0].text).toBe('legacy incoming');expect(await c.cursor()).toBe(1);
  expect(execFileSync(PYTHON,['-c','import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("PRAGMA user_version").fetchone()[0])',path.join(c.state,'messages.sqlite3')],{encoding:'utf8'}).trim()).toBe('1');
  expect(await fs.readFile(path.join(c.state,'unrelated.txt'),'utf8')).toBe('keep');
});

test('GUI-04 canceled and confirmed reset preserve unrelated files',async()=>{
  const c=await f.client('gui','alice');await c.transport('offline');const id=await c.send('bob','Reset queued');
  await fs.writeFile(path.join(c.state,'unrelated.txt'),'keep');await c.click('reset-button');
  expect((await c.outbox())[0].message_id).toBe(id);expect((await widget(c,'reset-confirm')).visible).toBe(true);
  await c.click('reset-cancel');expect((await c.outbox())[0].message_id).toBe(id);expect((await widget(c,'current-user')).text).toBe('alice');
  await c.click('reset-button');await c.click('reset-confirm');
  await expect.poll(async()=> (await widget(c,'username-input')).visible).toBe(true);expect(await c.outbox()).toEqual([]);expect(await c.inbox()).toEqual([]);
  expect(await fs.readFile(path.join(c.state,'unrelated.txt'),'utf8')).toBe('keep');await c.login('carol');
});

test('GUI-04 reset during delayed receive cannot restore old identity messages',async()=>{
  const c=await f.client('gui','alice');c.proxy.mode.getResponseDelay=1500;await seed(f.backend.origin,'alice','Old identity only');
  const start=c.proxy.history.length;await expect.poll(()=>c.proxy.history.slice(start).some(x=>x.method==='GET'&&x.held&&!x.delivered&&x.response.includes('Old identity only'))).toBe(true);
  await c.click('reset-button');await c.click('reset-confirm');await expect.poll(async()=> (await widget(c,'username-input')).visible).toBe(true);
  delete c.proxy.mode.getResponseDelay;await c.login('carol');await seed(f.backend.origin,'carol','New identity only');await received(c,'New identity only');
  expect((await c.inbox()).map(x=>x.text)).toEqual(['New identity only']);
});

test('GUI-05 editing during slow network and bounded window close',async()=>{
  const c=await f.client('gui','alice');c.proxy.mode.delay=6500;await c.send('bob','Slow send');
  await expect.poll(()=>c.proxy.history.some(x=>x.method==='POST')).toBe(true);
  const start=Date.now();await c.fill('message-input','unfinished\ndraft  ');expect((await widget(c,'message-input')).text).toBe('unfinished\ndraft  ');expect(Date.now()-start).toBeLessThan(2000);
  await expect.poll(async()=> (await widget(c,'connection-status')).text).toBe('offline');expect((await widget(c,'message-input')).text).toBe('unfinished\ndraft  ');
  const closing=Date.now();await c.quit();expect(Date.now()-closing).toBeLessThan(6000);
});

test('GUI-05 default main opens Tk with closed stdin',async()=>{
  const child=spawn(PYTHON,['generated/python-client/main.py','--server',f.backend.origin,'--state-dir',path.join(f.dir,'default'),'--transport','offline'],{cwd:ROOT,stdio:['ignore','pipe','pipe']});
  let diagnostic='';child.stderr.on('data',b=>diagnostic+=b);
  try {
    await expect.poll(async()=>{
      expect(child.exitCode,diagnostic).toBe(null);
      // Inspect the production top-level window on this isolated display.
      try { const out=execFileSync('xwininfo',['-name','Local Messenger - Python'],{encoding:'utf8',stdio:['ignore','pipe','pipe']}); return out.includes('Map State: IsViewable')?1:0; } catch(error) { if(error.status===1)return 0;throw error; }
    }).toBeGreaterThan(0);
    child.kill('SIGINT');await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(new Error('Default GUI did not close')),6000);child.once('exit',code=>{clearTimeout(t);code===0?resolve():reject(new Error(diagnostic));});});
  } finally {await stop(child);}
});

test('GUI-06 unsupported store is visible and preserved',async()=>{
  const c=await f.client('gui','alice');await c.quit();
  execFileSync(PYTHON,['-c','import sqlite3,sys; d=sqlite3.connect(sys.argv[1]); d.execute("PRAGMA user_version=999"); d.close()',path.join(c.state,'messages.sqlite3')]);
  await c.start();await expect.poll(async()=> (await widget(c,'error-message')).text).not.toBe('');expect((await c.snapshot()).ready).toBe(false);
  await c.quit();expect(execFileSync(PYTHON,['-c','import sqlite3,sys; d=sqlite3.connect(sys.argv[1]); print(d.execute("PRAGMA user_version").fetchone()[0],d.execute("SELECT username FROM metadata").fetchone()[0])',path.join(c.state,'messages.sqlite3')],{encoding:'utf8'}).trim()).toBe('999 alice');
});

test('GUI-06 visible permanent rejection and cursor-invalid pause',async()=>{
  const c=await f.client('gui','alice');c.proxy.mode.postStatus=400;c.proxy.mode.errorBody='not JSON';const id=await c.send('bob','Rejected');
  await expect.poll(async()=> (await c.outbox()).find(x=>x.message_id===id).state).toBe('failed');expect((await c.outbox())[0].error).not.toBe(null);
  delete c.proxy.mode.postStatus;delete c.proxy.mode.errorBody;
  c.proxy.mode.getStatus=409;c.proxy.mode.page={error:{code:'CURSOR_INVALID',message:'Reset local store.',field:'after'}};
  await expect.poll(async()=> (await widget(c,'send-button')).enabled).toBe(false);expect((await widget(c,'error-message')).text).not.toBe('');
  expect((await widget(c,'reset-button')).enabled).toBe(true);
});
