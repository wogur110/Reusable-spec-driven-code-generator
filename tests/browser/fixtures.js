// Independent black-box fixtures. No generated client modules are imported.
const { spawn } = require('node:child_process');
const http = require('node:http');
const readline = require('node:readline');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { expect } = require('@playwright/test');
const ROOT = path.resolve(__dirname, '../..');
const PYTHON = process.env.TEST_PYTHON || 'python3';

function processLine(child, predicate, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const lines = readline.createInterface({ input: child.stdout });
    const timer = setTimeout(() => { lines.close(); reject(new Error('Process readiness timeout')); }, timeout);
    lines.on('line', line => {
      try { const item = JSON.parse(line); if (predicate(item)) { clearTimeout(timer); lines.close(); resolve(item); } } catch (_) {}
    });
    child.once('exit', code => { clearTimeout(timer); lines.close(); reject(new Error(`Process exited ${code}`)); });
  });
}

async function stop(child) {
  if (child.exitCode !== null || child.signalCode !== null) return;
  child.kill('SIGTERM');
  await new Promise(resolve => {
    const timer = setTimeout(() => { child.kill('SIGKILL'); }, 5000);
    child.once('exit', () => { clearTimeout(timer); resolve(); });
  });
}

async function server() {
  const child = spawn(PYTHON, ['server/main.py', '--port', '0', '--static-dir', 'generated/typescript-web/dist'], { cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'] });
  let errors = ''; child.stderr.on('data', b => { errors += b; });
  const ready = await processLine(child, v => v.event === 'ready').catch(e => { throw new Error(e.message + errors); });
  return { origin: ready.origin, close: () => stop(child) };
}

async function proxy(origin) {
  const mode = {}; const history = []; const apiHistory = []; const auxiliaryHistory = []; const assetHistory = []; const timers = new Set();
  const listener = http.createServer(async (req, res) => {
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    const api = req.url.startsWith('/api/');
    const route=req.url.split('?')[0];
    const messageApi=route==='/api/v1/messages';
    const directory=route==='/api/v1/users';
    const acknowledgment=route==='/api/v1/receipts';
    const entry = { method: req.method, url: req.url, body: body.toString(), failed: false };
    // Preserve existing message-only fault assertions; expose every API attempt separately.
    if (api) { apiHistory.push(entry); (messageApi ? history : auxiliaryHistory).push(entry); } else assetHistory.push(entry);
    const fail = (error) => { entry.failed = true; entry.error = error ? {code:error.code,message:error.message} : {code:'INJECTED_OUTAGE'}; if (!res.writableEnded && !res.destroyed) req.socket.destroy(); };
    if (api && mode.offline) return fail();
    const reply = (status, value, headers = {}) => {
      const data = typeof value === 'string' ? value : JSON.stringify(value);
      res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers }); res.end(data);
    };
    if (acknowledgment && mode.blockReceipts) return fail();
    if (acknowledgment && mode.ackStatus) return reply(mode.ackStatus,{error:{code:'INVALID_RECEIPT',message:'Injected receipt failure.',field:'through'}});
    if (directory && req.method==='POST' && mode.announceStatus) return reply(mode.announceStatus,{error:{code:'INTERNAL_ERROR',message:'Injected announcement failure.',field:null}});
    if (directory && req.method==='GET' && mode.usersPage !== undefined) {
      const value=mode.usersPage;
      const deliver=()=>{entry.delivered=true;if(!res.destroyed)reply(mode.usersStatus || 200,value);};
      if(mode.directoryDelay){entry.held=true;entry.response=JSON.stringify(value);const timer=setTimeout(()=>{timers.delete(timer);deliver();},mode.directoryDelay);timers.add(timer);return;}
      return deliver();
    }
    if (messageApi && req.method === 'POST' && mode.postStatus) {
      return reply(mode.postStatus, mode.errorBody ?? {error:{code:'INVALID_TEXT',message:'Injected rejection.',field:'text'}}, mode.postStatus === 302 ? {Location:'/api/v1/messages'} : {});
    }
    if (messageApi && req.method === 'GET' && mode.page) return reply(mode.getStatus || 200, typeof mode.page === 'function' ? mode.page(req.url) : mode.page);
    const forward = () => {
      // The retained server closes each response; never pool its upstream sockets.
      const upstream = http.request(new URL(req.url, origin), { agent: false, method: req.method, headers: {...req.headers, host: new URL(origin).host, connection:'close'} }, response => {
        const data = []; response.on('data', chunk => data.push(chunk));
        response.on('end', () => {
          entry.status = response.statusCode;
          const payload = Buffer.concat(data); if (api) entry.response = payload.toString();
          // Static diagnostics must not expose another client's source to repairs.
          if (acknowledgment && mode.dropReceiptAck) { mode.dropReceiptAck=false; return fail(); }
          if (messageApi && req.method === 'POST' && mode.dropAck) { mode.dropAck = false; return fail(); }
          if (messageApi && req.method === 'POST' && mode.receipt !== undefined) return reply(201, mode.receipt);
          const deliver = () => { entry.delivered = true; if (!res.destroyed) { res.writeHead(response.statusCode, response.headers); res.end(payload); } };
          if (messageApi && req.method === 'GET' && mode.getResponseDelay) {
            entry.held = true;
            const timer = setTimeout(() => { timers.delete(timer); deliver(); }, mode.getResponseDelay); timers.add(timer);
          } else deliver();
        });
      });
      upstream.on('error', fail); req.on('error', () => upstream.destroy());
      upstream.end(body);
    };
    if (messageApi && req.method === 'POST' && mode.delay) {
      const timer = setTimeout(() => { timers.delete(timer); if (!res.destroyed) forward(); }, mode.delay); timers.add(timer);
    } else forward();
  });
  await new Promise(resolve => listener.listen(0, '127.0.0.1', resolve));
  return { mode, history, apiHistory, auxiliaryHistory, assetHistory, origin:`http://127.0.0.1:${listener.address().port}`,
    async close() { for (const t of timers) clearTimeout(t); listener.closeAllConnections(); await new Promise(r => listener.close(r)); } };
}

class Cli {
  constructor(origin, state) { this.origin = origin; this.state = state; this.pending = new Map(); this.next = 0; }
  launchArguments(offline) { return ['generated/python-client/main.py', '--server', this.origin, '--state-dir', this.state, '--machine', '--transport', offline ? 'offline' : 'online']; }
  async start(offline = false) {
    this.process = spawn(PYTHON, this.launchArguments(offline), { cwd:ROOT, stdio:['pipe','pipe','pipe'] });
    this.errors = ''; this.process.stderr.on('data', b => { this.errors += b; });
    const lines = readline.createInterface({input:this.process.stdout});
    await new Promise((resolve,reject) => {
      const timer = setTimeout(() => reject(new Error('CLI ready timeout: ' + this.errors)), 10000);
      lines.on('line', line => {
        let item; try { item=JSON.parse(line); } catch (_) { reject(new Error('Non-JSON stdout: '+line)); return; }
        if(item.type === 'result') { const pending=this.pending.get(item.id); if(pending) { clearTimeout(pending.timer); this.pending.delete(item.id); pending.resolve(item); } }
        if(item.event === 'ready') { clearTimeout(timer); resolve(); }
      });
      this.process.once('exit', code => { clearTimeout(timer); reject(new Error(`CLI exit ${code}: ${this.errors}`)); });
    });
    return this;
  }
  command(command, params={}) {
    const id=String(++this.next);
    return new Promise((resolve,reject) => {
      const timer=setTimeout(() => { this.pending.delete(id); reject(new Error(`CLI ${command} timeout: ${this.errors}`)); }, 5000);
      this.pending.set(id,{resolve,timer}); this.process.stdin.write(JSON.stringify({id,command,...params})+'\n');
    });
  }
  async login(username) { const r=await this.command('login',{username}); expect(r.ok).toBe(true); this.username=username; }
  async send(recipient,text) { const r=await this.command('send',{recipient,text}); expect(r.ok).toBe(true); return r.data.message_id; }
  async inbox() { return (await this.command('inbox')).data.messages; }
  async outbox() { return (await this.command('outbox')).data.messages; }
  async status() { return (await this.command('status')).data; }
  async transport(mode) { expect((await this.command('transport',{mode})).ok).toBe(true); }
  async cursor() { return (await this.status()).cursor; }
  async quit() {
    if(this.process.exitCode !== null) return;
    const exit = new Promise(resolve => this.process.once('exit',resolve));
    expect((await this.command('quit')).ok).toBe(true);
    await Promise.race([exit,new Promise((_,reject)=>{const t=setTimeout(()=>reject(new Error('CLI shutdown timeout')),6000);t.unref();})]);
    expect(this.process.exitCode).toBe(0);
  }
  async close() { if(this.process) await stop(this.process); }
}

class Gui extends Cli {
  launchArguments(offline) { return ['tests/gui_driver.py', '--server', this.origin, '--state-dir', this.state, '--transport', offline ? 'offline' : 'online']; }
  async action(command,params={}) { const r=await this.command(command,params);expect(r.ok,JSON.stringify(r.error)).toBe(true);return r.data; }
  async snapshot() { return this.action('snapshot'); }
  async fill(widget,text) { return this.action('fill',{widget,text}); }
  async click(widget) { return this.action('click',{widget}); }
  async login(username) {
    await expect.poll(async()=> (await this.snapshot()).ready).toBe(true);
    await this.fill('username-input',username);await this.click('login-button');
    await expect.poll(async()=> (await this.snapshot()).widgets['current-user'].text).toBe(username);this.username=username;
  }
  async send(recipient,text) {
    const before=new Set((await this.outbox()).map(m=>m.message_id));
    await this.fill('recipient-input',recipient);await this.fill('message-input',text);await this.click('send-button');
    await expect.poll(async()=> (await this.outbox()).filter(m=>!before.has(m.message_id)).length).toBe(1);
    return (await this.outbox()).find(m=>!before.has(m.message_id)).message_id;
  }
  async inbox() { return (await this.snapshot()).inbox; }
  async outbox() { return (await this.snapshot()).outbox; }
  async cursor() { return (await this.snapshot()).cursor; }
  async transport(mode) { await this.action('select',{widget:'transport-mode',value:mode}); }
  async quit() {
    if(this.process.exitCode!==null)return;
    const exit=new Promise(resolve=>this.process.once('exit',resolve));
    await this.action('close');
    await Promise.race([exit,new Promise((_,reject)=>{const t=setTimeout(()=>reject(new Error('Desktop shutdown timeout')),6000);t.unref();})]);
    expect(this.process.exitCode).toBe(0);
  }
}

class Web {
  constructor(context,page,origin) { this.context=context;this.page=page;this.origin=origin; }
  async start() { const errors=[];this.page.on('pageerror',e=>errors.push(String(e)));this.page.on('requestfailed',r=>errors.push(r.url()+': '+r.failure()?.errorText));await this.page.goto(this.origin);try { await expect(this.page.getByTestId('app-ready')).toHaveAttribute('data-ready','true'); } catch(e) { throw new Error(e.message+'\nBrowser diagnostics: '+JSON.stringify(errors)); } return this; }
  async login(username) { await this.page.getByTestId('username-input').fill(username); await this.page.getByTestId('login-button').click(); await expect(this.page.getByTestId('current-user')).toHaveText(username); this.username=username; }
  async send(recipient,text) {
    const before = new Set((await this.outbox()).map(m=>m.message_id));
    await this.page.getByTestId('recipient-input').fill(recipient); await this.page.getByTestId('message-input').fill(text); await this.page.getByTestId('send-button').click();
    await expect.poll(async()=> (await this.outbox()).filter(m=>!before.has(m.message_id)).length).toBe(1);
    return (await this.outbox()).find(m=>!before.has(m.message_id)).message_id;
  }
  async inbox() { return this.page.getByTestId('inbox-item').evaluateAll(rows=>rows.map(row=>({message_id:row.dataset.messageId,sender:row.dataset.sender,sequence:Number(row.dataset.sequence),text:row.querySelector('[data-testid="message-text"]').textContent}))); }
  async outbox() { return this.page.getByTestId('outbox-item').evaluateAll(rows=>rows.map(row=>({message_id:row.dataset.messageId,state:row.dataset.state,local_order:Number(row.dataset.localOrder),recipient:row.querySelector('[data-testid="message-recipient"]').textContent,text:row.querySelector('[data-testid="message-text"]').textContent}))); }
  async transport(mode) { await this.page.getByTestId('transport-mode').selectOption(mode); }
  async cursor() {
    return this.page.evaluate(()=>new Promise((resolve,reject)=>{const open=indexedDB.open('reusable-spec-messenger');open.onerror=()=>reject(open.error);open.onsuccess=()=>{const db=open.result;const tx=db.transaction('metadata');const get=tx.objectStore('metadata').get('state');get.onsuccess=()=>resolve(get.result.receive_cursor);tx.oncomplete=()=>db.close();};}));
  }
  async close() { await this.context.close(); }
}

async function fixture(browser, suppliedBackend) {
  const backend=suppliedBackend || await server(); const dir=await fs.mkdtemp(path.join(os.tmpdir(),'spec-acceptance-'));
  const proxies=[]; const clients=[];
  return { backend,dir,proxies,clients,
    async client(kind,username) {
      const p=await proxy(backend.origin); proxies.push(p);
      let c;
      if(kind==='gui') c=await new Gui(p.origin,path.join(dir,`${kind}-${clients.length}`)).start();
      else if(kind==='python') c=await new Cli(p.origin,path.join(dir,`${kind}-${clients.length}`)).start();
      else {const context=await browser.newContext();try {c=await new Web(context,await context.newPage(),p.origin).start();} catch(error) {await context.close();throw new Error(error.message+'\nAsset proxy diagnostics: '+JSON.stringify(p.assetHistory));}}
      clients.push(c);c.proxy=p;c.kind=kind;if(username)await c.login(username);return c;
    },
    async close() { for(const c of clients)await c.close();for(const p of proxies)await p.close();await backend.close();await fs.rm(dir,{recursive:true,force:true}); }
  };
}

async function accepted(client,id) { await expect.poll(async()=> (await client.outbox()).find(m=>m.message_id===id)?.state).toBe('accepted'); }
async function received(client,text,count=1) { await expect.poll(async()=> (await client.inbox()).filter(m=>m.text===text).length).toBe(count); }
async function seed(origin,recipient,text='seed',extra={}) {
  const message={message_id:require('node:crypto').randomUUID(),sender:'seeder',recipient,text,...extra};
  const response=await fetch(origin+'/api/v1/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(message)});
  expect(response.status).toBe(201); return {...message,...await response.json()};
}
module.exports={fixture,Cli,Gui,Web,accepted,received,seed,ROOT,PYTHON,stop};
