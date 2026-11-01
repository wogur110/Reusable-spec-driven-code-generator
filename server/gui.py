"""Local desktop controls for the retained in-memory messaging server."""
import argparse
from pathlib import Path
import queue
import signal
import sys
import threading
import uuid
import webbrowser

# Keep --help available on installations without Tk or a desktop display.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server.main import Server


class ServerApp:
    def __init__(self, root, port=8765, static_dir=None):
        import tkinter as tk
        from tkinter import ttk
        self.root = root
        self.events = queue.Queue()
        self.server = None
        self.thread = None
        self.state = 'Stopped'
        self.closing = False
        self.destroyed = False
        self.last_messages = None
        self.last_requests = None
        self.widgets = w = {}
        root.title('Local Messenger - Server')
        root.geometry('1050x760')
        root.minsize(720, 560)
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=12)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='Port (0 chooses an available port)').grid(row=0, column=0, sticky='w')
        w['port-input'] = ttk.Entry(frame)
        w['port-input'].insert(0, str(port))
        w['port-input'].grid(row=0, column=1, sticky='ew')
        ttk.Label(frame, text='Browser assets directory').grid(row=1, column=0, sticky='w')
        w['static-input'] = ttk.Entry(frame)
        w['static-input'].insert(0, str(static_dir or ROOT/'generated/typescript-web/dist'))
        w['static-input'].grid(row=1, column=1, sticky='ew')
        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky='w', pady=8)
        for name, label, command in [('start-button','Start',self.start),('stop-button','Stop',self.stop),('open-browser','Open browser',self.open_browser)]:
            w[name] = ttk.Button(buttons, text=label, command=command)
            w[name].pack(side='left', padx=(0,8))
        for row, (name, label) in enumerate([('server-status','Status'),('server-url','Listening URL'),('session-id','Session'),('message-count','Unique accepted messages'),('response-count','Completed HTTP responses'),('error-count','HTTP error responses')], 3):
            ttk.Label(frame, text=label).grid(row=row,column=0,sticky='w')
            w[name] = ttk.Label(frame, text='0' if name.endswith('-count') else '')
            w[name].grid(row=row,column=1,sticky='w')
        w['session-notice'] = ttk.Label(frame, text='Stopping or closing discards server messages. Every Start creates a new session: use fresh/reset client stores.',wraplength=950)
        w['session-notice'].grid(row=9,column=0,columnspan=2,sticky='ew',pady=8)
        w['error-message'] = ttk.Label(frame,text='',foreground='#a00000',wraplength=950)
        w['error-message'].grid(row=10,column=0,columnspan=2,sticky='ew')
        frame.rowconfigure(11, weight=1)
        tabs = w['server-tabs'] = ttk.Notebook(frame)
        tabs.grid(row=11, column=0, columnspan=2, sticky='nsew')
        overview = ttk.Frame(tabs); users_panel = ttk.Frame(tabs)
        tabs.add(overview, text='Overview'); tabs.add(users_panel, text='Users')
        frame = overview; frame.columnconfigure(1, weight=1)
        for row, name, title, columns in [(11,'messages','Latest 200 accepted messages',('sender','recipient','message_id','sequence','text')),(14,'requests','Latest 200 HTTP responses',('method','path','status'))]:
            box = ttk.LabelFrame(frame,text=title,padding=4)
            box.grid(row=row,column=0,columnspan=2,sticky='nsew',pady=6)
            frame.rowconfigure(row,weight=1)
            box.rowconfigure(0,weight=1);box.columnconfigure(0,weight=1)
            tree = w[name] = ttk.Treeview(box,columns=columns,show='headings',height=5)
            for col in columns:
                tree.heading(col,text=col.replace('_',' ').title())
                tree.column(col,width=250 if col in ('text','message_id','path') else 100,stretch=True)
            tree.grid(row=0,column=0,sticky='nsew')
            vs=ttk.Scrollbar(box,orient='vertical',command=tree.yview);vs.grid(row=0,column=1,sticky='ns')
            hs=ttk.Scrollbar(box,orient='horizontal',command=tree.xview);hs.grid(row=1,column=0,sticky='ew')
            tree.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
        ttk.Label(frame,text='Selected message — exact text').grid(row=12,column=0,columnspan=2,sticky='w')
        detailbox=ttk.Frame(frame);detailbox.grid(row=13,column=0,columnspan=2,sticky='nsew')
        frame.rowconfigure(13,weight=1)
        detailbox.columnconfigure(0,weight=1);detailbox.rowconfigure(0,weight=1)
        w['message-detail']=tk.Text(detailbox,height=4,wrap='none',state='disabled')
        w['message-detail'].grid(row=0,column=0,sticky='nsew')
        vs=ttk.Scrollbar(detailbox,orient='vertical',command=w['message-detail'].yview);vs.grid(row=0,column=1,sticky='ns')
        hs=ttk.Scrollbar(detailbox,orient='horizontal',command=w['message-detail'].xview);hs.grid(row=1,column=0,sticky='ew')
        w['message-detail'].configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
        w['messages'].bind('<<TreeviewSelect>>',self.show_detail)
        self.build_users(users_panel)
        self.set_state('Stopped')
        self.after_id = root.after(50,self.poll)

    def build_users(self, parent):
        import tkinter as tk
        from tkinter import ttk
        w=self.widgets
        parent.columnconfigure(1,weight=1);parent.rowconfigure(2,weight=1)
        bar=ttk.Frame(parent,padding=5);bar.grid(row=0,column=0,columnspan=2,sticky='ew')
        ttk.Label(bar,text='Filter known users').pack(side='left')
        w['user-filter']=ttk.Entry(bar);w['user-filter'].pack(side='left',fill='x',expand=True,padx=6)
        w['user-filter'].bind('<KeyRelease>',lambda _:self.refresh() if self.state=='Running' else None)
        w['user-refresh']=ttk.Button(bar,text='Refresh',command=lambda:self.refresh() if self.state=='Running' else None)
        w['user-refresh'].pack(side='left')
        w['directory-status']=ttk.Label(bar,text='stopped');w['directory-status'].pack(side='left',padx=6)
        w['queue-notice']=ttk.Label(parent,text='Queued = accepted, awaiting recipient acknowledgment. Received = recipient-reported durable storage, not read confirmation. Offline client queues: unknown.',wraplength=950)
        w['queue-notice'].grid(row=1,column=0,columnspan=2,sticky='ew',padx=5,pady=5)
        w['presence-notice']=ttk.Label(parent,text='Online: recent client presence. A communicated Offline choice applies immediately; uncommunicated disconnections expire after 15 seconds.',wraplength=950)
        w['presence-notice'].grid(row=4,column=0,columnspan=2,sticky='ew',padx=5,pady=5)
        usersbox=ttk.Frame(parent,padding=5);usersbox.grid(row=2,column=0,sticky='nsew')
        usersbox.rowconfigure(0,weight=1);usersbox.columnconfigure(0,weight=1)
        tree=w['users']=ttk.Treeview(usersbox,columns=('username','presence'),show='headings',selectmode='browse',height=8)
        tree.heading('username',text='Username');tree.heading('presence',text='Status')
        tree.column('username',width=100);tree.column('presence',width=130)
        tree.grid(row=0,column=0,sticky='nsew')
        scroll=ttk.Scrollbar(usersbox,orient='vertical',command=tree.yview);scroll.grid(row=0,column=1,sticky='ns');tree.configure(yscrollcommand=scroll.set)
        tree.bind('<<TreeviewSelect>>',lambda _:self.refresh() if self.state=='Running' else None)
        right=ttk.Frame(parent,padding=5);right.grid(row=2,column=1,sticky='nsew');right.columnconfigure(0,weight=1);right.rowconfigure(1,weight=1)
        summary=ttk.Frame(right);summary.grid(row=0,column=0,sticky='ew')
        ttk.Label(summary,text='Selected user:').pack(side='left')
        w['selected-user']=ttk.Label(summary,text='');w['selected-user'].pack(side='left',padx=5)
        for name in ('sent','received','queued'):
            ttk.Label(summary,text=name.title()+':').pack(side='left',padx=(7,0))
            w['user-'+name+'-count']=ttk.Label(summary,text='0');w['user-'+name+'-count'].pack(side='left')
        tabs=w['activity-tabs']=ttk.Notebook(right);tabs.grid(row=1,column=0,sticky='nsew',pady=5)
        for name in ('sent','received','queued'):
            box=ttk.Frame(tabs);tabs.add(box,text=name.title());box.rowconfigure(0,weight=1);box.columnconfigure(0,weight=1)
            columns=('peer','message_id','sequence','state','text')
            tree=w['user-'+name]=ttk.Treeview(box,columns=columns,show='headings',height=8)
            for col in columns:
                tree.heading(col,text=col.replace('_',' ').title());tree.column(col,width=230 if col in ('message_id','text') else 100,stretch=True)
            tree.grid(row=0,column=0,sticky='nsew')
            vs=ttk.Scrollbar(box,orient='vertical',command=tree.yview);vs.grid(row=0,column=1,sticky='ns')
            hs=ttk.Scrollbar(box,orient='horizontal',command=tree.xview);hs.grid(row=1,column=0,sticky='ew')
            tree.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)
            tree.bind('<<TreeviewSelect>>',self.show_user_detail)
        tabs.bind('<<NotebookTabChanged>>',self.show_user_detail)
        box=ttk.LabelFrame(parent,text='Selected activity — exact message text',padding=5)
        box.grid(row=3,column=0,columnspan=2,sticky='nsew',padx=5,pady=5);parent.rowconfigure(3,weight=1)
        box.rowconfigure(0,weight=1);box.columnconfigure(0,weight=1)
        text=w['user-message-detail']=tk.Text(box,height=4,wrap='none',state='disabled');text.grid(row=0,column=0,sticky='nsew')
        vs=ttk.Scrollbar(box,orient='vertical',command=text.yview);vs.grid(row=0,column=1,sticky='ns')
        hs=ttk.Scrollbar(box,orient='horizontal',command=text.xview);hs.grid(row=1,column=0,sticky='ew')
        text.configure(yscrollcommand=vs.set,xscrollcommand=hs.set)

    def selected_username(self):
        selection=self.widgets['users'].selection()
        if selection and self.widgets['user-filter'].get().lower() in selection[0].lower():return selection[0]
        return None

    @staticmethod
    def replace_rows(tree, rows):
        desired=[(iid,tuple(str(value) for value in values)) for iid,values in rows]
        actual=[(iid,tree.item(iid,'values')) for iid in tree.get_children()]
        if desired==actual:return
        selection=tree.selection()
        for iid in tree.get_children():tree.delete(iid)
        for iid,values in rows:tree.insert('','end',iid=iid,values=values)
        if selection and tree.exists(selection[0]):tree.selection_set(selection[0])

    def render_users(self, data, selected):
        w=self.widgets;query=w['user-filter'].get().lower()
        users=[row for row in data['users'] if query in row['username'].lower()]
        self.replace_rows(w['users'],[(row['username'],(row['username'],'Online' if row['online'] else 'Offline')) for row in users])
        selected=selected if selected in {row['username'] for row in users} else None
        w['selected-user'].configure(text=selected or '')
        w['directory-status'].configure(text='current')
        for name in ('sent','received','queued'):
            messages=data['activity'][name] if selected else []
            w['user-'+name+'-count'].configure(text=str(len(messages)))
            self.replace_rows(w['user-'+name],[(m['sender']+':'+m['message_id'],
                (m['recipient'] if name=='sent' else m['sender'],m['message_id'],m['sequence'],m['state'],m['text'])) for m in messages])
        self.show_user_detail()

    def show_user_detail(self, event=None):
        w=self.widgets
        if 'user-message-detail' not in w:return
        tabs=w['activity-tabs'];current=tabs.select()
        name=tabs.tab(current,'text').lower() if current else 'sent'
        tree=w['user-'+name]
        if event is not None and event.widget not in (tabs,tree):return
        selected=tree.selection();body=tree.item(selected[0],'values')[4] if selected else ''
        text=w['user-message-detail'];text.configure(state='normal');text.delete('1.0','end');text.insert('1.0',body);text.configure(state='disabled')

    def set_state(self, state):
        self.state=state
        self.widgets['server-status'].configure(text=state)
        editable=state in ('Stopped','Error') and not self.closing
        for name in ('start-button','port-input','static-input'):
            self.widgets[name].configure(state='normal' if editable else 'disabled')
        for name in ('stop-button','open-browser','user-refresh'):
            self.widgets[name].configure(state='normal' if state=='Running' and not self.closing else 'disabled')

    def start(self):
        if self.state not in ('Stopped','Error') or self.closing:return
        self.widgets['error-message'].configure(text='')
        value=self.widgets['port-input'].get()
        try:
            valid_port = value.isascii() and value.isdecimal() and 0 <= int(value) <= 65535
        except ValueError:
            valid_port = False
        if not valid_port:
            self.widgets['error-message'].configure(text='Enter a decimal port from 0 to 65535.')
            self.set_state('Error');return
        static=Path(self.widgets['static-input'].get()).expanduser()
        if not (static/'index.html').is_file():
            self.widgets['error-message'].configure(text='Browser assets are missing. Run python3 scripts/build.py --target all, then select its dist directory.')
            self.set_state('Error');return
        self.clear_monitor()
        self.set_state('Starting')
        def worker():
            server=None
            try:
                server=Server(('127.0.0.1',int(value)),static)
                thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.05},daemon=True)
                thread.start()
                self.events.put(('started',server,thread))
            except Exception as exc:
                if server is not None:server.server_close()
                self.events.put(('error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def stop(self):
        if self.state!='Running':return
        self.set_state('Stopping')
        server,thread=self.server,self.thread
        def worker():
            try:
                server.shutdown()
                server.close_connections()
                server.server_close()
                thread.join(timeout=2)
                if thread.is_alive():raise RuntimeError('Server thread did not stop.')
                self.events.put(('stopped',))
            except Exception as exc:self.events.put(('stop-error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def open_browser(self):
        if self.state!='Running':return
        try:
            if not webbrowser.open(self.widgets['server-url'].cget('text')):
                raise RuntimeError('No browser could be opened. Open the displayed URL in your browser.')
        except Exception as exc:self.widgets['error-message'].configure(text=str(exc))

    def clear_monitor(self):
        for name in ('server-url','session-id'):
            self.widgets[name].configure(text='')
        for name in ('message-count','response-count','error-count'):
            self.widgets[name].configure(text='0')
        for name in ('messages','requests'):
            tree=self.widgets[name]
            for iid in tree.get_children():tree.delete(iid)
        self.last_messages=None;self.last_requests=None
        self.show_detail()
        self.widgets['user-filter'].delete(0,'end')
        for name in ('users','user-sent','user-received','user-queued'):
            tree=self.widgets[name]
            for iid in tree.get_children():tree.delete(iid)
        self.widgets['selected-user'].configure(text='')
        self.widgets['directory-status'].configure(text='stopped')
        for name in ('sent','received','queued'):self.widgets['user-'+name+'-count'].configure(text='0')
        self.show_user_detail()

    def show_detail(self, event=None):
        tree=self.widgets['messages'];selection=tree.selection()
        text=tree.item(selection[0],'values')[4] if selection else ''
        detail=self.widgets['message-detail'];detail.configure(state='normal')
        detail.delete('1.0','end');detail.insert('1.0',text);detail.configure(state='disabled')

    def refresh(self):
        selected=self.selected_username()
        data=self.server.snapshot(selected)
        self.render_users(data,selected)
        for name,key in [('message-count','message_count'),('response-count','responses'),('error-count','errors')]:
            self.widgets[name].configure(text=str(data[key]))
        messages=[tuple(row[k] for k in ('sender','recipient','message_id','sequence','text')) for row in data['messages']]
        if messages!=self.last_messages:
            tree=self.widgets['messages'];selected=tree.selection()
            for iid in tree.get_children():tree.delete(iid)
            for row in messages:tree.insert('', 'end',iid=row[0]+':'+row[2],values=row)
            if selected and tree.exists(selected[0]):tree.selection_set(selected[0])
            self.last_messages=messages;self.show_detail()
        if data['requests']!=self.last_requests:
            tree=self.widgets['requests']
            for iid in tree.get_children():tree.delete(iid)
            for row in data['requests']:tree.insert('','end',values=row)
            self.last_requests=data['requests']

    def poll(self):
        if self.destroyed:return
        try:
            while True:
                event=self.events.get_nowait()
                if event[0]=='started':
                    self.server,self.thread=event[1:]
                    self.widgets['server-url'].configure(text=f'http://127.0.0.1:{self.server.server_port}')
                    self.widgets['session-id'].configure(text=str(uuid.uuid4()))
                    self.set_state('Running')
                    if self.closing:self.stop()
                elif event[0]=='stopped':
                    self.server=None;self.thread=None;self.clear_monitor();self.set_state('Stopped')
                elif event[0]=='error':
                    self.widgets['error-message'].configure(text='Could not start server: '+event[1])
                    self.set_state('Error')
                elif event[0]=='stop-error':
                    self.widgets['error-message'].configure(text='Could not stop server: '+event[1])
                    # Keep ownership and allow another Stop; do not allow overlapping Start.
                    self.set_state('Running')
        except queue.Empty:pass
        if self.closing and self.state in ('Stopped','Error'):
            self.destroy();return
        if self.state=='Running':self.refresh()
        self.after_id = self.root.after(100,self.poll)

    def destroy(self):
        self.destroyed=True
        self.root.after_cancel(self.after_id)
        self.root.destroy()

    def close(self):
        if self.destroyed:return
        self.closing=True
        if self.state=='Running':self.stop()
        else:self.set_state(self.state)
        if self.state in ('Stopped','Error'):
            self.destroy()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--static-dir',default=str(ROOT/'generated/typescript-web/dist'))
    args=parser.parse_args()
    try:
        import tkinter as tk
        root=tk.Tk()
    except (ImportError, RuntimeError) as exc:
        print('Install python3-tk and use a working desktop display: '+str(exc),file=sys.stderr);return 2
    except Exception as exc:
        print('Could not open desktop display: '+str(exc),file=sys.stderr);return 2
    app=ServerApp(root,args.port,args.static_dir)
    signal.signal(signal.SIGINT,lambda *_:app.close())
    signal.signal(signal.SIGTERM,lambda *_:app.close())
    root.mainloop()
    return 0


if __name__=='__main__':sys.exit(main())
