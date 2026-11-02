"""Tk presentation for the production client; no network work runs on the UI thread."""
import queue
import threading
import tkinter as tk
from tkinter import ttk
from core import Client
from protocol import ClientError, origin
from storage import reset_files

class DesktopApp:
    def __init__(self, root, server_origin, state_dir, transport='online'):
        self.root, self.state_dir = root, state_dir
        self.server_origin = server_origin
        self.widgets = {}
        self.ready = False
        self.client = None
        self.closing = False
        self.resetting = False
        self.local_error = ''
        self.latest = None
        self.results = queue.Queue()
        root.title('Local Messenger - Python')
        root.geometry('1100x800')
        root.minsize(960,640)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.build()
        try:
            self.server_origin = origin(server_origin)
            self.client = Client(self.server_origin,state_dir,transport)
            self.render()
            self.ready = True
        except ClientError as exc:
            self.local_error = exc.code + ': ' + exc.message
            self.widgets['error-message'].configure(text=self.local_error)
            self.set_compose(False)
            self.widgets['login-button'].configure(state='disabled')
        self.root.after(80,self.poll)

    def add(self, key, widget):
        self.widgets[key] = widget
        return widget

    def build(self):
        w = self.widgets
        outer = ttk.Frame(self.root,padding=10)
        outer.pack(fill='both',expand=True)
        outer.columnconfigure(0,weight=1)
        outer.rowconfigure(4,weight=1)
        header = ttk.LabelFrame(outer,text='Session',padding=6)
        header.grid(row=0,column=0,sticky='ew')
        ttk.Label(header,text='Username').grid(row=0,column=0)
        self.add('username-input',ttk.Entry(header,width=24)).grid(row=0,column=1,padx=5)
        self.add('login-button',ttk.Button(header,text='Log in',command=self.login)).grid(row=0,column=2)
        self.add('current-user',ttk.Label(header,text='')).grid(row=0,column=3,padx=6)
        ttk.Label(header,text='Connection:').grid(row=0,column=4)
        self.add('connection-status',ttk.Label(header,text='unknown')).grid(row=0,column=5,padx=5)
        ttk.Label(header,text='Development transport').grid(row=1,column=0,pady=5)
        combo = self.add('transport-mode',ttk.Combobox(header,values=('online','offline'),state='readonly',width=12))
        combo.set('online')
        combo.grid(row=1,column=1,sticky='w')
        combo.bind('<<ComboboxSelected>>',self.change_mode)
        self.add('reset-button',ttk.Button(header,text='Reset local store',command=self.ask_reset)).grid(row=1,column=2,padx=6)
        ttk.Label(header,text='Presence report:').grid(row=1,column=3)
        self.add('presence-status',ttk.Label(header,text='unknown')).grid(row=1,column=4)
        ttk.Label(header,text='Reports selected mode to server; real network loss may delay server Offline status.').grid(row=2,column=0,columnspan=6,sticky='w')
        self.confirm_frame = ttk.Frame(header)
        ttk.Label(self.confirm_frame,text='Delete this local identity and all local messages?').pack(side='left')
        self.add('reset-confirm',ttk.Button(self.confirm_frame,text='Confirm reset',command=self.confirm_reset)).pack(side='left',padx=5)
        self.add('reset-cancel',ttk.Button(self.confirm_frame,text='Cancel',command=self.cancel_reset)).pack(side='left')
        self.add('error-message',ttk.Label(outer,text='',foreground='#a00000',wraplength=1000)).grid(row=1,column=0,sticky='ew',pady=3)
        middle = ttk.Frame(outer)
        middle.grid(row=2,column=0,sticky='nsew')
        middle.columnconfigure(1,weight=1)
        directory = ttk.LabelFrame(middle,text='Known recipients',padding=6)
        directory.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        self.add('user-filter',ttk.Entry(directory,width=28)).grid(row=0,column=0,sticky='ew')
        w['user-filter'].bind('<KeyRelease>',lambda event:self.render_directory())
        self.add('user-refresh',ttk.Button(directory,text='Refresh',command=self.refresh)).grid(row=0,column=1)
        tree = self.add('user-directory',ttk.Treeview(directory,columns=('username','presence'),show='headings',height=5,selectmode='browse'))
        tree.heading('username',text='Username')
        tree.heading('presence',text='Advisory presence')
        tree.column('username',width=110)
        tree.column('presence',width=145)
        tree.grid(row=1,column=0,columnspan=2,sticky='nsew')
        scroll = ttk.Scrollbar(directory,orient='vertical',command=tree.yview)
        scroll.grid(row=1,column=2,sticky='ns')
        tree.configure(yscrollcommand=scroll.set)
        tree.bind('<<TreeviewSelect>>',self.choose_recipient)
        self.add('directory-status',ttk.Label(directory,text='loading')).grid(row=2,column=0,sticky='w')
        compose = ttk.LabelFrame(middle,text='Compose',padding=6)
        compose.grid(row=0,column=1,sticky='nsew')
        compose.columnconfigure(1,weight=1)
        ttk.Label(compose,text='Recipient').grid(row=0,column=0,sticky='w')
        self.add('recipient-input',ttk.Entry(compose)).grid(row=0,column=1,columnspan=2,sticky='ew',padx=4)
        text = self.add('message-input',tk.Text(compose,height=6,width=48,wrap='word',undo=True))
        text.grid(row=1,column=0,columnspan=3,sticky='nsew',pady=4)
        scroll = ttk.Scrollbar(compose,orient='vertical',command=text.yview)
        scroll.grid(row=1,column=3,sticky='ns')
        text.configure(yscrollcommand=scroll.set)
        self.add('send-button',ttk.Button(compose,text='Send',command=self.send)).grid(row=2,column=0,sticky='w')
        ttk.Label(compose,text='Durable receipt report:').grid(row=2,column=1,sticky='e')
        self.add('receipt-status',ttk.Label(compose,text='unknown')).grid(row=2,column=2)
        note = ttk.Frame(outer)
        note.grid(row=3,column=0,sticky='ew',pady=5)
        ttk.Label(note,text='Accepted by server is not a delivery/read receipt. Received acknowledgments describe durable storage, not reading.').pack(anchor='w')
        self.feature_label = ttk.Label(note,text='',wraplength=1000)
        self.feature_label.pack(anchor='w')
        panels = ttk.Panedwindow(outer,orient='horizontal')
        panels.grid(row=4,column=0,sticky='nsew')
        for key, title, columns in (
            ('inbox','Inbox',('sender','text','sequence')),
            ('outbox','Outgoing',('recipient','text','state','error','local_order'))):
            frame = ttk.LabelFrame(panels,text=title,padding=4)
            frame.columnconfigure(0,weight=1)
            frame.rowconfigure(0,weight=1)
            frame.rowconfigure(2,weight=1)
            panels.add(frame,weight=1)
            tree = self.add(key,ttk.Treeview(frame,columns=columns,show='tree headings',height=7,selectmode='browse'))
            tree.heading('#0',text='Message ID')
            tree.column('#0',width=90,minwidth=60)
            for col in columns:
                tree.heading(col,text=col.replace('_',' ').title())
                tree.column(col,width=140 if col=='text' else 95,minwidth=60)
            tree.grid(row=0,column=0,sticky='nsew')
            sy = ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
            sy.grid(row=0,column=1,sticky='ns')
            sx = ttk.Scrollbar(frame,orient='horizontal',command=tree.xview)
            sx.grid(row=1,column=0,sticky='ew')
            tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
            detail = self.add(key+'-detail',tk.Text(frame,height=5,width=42,wrap='word',state='disabled'))
            detail.grid(row=2,column=0,sticky='nsew',pady=5)
            ds = ttk.Scrollbar(frame,orient='vertical',command=detail.yview)
            ds.grid(row=2,column=1,sticky='ns')
            detail.configure(yscrollcommand=ds.set)
            tree.bind('<<TreeviewSelect>>',lambda event,k=key:self.detail(k))
        self.set_compose(False)

    def set_compose(self, enabled):
        state = 'normal' if enabled else 'disabled'
        for key in ('recipient-input','message-input','send-button'):
            self.widgets[key].configure(state=state)

    def action(self, callback):
        if not self.client or self.resetting:
            return
        try:
            callback()
            self.local_error = ''
        except ClientError as exc:
            self.local_error = exc.code + ': ' + exc.message
        self.render()

    def login(self):
        self.action(lambda:self.client.login(self.widgets['username-input'].get()))

    def send(self):
        def operation():
            self.client.send(self.widgets['recipient-input'].get(),self.widgets['message-input'].get('1.0','end-1c'))
            self.widgets['message-input'].delete('1.0','end')
        self.action(operation)

    def change_mode(self,event=None):
        if self.client and not self.resetting:
            self.client.transport(self.widgets['transport-mode'].get())
            self.render()

    def refresh(self):
        if self.client and not self.resetting:
            self.client.refresh()

    def choose_recipient(self,event=None):
        selected = self.widgets['user-directory'].selection()
        if selected and self.client and not self.resetting:
            field = self.widgets['recipient-input']
            if str(field.cget('state')) != 'disabled':
                field.delete(0,'end')
                field.insert(0,selected[0])

    def update_tree(self,key,rows):
        tree = self.widgets[key]
        wanted = [row[0] for row in rows]
        for item in tree.get_children():
            if item not in wanted:
                tree.delete(item)
        for index,(iid,text,values) in enumerate(rows):
            if not tree.exists(iid):
                tree.insert('',index,iid=iid,text=text,values=values)
            else:
                # Updating in place preserves actual selection, focus and scroll.
                if tuple(str(v) for v in tree.item(iid,'values')) != tuple(str(v) for v in values):
                    tree.item(iid,text=text,values=values)
                tree.move(iid,'',index)

    def render_directory(self):
        snap = self.latest
        if not snap:
            self.update_tree('user-directory',[])
            return
        term = self.widgets['user-filter'].get().lower()
        rows = [(r['username'],'',(r['username'],'recently seen' if r['online'] else 'not recently seen'))
                for r in snap['users'] if r['username']!=snap['status']['username'] and term in r['username'].lower()]
        self.update_tree('user-directory',rows)

    def detail(self,key):
        selected = self.widgets[key].selection()
        text = ''
        if self.latest and selected:
            for row in self.latest[key]:
                iid = row['sender']+':'+row['message_id'] if key=='inbox' else row['message_id']
                if iid==selected[0]:
                    text = row['text']
                    break
        widget = self.widgets[key+'-detail']
        if widget.get('1.0','end-1c') != text:
            widget.configure(state='normal')
            widget.delete('1.0','end')
            widget.insert('1.0',text)
            widget.configure(state='disabled')

    def render(self):
        if not self.client or self.resetting:
            return
        try:
            snap = self.client.snapshot()
        except ClientError as exc:
            self.widgets['error-message'].configure(text=exc.code+': '+exc.message)
            return
        self.latest = snap
        s, w = snap['status'], self.widgets
        # Clear and render all data before making login controls available.
        self.update_tree('inbox',[(r['sender']+':'+r['message_id'],r['message_id'],(r['sender'],r['text'],r['sequence'])) for r in snap['inbox']])
        self.update_tree('outbox',[(r['message_id'],r['message_id'],(r['recipient'],r['text'],'accepted by server' if r['state']=='accepted' else r['state'],(r['error']['code']+': '+r['error']['message']) if r['error'] else '',r['local_order'])) for r in snap['outbox']])
        self.render_directory()
        self.detail('inbox')
        self.detail('outbox')
        w['current-user'].configure(text=s['username'] or '')
        for key in ('connection','presence','directory','receipt'):
            value = s['connection'] if key=='connection' else snap[key+'_status']
            w[key+'-status'].configure(text=value)
        w['transport-mode'].set(s['transport'])
        error = self.local_error or ((s['last_error']['code']+': '+s['last_error']['message']) if s['last_error'] else '')
        w['error-message'].configure(text=error)
        self.feature_label.configure(text=snap['feature_error'])
        self.set_compose(bool(s['username']) and not s['sync_paused'])
        if s['username']:
            w['username-input'].grid_remove()
            w['login-button'].grid_remove()
        else:
            w['username-input'].configure(state='normal')
            w['login-button'].configure(state='normal')
            w['username-input'].grid()
            w['login-button'].grid()

    def ask_reset(self):
        if not self.resetting:
            self.confirm_frame.grid(row=3,column=0,columnspan=6,sticky='w',pady=5)

    def cancel_reset(self):
        self.confirm_frame.grid_remove()

    def confirm_reset(self):
        if self.resetting:
            return
        self.cancel_reset()
        self.resetting, self.ready = True,False
        self.set_compose(False)
        self.widgets['login-button'].configure(state='disabled')
        self.widgets['username-input'].configure(state='disabled')
        self.widgets['transport-mode'].configure(state='disabled')
        self.widgets['reset-button'].configure(state='disabled')
        old = self.client
        self.client = None
        def work():
            try:
                if old:
                    old.shutdown()
                reset_files(self.state_dir)
                self.results.put(('reset',None))
            except Exception as exc:
                self.results.put(('reset',exc))
        threading.Thread(target=work,daemon=True).start()

    def complete_reset(self,error):
        if self.closing:
            self.root.destroy()
            return
        self.latest = None
        for key in ('inbox','outbox','user-directory'):
            self.update_tree(key,[])
        for key in ('inbox','outbox'):
            self.detail(key)
        for key in ('username-input','recipient-input','user-filter'):
            self.widgets[key].configure(state='normal')
            self.widgets[key].delete(0,'end')
        self.widgets['message-input'].configure(state='normal')
        self.widgets['message-input'].delete('1.0','end')
        self.widgets['transport-mode'].configure(state='readonly')
        self.widgets['reset-button'].configure(state='normal')
        self.local_error = ''
        self.resetting = False
        try:
            if error:
                raise error
            self.client = Client(self.server_origin,self.state_dir,'online')
            self.render()
            self.ready = True
        except Exception as exc:
            self.local_error = 'Reset failed: ' + str(exc)
            self.widgets['error-message'].configure(text=self.local_error)
            self.set_compose(False)
            self.widgets['login-button'].configure(state='disabled')

    def poll(self):
        try:
            while True:
                kind, result = self.results.get_nowait()
                if kind=='closed':
                    self.root.destroy()
                    return
                if kind=='reset':
                    self.complete_reset(result)
                    if self.closing:
                        return
        except queue.Empty:
            pass
        if not self.closing:
            self.render()
        self.root.after(80,self.poll)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.ready = False
        if self.resetting:
            return
        client = self.client
        self.client = None
        def work():
            try:
                if client:
                    client.shutdown()
            finally:
                self.results.put(('closed',None))
        threading.Thread(target=work,daemon=True).start()
