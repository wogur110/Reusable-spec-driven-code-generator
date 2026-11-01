const {test,expect}=require('@playwright/test');
const {fixture,Gui,accepted,received}=require('./fixtures');
class ServerWindow extends Gui {
  launchArguments(){return ['tests/server_gui_driver.py'];}
  async value(name){return (await this.snapshot()).widgets[name].text;}
  async listen(){await this.click('start-button');await expect.poll(()=>this.value('server-status')).toBe('Running');return this.value('server-url');}
  async selectUser(username){await this.action('tab',{widget:'server-tabs',text:'Users'});await expect.poll(async()=>(await this.snapshot()).users.map(row=>row[0])).toContain(username);await this.action('row',{widget:'users',iid:username});await expect.poll(()=>this.value('selected-user')).toBe(username);}
}
let manager,f;
test.beforeEach(async({browser})=>{manager=await new ServerWindow().start();const origin=await manager.listen();f=await fixture(browser,{origin,close:async()=>{}});});
test.afterEach(async()=>{try{if(f)await f.close();}finally{if(manager)await manager.quit();}});
async function users(c){return c.kind==='gui'?(await c.snapshot()).users.map(row=>row.username):c.page.getByTestId('user-item').evaluateAll(rows=>rows.map(row=>row.dataset.username));}
async function state(c,name){return c.kind==='gui'?(await c.snapshot()).widgets[name].text:c.page.getByTestId(name).innerText();}
async function fill(c,name,value){if(c.kind==='gui')await c.fill(name,value);else await c.page.getByTestId(name).fill(value);}
async function click(c,name){if(c.kind==='gui')await c.click(name);else await c.page.getByTestId(name).click();}
async function pick(c,name){if(c.kind==='gui')await c.action('row',{widget:'user-directory',iid:name});else await c.page.locator(`[data-testid="user-item"][data-username="${name}"]`).click();}
async function draft(c){return c.kind==='gui'?(await c.snapshot()).widgets['message-input'].text:c.page.getByTestId('message-input').inputValue();}
async function recipient(c){return c.kind==='gui'?(await c.snapshot()).widgets['recipient-input'].text:c.page.getByTestId('recipient-input').inputValue();}
async function announce(username){expect((await fetch(f.backend.origin+'/api/v1/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username})})).status).toBe(200);}
async function reset(c){await click(c,'reset-button');await click(c,'reset-confirm');if(c.kind==='gui')await expect.poll(async()=>(await c.snapshot()).widgets['username-input'].visible).toBe(true);else await expect(c.page.getByTestId('username-input')).toBeVisible();}
for(const kind of ['gui','web']) {
 const other=kind==='gui'?'web':'gui';
 test(`DIR-04 DIR-08 shared list, click-to-address, offline unknown and manual recipient (${kind})`,async()=>{
  const alice=await f.client(kind,'alice'),bob=await f.client(other,'bob');await announce('carol');
  await expect.poll(()=>users(alice)).toEqual(['bob','carol']);
  await expect.poll(()=>users(bob)).toEqual(['alice','carol']);
  await expect.poll(async()=>(await manager.snapshot()).users.map(row=>row[0])).toEqual(['alice','bob','carol']);
  const text='  한글 😀\nselected recipient  ';await fill(alice,'message-input',text);await fill(alice,'user-filter','BO');
  await expect.poll(()=>users(alice)).toEqual(['bob']);await pick(alice,'bob');
  expect(await recipient(alice)).toBe('bob');expect(await draft(alice)).toBe(text);expect(await alice.outbox()).toEqual([]);
  expect(alice.proxy.history.filter(x=>x.method==='POST')).toHaveLength(0);
  await click(alice,'send-button');await received(bob,text);
  await fill(alice,'user-filter','');await alice.transport('offline');
  await expect.poll(()=>state(alice,'directory-status')).toBe('stale');expect(await users(alice)).toContain('bob');
  const queued=await alice.send('bob','Unknown until accepted');await manager.selectUser('alice');
  expect((await manager.snapshot())['user-sent'].some(row=>row[1]===queued)).toBe(false);
  expect(await manager.value('queue-notice')).toContain('Offline client queues: unknown');
  await alice.transport('online');await accepted(alice,queued);await received(bob,'Unknown until accepted');
  const manual=await alice.send('dave','Unlisted recipient');await accepted(alice,manual);
  await click(alice,'user-refresh');await expect.poll(()=>users(alice)).toContain('dave');
  await fill(alice,'recipient-input','carol');await fill(alice,'message-input','Offline recipients remain selectable');
  const count=(await alice.outbox()).length;await pick(alice,'dave');
  expect(await recipient(alice)).toBe('dave');expect(await draft(alice)).toBe('Offline recipients remain selectable');expect(await alice.outbox()).toHaveLength(count);
 });
 test(`DIR-05 queued until durable receipt and lost report reply retries (${kind})`,async()=>{
  const sender=await f.client(other,'alice'),receiver=await f.client(kind,'bob');receiver.proxy.mode.blockReceipts=true;
  const text='  Recipient stored\n한글 😀  ';const id=await sender.send('bob',text);await accepted(sender,id);await received(receiver,text);
  expect(await receiver.cursor()).toBe(1);await manager.selectUser('bob');
  await expect.poll(()=>manager.value('user-queued-count')).toBe('1');expect(await manager.value('user-received-count')).toBe('0');
  await expect.poll(()=>receiver.proxy.auxiliaryHistory.some(x=>x.url==='/api/v1/receipts'&&x.failed&&JSON.parse(x.body).through===1)).toBe(true);
  await manager.click('user-refresh');expect(await manager.value('user-queued-count')).toBe('1');
  await manager.action('tab',{widget:'activity-tabs',text:'Queued'});await manager.action('row',{widget:'user-queued',iid:'alice:'+id});
  expect(await manager.value('user-message-detail')).toBe(text);
  receiver.proxy.mode.dropReceiptAck=true;delete receiver.proxy.mode.blockReceipts;
  await expect.poll(()=>receiver.proxy.auxiliaryHistory.some(x=>x.url==='/api/v1/receipts'&&x.status===200&&x.failed&&JSON.parse(x.body).through===1)).toBe(true);
  await expect.poll(()=>receiver.proxy.auxiliaryHistory.filter(x=>x.url==='/api/v1/receipts'&&x.status===200&&JSON.parse(x.body).through===1).length).toBeGreaterThanOrEqual(2);
  await expect.poll(()=>manager.value('user-received-count')).toBe('1');expect(await manager.value('user-queued-count')).toBe('0');
  expect((await receiver.inbox()).filter(row=>row.message_id===id)).toHaveLength(1);
  await manager.selectUser('alice');expect((await manager.snapshot())['user-sent'].find(row=>row[1]===id)[3]).toBe('received');
 });
 test(`DIR-06 bad pages cannot be acknowledged; auxiliary failures do not block messaging (${kind})`,async()=>{
  const receiver=await f.client(kind,'bob'),sender=await f.client(other,'alice');await expect.poll(()=>users(receiver)).toContain('alice');
  receiver.proxy.mode.usersPage={users:[{username:'alice',online:'yes'}]};receiver.proxy.mode.announceStatus=503;receiver.proxy.mode.ackStatus=503;
  receiver.proxy.mode.page={messages:[{message_id:'11111111-1111-4111-8111-111111111111',sender:'alice',recipient:'bob',text:'uncommitted',sequence:1},{bad:true}],next_after:2};
  await expect.poll(()=>receiver.proxy.history.some(x=>x.method==='GET'&&x.status===undefined)).toBe(true);
  await expect.poll(()=>receiver.proxy.auxiliaryHistory.filter(x=>x.url==='/api/v1/receipts').length).toBeGreaterThan(1);
  expect(await receiver.cursor()).toBe(0);expect(await receiver.inbox()).toEqual([]);
  expect(receiver.proxy.auxiliaryHistory.filter(x=>x.url==='/api/v1/receipts').every(x=>JSON.parse(x.body).through===0)).toBe(true);
  delete receiver.proxy.mode.page;const id=await sender.send('bob','Receive despite auxiliary errors');await accepted(sender,id);await received(receiver,'Receive despite auxiliary errors');
  const outgoing=await receiver.send('alice','Send despite auxiliary errors');await accepted(receiver,outgoing);await received(sender,'Send despite auxiliary errors');
  await expect.poll(()=>state(receiver,'directory-status')).toBe('error');expect(await users(receiver)).toContain('alice');
  await manager.selectUser('bob');expect(await manager.value('user-received-count')).toBe('0');
  delete receiver.proxy.mode.usersPage;delete receiver.proxy.mode.announceStatus;delete receiver.proxy.mode.ackStatus;
  await click(receiver,'user-refresh');await expect.poll(()=>state(receiver,'directory-status')).toBe('current');await expect.poll(()=>manager.value('user-received-count')).toBe('1');
 });
 test(`DIR-07 restart re-reports durable cursor and reset discards held directory (${kind})`,async()=>{
  const receiver=await f.client(kind,'bob'),sender=await f.client(other,'alice');receiver.proxy.mode.blockReceipts=true;
  const id=await sender.send('bob','Persisted receipt retry');await accepted(sender,id);await received(receiver,'Persisted receipt retry');expect(await receiver.cursor()).toBe(1);
  if(kind==='gui'){await receiver.quit();await receiver.start();await expect.poll(()=>state(receiver,'current-user')).toBe('bob');}
  else{await receiver.page.reload();await expect(receiver.page.getByTestId('current-user')).toHaveText('bob');}
  delete receiver.proxy.mode.blockReceipts;await manager.selectUser('bob');await expect.poll(()=>manager.value('user-received-count')).toBe('1');
  expect((await receiver.inbox()).map(row=>row.message_id)).toEqual([id]);
  receiver.proxy.mode.usersPage={users:[{username:'old_only',online:true}]};receiver.proxy.mode.directoryDelay=1500;
  const start=receiver.proxy.auxiliaryHistory.length;await click(receiver,'user-refresh');
  await expect.poll(()=>receiver.proxy.auxiliaryHistory.slice(start).some(x=>x.held&&!x.delivered)).toBe(true);
  await reset(receiver);delete receiver.proxy.mode.usersPage;delete receiver.proxy.mode.directoryDelay;
  await receiver.login('carol');await announce('dave');await expect.poll(()=>users(receiver)).toContain('dave');
  await expect.poll(()=>receiver.proxy.auxiliaryHistory.slice(start).some(x=>x.held&&x.delivered)).toBe(true);
  expect(await users(receiver)).not.toContain('old_only');expect(await users(receiver)).not.toContain('carol');
  expect(await receiver.inbox()).toEqual([]);expect(await receiver.outbox()).toEqual([]);
 });
}
