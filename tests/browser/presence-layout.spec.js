const {test,expect}=require('@playwright/test');
const {fixture,Gui,accepted,received}=require('./fixtures');
class Manager extends Gui {
 launchArguments(){return ['tests/server_gui_driver.py'];}
 async status(user){return (await this.snapshot()).users.find(r=>r[0]===user)?.[1];}
 async listen(){await this.click('start-button');await expect.poll(async()=>(await this.snapshot()).widgets['server-status'].text).toBe('Running');return (await this.snapshot()).widgets['server-url'].text;}
}
let m,f;
test.beforeEach(async({browser})=>{m=await new Manager().start();f=await fixture(browser,{origin:await m.listen(),close:async()=>{}});});
test.afterEach(async()=>{try{if(f)await f.close();}finally{if(m)await m.quit();}});
const notifications=c=>c.proxy.auxiliaryHistory.filter(x=>x.url==='/api/v1/presence');
const state=async c=>c.kind==='gui'?(await c.snapshot()).widgets['presence-status'].text:c.page.getByTestId('presence-status').innerText();
for(const kind of ['gui','web','python'])test(`PRES-03 explicit offline and online without peer traffic (${kind})`,async()=>{
 const c=await f.client(kind,'bob');await expect.poll(()=>notifications(c).some(x=>JSON.parse(x.body).online===true&&x.status===200)).toBe(true);
 await expect.poll(()=>m.status('bob')).toBe('Online');await c.transport('offline');
 await expect.poll(()=>m.status('bob'),{timeout:8000}).toBe('Offline');
 expect(notifications(c).filter(x=>JSON.parse(x.body).online===false&&x.status===200)).toHaveLength(1);
 if(kind!=='python')await expect.poll(()=>state(c)).toBe('confirmed');
 const queued=await c.send('alice','Local offline queue');const start=c.proxy.apiHistory.length;
 const other=await f.client('web','alice');const incoming=await other.send('bob','Addressed to an offline user');await accepted(other,incoming);
 await expect.poll(()=>other.proxy.auxiliaryHistory.filter(x=>x.url==='/api/v1/users'&&x.method==='POST'&&x.status===200).length).toBeGreaterThanOrEqual(3);
 expect(await m.status('bob')).toBe('Offline');expect(c.proxy.apiHistory.slice(start)).toEqual([]);
 expect((await c.outbox()).find(x=>x.message_id===queued).state).toBe('queued');
 await c.transport('online');await expect.poll(()=>m.status('bob'),{timeout:8000}).toBe('Online');
 await accepted(c,queued);await received(other,'Local offline queue');await received(c,'Addressed to an offline user');
});
for(const kind of ['gui','web']) {
 test(`PRES-04 rejected and lost offline replies preserve queues (${kind})`,async()=>{
  const c=await f.client(kind,'bob');await expect.poll(()=>state(c)).toBe('confirmed');
  c.proxy.mode.presenceStatus=503;await c.transport('offline');await expect.poll(()=>state(c),{timeout:8000}).toBe('error');
  const id=await c.send('alice','Keep on notification error');expect((await c.outbox()).find(x=>x.message_id===id).state).toBe('queued');
  delete c.proxy.mode.presenceStatus;await c.transport('online');await expect.poll(()=>state(c)).toBe('confirmed');await accepted(c,id);
  c.proxy.mode.dropPresenceReply=true;await c.transport('offline');await expect.poll(()=>state(c),{timeout:8000}).toBe('error');
  await expect.poll(()=>m.status('bob')).toBe('Offline');const attempts=notifications(c).length;
  const other=await f.client('web','alice');await expect.poll(()=>other.proxy.auxiliaryHistory.filter(x=>x.url==='/api/v1/users'&&x.method==='POST').length).toBeGreaterThanOrEqual(3);
  expect(notifications(c)).toHaveLength(attempts);await c.transport('online');await expect.poll(()=>state(c)).toBe('confirmed');await expect.poll(()=>m.status('bob')).toBe('Online');
 });
 test(`PRES-05 held heartbeat and rapid mode changes preserve final intent (${kind})`,async()=>{
  const c=await f.client(kind,'bob');await expect.poll(()=>state(c)).toBe('confirmed');
  c.proxy.mode.announceResponseDelay=1500;const start=c.proxy.auxiliaryHistory.length;
  await expect.poll(()=>c.proxy.auxiliaryHistory.slice(start).some(x=>x.url==='/api/v1/users'&&x.held&&!x.delivered)).toBe(true);
  await c.transport('offline');await expect.poll(()=>m.status('bob'),{timeout:8000}).toBe('Offline');
  const old=c.proxy.auxiliaryHistory.slice(start).find(x=>x.held);await expect.poll(()=>old.delivered).toBe(true);
  expect(await m.status('bob')).toBe('Offline');delete c.proxy.mode.announceResponseDelay;
  c.proxy.mode.presenceResponseDelay=1000;const n=notifications(c).length;
  await c.transport('online');await expect.poll(()=>notifications(c).slice(n).some(x=>x.held&&!x.delivered)).toBe(true);
  await c.transport('offline');await expect.poll(()=>m.status('bob'),{timeout:8000}).toBe('Offline');await expect.poll(()=>state(c)).toBe('confirmed');
  expect(JSON.parse(notifications(c).at(-1).body).online).toBe(false);
  delete c.proxy.mode.presenceResponseDelay;await c.transport('online');await expect.poll(()=>m.status('bob')).toBe('Online');
 });
}
test('WEB-01 desktop layout, exact table details and narrow viewport',async()=>{
 const c=await f.client('web','bob');await c.page.setViewportSize({width:1280,height:900});
 const box=async id=>{const element=c.page.getByTestId(id);await expect(element).toBeVisible();return element.boundingBox();};
 const session=await box('session-panel'),directory=await box('directory-panel'),compose=await box('compose-panel');
 const inbox=await box('inbox-panel'),outbox=await box('outbox-panel');
 expect(session.y+session.height).toBeLessThanOrEqual(directory.y+2);expect(directory.height).toBeLessThanOrEqual(200);
 expect(directory.y+directory.height).toBeLessThanOrEqual(compose.y+2);expect(compose.y+compose.height).toBeLessThanOrEqual(inbox.y+2);
 expect(Math.abs(inbox.y-outbox.y)).toBeLessThanOrEqual(2);expect(inbox.x+inbox.width).toBeLessThanOrEqual(outbox.x+2);
 for(const r of [inbox,outbox])expect(r.y+r.height).toBeLessThanOrEqual(900);
 expect(await c.page.getByTestId('inbox-panel').locator('th').allTextContents()).toEqual(['Message ID','Sender','Text','Sequence']);
 expect(await c.page.getByTestId('outbox-panel').locator('th').allTextContents()).toEqual(['Message ID','Recipient','Text','State','Error','Order']);
 const other=await f.client('gui','alice');const exact='  한글 😀\n<not-html> & exact trailing spaces  ';
 await other.send('bob',exact);await received(c,exact);await c.page.getByTestId('inbox-item').first().click();await expect(c.page.getByTestId('inbox-detail')).toHaveText(exact,{useInnerText:false});
 expect(await c.page.getByTestId('inbox-detail').textContent()).toBe(exact);
 const id=await c.send('alice',exact);await accepted(c,id);const row=c.page.getByTestId('outbox-item').first();await row.focus();await row.press('Enter');expect(await c.page.getByTestId('outbox-detail').textContent()).toBe(exact);
 await c.page.setViewportSize({width:390,height:844});
 await expect(c.page.getByTestId('send-button')).toBeVisible();
 expect(await c.page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 const narrowIn=await box('inbox-panel'),narrowOut=await box('outbox-panel');expect(narrowIn.y+narrowIn.height).toBeLessThanOrEqual(narrowOut.y+2);
});
