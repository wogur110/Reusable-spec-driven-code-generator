const { test,expect }=require('@playwright/test');
const { fixture,accepted,received,seed,ROOT,PYTHON }=require('./fixtures');
const { spawn }=require('node:child_process');
let f;
test.beforeEach(async({browser})=>{f=await fixture(browser);});
test.afterEach(async()=>{if(f)await f.close();});

async function sendError(c,id) {
  if(c.kind==='python')await expect.poll(async()=>Boolean((await c.outbox()).find(x=>x.message_id===id)?.error)).toBe(true);
  else await expect(c.page.locator(`[data-testid="outbox-item"][data-message-id="${id}"]`).getByTestId('message-error')).not.toHaveText('');
}

for(const kind of ['python','web']) {
  const other=kind==='python'?'web':'python';
  test(`AT-02 AT-03 AT-04 fixed offline scenario and Unicode (${kind} Alice)`,async()=>{
    const alice=await f.client(kind,'alice'),bob=await f.client(other,'bob');
    let id=await alice.send('bob','Hi Bob, I have something important to tell you');await accepted(alice,id);await received(bob,'Hi Bob, I have something important to tell you');
    id=await bob.send('alice','What is it?');await accepted(bob,id);await received(alice,'What is it?');
    alice.proxy.mode.offline=true;const a=await alice.send('bob','Alice queued while offline');
    await expect.poll(()=>alice.proxy.history.filter(x=>x.method==='POST'&&x.failed&&x.body.includes(a)).length).toBeGreaterThan(0);
    expect((await alice.outbox()).find(x=>x.message_id===a).state).toBe('queued');
    bob.proxy.mode.offline=true;const b=await bob.send('alice','Bob queued while offline');
    await expect.poll(()=>bob.proxy.history.filter(x=>x.method==='POST'&&x.failed&&x.body.includes(b)).length).toBeGreaterThan(0);
    alice.proxy.mode.offline=false;await accepted(alice,a);expect((await bob.outbox()).find(x=>x.message_id===b).state).toBe('queued');
    alice.proxy.mode.offline=true;bob.proxy.mode.offline=false;await accepted(bob,b);await received(bob,'Alice queued while offline');
    alice.proxy.mode.offline=false;await received(alice,'Bob queued while offline');
    expect((await alice.inbox()).map(m=>m.text)).toEqual(['What is it?','Bob queued while offline']);
    expect((await bob.inbox()).map(m=>m.text)).toEqual(['Hi Bob, I have something important to tell you','Alice queued while offline']);
    for(const c of [alice,bob])expect((await c.outbox()).map(m=>m.state)).toEqual(['accepted','accepted']);
    const unicode='  한글 😀\nsecond line  ';await alice.send('bob',unicode);await received(bob,unicode);
    await bob.send('alice',unicode.replace('한글','답장'));await received(alice,unicode.replace('한글','답장'));
  });
  test(`AT-05 recipient launches later (${kind})`,async()=>{
    await seed(f.backend.origin,'carol','Before first launch');const c=await f.client(kind,'carol');await received(c,'Before first launch');
  });
  test(`AT-06 FIFO and receiving while send fails (${kind})`,async()=>{
    const c=await f.client(kind,'alice');c.proxy.mode.offline=true;
    const ids=[];for(const text of ['first','second','third'])ids.push(await c.send('bob',text));
    c.proxy.mode.offline=false;c.proxy.mode.postStatus=500;
    await seed(f.backend.origin,'alice','Incoming despite failed send');await received(c,'Incoming despite failed send');
    const attempts=c.proxy.history.filter(x=>x.method==='POST'&&!x.failed);expect(attempts.length).toBeGreaterThan(0);
    expect(attempts.every(x=>JSON.parse(x.body).message_id===ids[0])).toBe(true);
    delete c.proxy.mode.postStatus;for(const id of ids)await accepted(c,id);
    const page=await (await fetch(f.backend.origin+'/api/v1/messages?recipient=bob&after=0')).json();expect(page.messages.map(x=>x.text)).toEqual(['first','second','third']);
  });
  test(`AT-07 lost acknowledgment retains ID and deduplicates (${kind})`,async()=>{
    const c=await f.client(kind,'alice');const receiver=await f.client(other,'bob');c.proxy.mode.dropAck=true;
    const id=await c.send('bob','Lost reply');await accepted(c,id);await received(receiver,'Lost reply');
    const posts=c.proxy.history.filter(x=>x.method==='POST'&&JSON.parse(x.body).message_id===id);
    expect(posts.length).toBeGreaterThanOrEqual(2);expect(new Set(posts.map(x=>x.body)).size).toBe(1);
    expect(posts.map(x=>x.status)).toContain(200);
    const page=await (await fetch(f.backend.origin+'/api/v1/messages?recipient=bob&after=0')).json();expect(page.messages.length).toBe(1);
  });
  test(`AT-09 persisted identity queue inbox and cursor (${kind})`,async()=>{
    const c=await f.client(kind,'alice');c.proxy.mode.offline=true;const id=await c.send('bob','Restart queue');
    if(kind==='python'){await c.quit();await c.start();expect((await c.status()).username).toBe('alice');}else{await c.page.reload();await expect(c.page.getByTestId('current-user')).toHaveText('alice');}
    expect((await c.outbox()).find(x=>x.message_id===id)?.text).toBe('Restart queue');
    c.proxy.mode.offline=false;await accepted(c,id);await seed(f.backend.origin,'alice','Persist inbox');await received(c,'Persist inbox');const cursor=await c.cursor();
    if(kind==='python'){await c.quit();await c.start();}else{await c.page.reload();await expect(c.page.getByTestId('app-ready')).toHaveAttribute('data-ready','true');}
    await received(c,'Persist inbox');expect(await c.cursor()).toBe(cursor);
    const page=await (await fetch(f.backend.origin+'/api/v1/messages?recipient=bob&after=0')).json();expect(page.messages.filter(m=>m.message_id===id).length).toBe(1);
  });
  test(`AT-10 205-message pagination (${kind})`,async()=>{
    for(let i=0;i<205;i++)await seed(f.backend.origin,'alice',`message ${i}`);
    const c=await f.client(kind,'alice');await expect.poll(async()=> (await c.inbox()).length).toBe(205);
    expect((await c.inbox()).map(x=>x.sequence)).toEqual(Array.from({length:205},(_,i)=>i+1));expect(await c.cursor()).toBe(205);
    const pages=c.proxy.history.filter(x=>x.method==='GET'&&x.response).map(x=>JSON.parse(x.response));
    expect(pages.map(x=>x.next_after)).toEqual(expect.arrayContaining([100,200,205]));expect(pages.every(x=>x.messages.length<=100)).toBe(true);
  });
  test(`AT-11 invalid drafts and byte limits (${kind})`,async()=>{
    const c=await f.client(kind,'alice');await c.transport('offline');
    for(const [recipient,text] of [['Bob','x'],['alice','x'],['bob',''],['bob','a'.repeat(4097)],['bob','😀'.repeat(1025)]]) {
      if(kind==='python')expect((await c.command('send',{recipient,text})).ok).toBe(false);
      else {await c.page.getByTestId('recipient-input').fill(recipient);await c.page.getByTestId('message-input').fill(text);await c.page.getByTestId('send-button').click();await expect(c.page.getByTestId('error-message')).not.toHaveText('');await expect(c.page.getByTestId('message-input')).toHaveValue(text);}
    }
    expect(await c.outbox()).toEqual([]);expect(c.proxy.history.filter(x=>x.method==='POST').length).toBe(0);
    for(const text of [' ','a'.repeat(4096),'😀'.repeat(1024)])await c.send('bob',text);
    expect((await c.outbox()).map(x=>x.text)).toEqual([' ','a'.repeat(4096),'😀'.repeat(1024)]);
    await c.transport('online');for(const row of await c.outbox())await accepted(c,row.message_id);
  });
  test(`AT-10 maximum-size JSON-escaped receive page (${kind})`,async()=>{
    const text='\u0000'.repeat(4096);
    for(let i=0;i<100;i++)await seed(f.backend.origin,'alice',text);
    const c=await f.client(kind,'alice');await expect.poll(async()=> (await c.inbox()).length).toBe(100);
    expect((await c.inbox()).every(row=>row.text===text)).toBe(true);expect(await c.cursor()).toBe(100);
  });
  test(`AT-12 development transport (${kind})`,async()=>{
    const c=await f.client(kind,'alice');await c.transport('offline');const id=await c.send('bob','Toggle queue');expect((await c.outbox()).find(x=>x.message_id===id).state).toBe('queued');
    await c.transport('online');await accepted(c,id);
  });
  test(`AT-13 retryable send outcomes and stable IDs (${kind})`,async()=>{
    const c=await f.client(kind,'alice');
    for(const status of [408,429,500,302]) {
      c.proxy.mode.postStatus=status;const id=await c.send('bob',`status ${status}`);
      await expect.poll(()=>c.proxy.history.filter(x=>x.method==='POST'&&x.body.includes(id)).length).toBeGreaterThan(0);
      await sendError(c,id);
      expect((await c.outbox()).find(x=>x.message_id===id).state).toBe('queued');delete c.proxy.mode.postStatus;await accepted(c,id);
    }
    if(kind==='python')await expect.poll(async()=> (await c.status()).last_error).toBe(null);
    else await expect(c.page.getByTestId('connection-status')).toHaveAttribute('data-state','online');
    c.proxy.mode.delay=6500;const id=await c.send('bob','timeout');
    await expect.poll(async()=>kind==='python'?(await c.status()).last_error!==null:(await c.page.getByTestId('connection-status').getAttribute('data-state'))==='offline').toBe(true);
    expect((await c.outbox()).find(x=>x.message_id===id).state).toBe('queued');delete c.proxy.mode.delay;await accepted(c,id);
    for(const receipt of ['not JSON',{message_id:'wrong',sender:'alice',recipient:'bob',sequence:1}]) {
      c.proxy.mode.receipt=receipt;const bad=await c.send('bob','bad receipt '+String(receipt));
      await expect.poll(()=>c.proxy.history.filter(x=>x.method==='POST'&&x.body.includes(bad)&&x.status).length).toBeGreaterThan(0);
      await sendError(c,bad);
      expect((await c.outbox()).find(x=>x.message_id===bad).state).toBe('queued');delete c.proxy.mode.receipt;await accepted(c,bad);
    }
  });
  test(`AT-13 permanent rejection permits subsequent messages (${kind})`,async()=>{
    const c=await f.client(kind,'alice');
    for(const status of [400,409]) {
      c.proxy.mode.postStatus=status;c.proxy.mode.errorBody='not JSON';const id=await c.send('bob','Rejected '+status);
      await expect.poll(async()=> (await c.outbox()).find(x=>x.message_id===id).state).toBe('failed');delete c.proxy.mode.postStatus;delete c.proxy.mode.errorBody;
      const next=await c.send('bob','Next '+status);await accepted(c,next);
    }
  });
  test(`AT-13 AT-17 malformed receive pages roll back atomically (${kind})`,async()=>{
    const c=await f.client(kind,'alice');c.proxy.mode.offline=true;
    const one=await seed(f.backend.origin,'alice','one'),two=await seed(f.backend.origin,'alice','two');
    for(const bad of [ {...two,recipient:'bob'}, {...two,sequence:3}, {...two,unknown:true} ]) {
      c.proxy.mode.page={messages:[one,bad],next_after:2};c.proxy.mode.offline=false;const before=c.proxy.history.length;
      await expect.poll(()=>c.proxy.history.slice(before).filter(x=>x.method==='GET').length).toBeGreaterThan(1);
      expect(await c.inbox()).toEqual([]);expect(await c.cursor()).toBe(0);
    }
    c.proxy.mode.page={messages:[one,two],next_after:1};let n=c.proxy.history.length;
    await expect.poll(()=>c.proxy.history.slice(n).filter(x=>x.method==='GET').length).toBeGreaterThan(1);expect(await c.inbox()).toEqual([]);expect(await c.cursor()).toBe(0);
    delete c.proxy.mode.page;await received(c,'two');expect(await c.cursor()).toBe(2);
    c.proxy.mode.page={messages:[one,two],next_after:2};n=c.proxy.history.length;
    await expect.poll(()=>c.proxy.history.slice(n).filter(x=>x.method==='GET').length).toBeGreaterThan(1);expect((await c.inbox()).length).toBe(2);expect(await c.cursor()).toBe(2);
  });
  test(`AT-13 cursor-invalid pauses both directions (${kind})`,async()=>{
    const c=await f.client(kind,'alice');c.proxy.mode.getStatus=409;c.proxy.mode.page={error:{code:'CURSOR_INVALID',message:'Reset local store.',field:'after'}};
    if(kind==='python')await expect.poll(async()=> (await c.status()).sync_paused).toBe(true);
    else await expect(c.page.getByTestId('send-button')).toBeDisabled();
    const before=c.proxy.history.length;await c.transport('online');
    if(kind==='python') {expect((await c.command('send',{recipient:'bob',text:'blocked'})).ok).toBe(false);expect((await c.command('login',{username:'alice'})).ok).toBe(true);}
    else await expect(c.page.getByTestId('send-button')).toBeDisabled();
    expect(c.proxy.history.length).toBe(before);
  });
}

test('AT-01 browser invalid login and confirmed reset preserves unrelated storage',async()=>{
  const c=await f.client('web');await c.page.getByTestId('username-input').fill('Alice');await c.page.getByTestId('login-button').click();await expect(c.page.getByTestId('error-message')).not.toHaveText('');await c.login('alice');
  await c.page.evaluate(()=>localStorage.setItem('unrelated','keep'));
  await c.transport('offline');await c.send('bob','reset me');await c.page.getByTestId('reset-button').click();
  expect((await c.outbox()).length).toBe(1);await c.page.reload();await expect(c.page.getByTestId('current-user')).toHaveText('alice');
  await c.page.getByTestId('reset-button').click();await c.page.getByTestId('reset-confirm').click();await expect(c.page.getByTestId('username-input')).toBeVisible();
  expect(await c.outbox()).toEqual([]);expect(await c.page.evaluate(()=>localStorage.getItem('unrelated'))).toBe('keep');await c.login('carol');
});
test('AT-12 actual browser offline queues then reconnects',async()=>{
  const c=await f.client('web','alice');let failures=0;c.page.on('requestfailed',r=>{if(r.url().includes('/api/'))failures++;});
  await c.context.setOffline(true);const id=await c.send('bob','Browser network offline');await expect.poll(()=>failures).toBeGreaterThan(0);expect((await c.outbox())[0].state).toBe('queued');
  await c.context.setOffline(false);await accepted(c,id);
});
test('AT-16 input responsiveness and six-second shutdown',async()=>{
  const c=await f.client('python','alice');c.proxy.mode.delay=6500;await c.send('bob','slow');await expect.poll(()=>c.proxy.history.some(x=>x.method==='POST')).toBe(true);
  const start=Date.now();expect((await c.status()).username).toBe('alice');expect(Date.now()-start).toBeLessThan(2000);await c.quit();expect(Date.now()-start).toBeLessThan(6000);
  const web=await f.client('web','carol');web.proxy.mode.delay=6500;await web.send('bob','slow web');await web.page.getByTestId('message-input').fill('draft remains usable');await expect(web.page.getByTestId('message-input')).toHaveValue('draft remains usable');
});
test('AT-16 browser unsupported store version is visible without deletion',async()=>{
  const c=await f.client('web','alice');await c.page.goto('about:blank');
  await c.page.goto(c.origin+'/main-does-not-exist');
  await c.page.evaluate(()=>new Promise((resolve,reject)=>{const req=indexedDB.open('reusable-spec-messenger',999);req.onerror=()=>reject(req.error);req.onsuccess=()=>{req.result.close();resolve();};}));
  await c.page.goto(c.origin);await expect(c.page.getByTestId('error-message')).not.toHaveText('');await expect(c.page.getByTestId('app-ready')).toHaveAttribute('data-ready','false');
  expect(await c.page.evaluate(()=>new Promise(resolve=>{const req=indexedDB.open('reusable-spec-messenger');req.onsuccess=()=>{const version=req.result.version;req.result.close();resolve(version);};}))).toBe(999);
});
test('AT-14 browser resources remain local and render text safely',async()=>{
  const c=await f.client('web','alice');const urls=[];c.page.on('request',r=>urls.push(r.url()));await c.page.reload();await expect(c.page.getByTestId('app-ready')).toHaveAttribute('data-ready','true');
  const text='<img src=x onerror="window.injection=true">';await seed(f.backend.origin,'alice',text);await received(c,text);expect(await c.page.evaluate(()=>window.injection)).toBeUndefined();
  expect(urls.every(url=>new URL(url).origin===c.origin)).toBe(true);
});
