const {test,expect}=require('@playwright/test');
const {fixture,Gui,accepted,received}=require('./fixtures');
class ServerWindow extends Gui {
  launchArguments(){return ['tests/server_gui_driver.py'];}
  async value(name){return (await this.snapshot()).widgets[name].text;}
  async listen(){await this.click('start-button');await expect.poll(()=>this.value('server-status')).toBe('Running');return this.value('server-url');}
  async halt(){await this.click('stop-button');await expect.poll(()=>this.value('server-status')).toBe('Stopped');}
}
let manager,f;
test.beforeEach(async({browser})=>{
  manager=await new ServerWindow().start();
  const origin=await manager.listen();
  f=await fixture(browser,{origin,close:async()=>{}});
});
test.afterEach(async()=>{if(f)await f.close();if(manager)await manager.quit();});

test('SG-05 GUI-managed server supports full desktop/browser offline scenario and monitor',async()=>{
  const alice=await f.client('gui','alice'),bob=await f.client('web','bob');
  let id=await alice.send('bob','Hi Bob, I have something important to tell you');await accepted(alice,id);await received(bob,'Hi Bob, I have something important to tell you');
  id=await bob.send('alice','What is it?');await accepted(bob,id);await received(alice,'What is it?');
  alice.proxy.mode.offline=true;const a=await alice.send('bob','Alice queued while offline');
  await expect.poll(()=>alice.proxy.history.some(x=>x.method==='POST'&&x.failed&&x.body.includes(a))).toBe(true);
  bob.proxy.mode.offline=true;const b=await bob.send('alice','Bob queued while offline');
  await expect.poll(()=>bob.proxy.history.some(x=>x.method==='POST'&&x.failed&&x.body.includes(b))).toBe(true);
  alice.proxy.mode.offline=false;await accepted(alice,a);expect((await bob.outbox()).find(x=>x.message_id===b).state).toBe('queued');
  alice.proxy.mode.offline=true;bob.proxy.mode.offline=false;await received(bob,'Alice queued while offline');await accepted(bob,b);
  alice.proxy.mode.offline=false;await received(alice,'Bob queued while offline');
  expect((await alice.inbox()).map(x=>x.text)).toEqual(['What is it?','Bob queued while offline']);
  expect((await bob.inbox()).map(x=>x.text)).toEqual(['Hi Bob, I have something important to tell you','Alice queued while offline']);
  const text='  한글 😀\nserver monitor  ';id=await alice.send('bob',text);await accepted(alice,id);await received(bob,text);
  await expect.poll(()=>manager.value('message-count')).toBe('5');
  const rows=(await manager.snapshot()).messages;
  expect(rows.find(row=>row[2]===id)).toEqual(['alice','bob',id,'3',text]);
  expect(await manager.value('server-status')).toBe('Running');
});

test('SG-06 GUI Stop queues sends and restart requires fresh client stores',async()=>{
  const alice=await f.client('gui','alice'),bob=await f.client('web','bob');
  let id=await alice.send('bob','Old session');await accepted(alice,id);await received(bob,'Old session');
  const session=await manager.value('session-id');
  await manager.halt();
  await expect(fetch(f.backend.origin+'/health')).rejects.toThrow();
  id=await alice.send('bob','Queued after Stop');
  await expect.poll(()=>alice.proxy.history.some(x=>x.method==='POST'&&x.failed&&x.body.includes(id))).toBe(true);
  expect((await alice.outbox()).find(x=>x.message_id===id).state).toBe('queued');
  await alice.close();await bob.close();
  await manager.fill('port-input',new URL(f.backend.origin).port);
  expect(await manager.listen()).toBe(f.backend.origin);
  expect(await manager.value('session-id')).not.toBe(session);
  expect(await manager.value('message-count')).toBe('0');
  const freshAlice=await f.client('gui','alice'),freshBob=await f.client('web','bob');
  expect(await freshAlice.inbox()).toEqual([]);expect(await freshBob.inbox()).toEqual([]);
  id=await freshBob.send('alice','Fresh session');await accepted(freshBob,id);await received(freshAlice,'Fresh session');
  await expect.poll(()=>manager.value('message-count')).toBe('1');
});
