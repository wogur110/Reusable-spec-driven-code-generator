"""Tk presentation; widget handlers use the same core as the machine interface."""
import tkinter as tk
from tkinter import ttk
from core import Client
from protocol import Failure
from storage import reset_files

class DesktopApp:
    def __init__(self, root, server_origin, state_dir, transport='online'):
        self.root = root
        self.server = server_origin
        self.directory = state_dir
        self.client = None
        self.ready = False
        self.closed = False
        self.form_error = ''
        self.widgets = {}
        self.row_text = {'inbox': {}, 'outbox': {}}
        self.root.title('Local Messenger - Python')
        self.root.geometry('1100x760')
        self.root.minsize(960, 640)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.build(transport)
        try:
            self.client = Client(server_origin, state_dir, transport)
            self.render()
            self.ready = True
            self.client.start()
        except Exception as e:
            self.show_error(e)
        self.timer = self.root.after(100, self.refresh)

    def add(self, key, widget):
        self.widgets[key] = widget
        return widget

    def build(self, transport):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill='both', expand=True)
        header = ttk.Frame(frame)
        header.pack(fill='x')
        ttk.Label(header, text='Username').pack(side='left')
        self.add('username-input', ttk.Entry(header, width=24)).pack(side='left', padx=6)
        self.add('login-button', ttk.Button(header, text='Log in', command=self.login)).pack(side='left')
        ttk.Label(header, text='Current user:').pack(side='left', padx=(18,4))
        self.add('current-user', ttk.Label(header, text='')).pack(side='left')
        ttk.Label(header, text='Connection:').pack(side='left', padx=(18,4))
        self.add('connection-status', ttk.Label(header, text='unknown')).pack(side='left')
        controls = ttk.Frame(frame)
        controls.pack(fill='x', pady=10)
        ttk.Label(controls, text='Development transport').pack(side='left')
        mode = self.add('transport-mode', ttk.Combobox(controls, values=('online','offline'), state='readonly', width=12))
        mode.set(transport)
        mode.pack(side='left', padx=8)
        mode.bind('<<ComboboxSelected>>', self.transport)
        self.add('reset-button', ttk.Button(controls, text='Reset local store', command=self.confirmation)).pack(side='left', padx=8)
        self.confirm_frame = ttk.Frame(frame)
        ttk.Label(self.confirm_frame, text='Clear this local identity and all its messages?').pack(side='left')
        self.add('reset-confirm', ttk.Button(self.confirm_frame, text='Confirm reset', command=self.reset)).pack(side='left', padx=8)
        self.add('reset-cancel', ttk.Button(self.confirm_frame, text='Cancel', command=self.cancel)).pack(side='left')
        self.add('error-message', ttk.Label(frame, text='', foreground='#a01818', wraplength=1000)).pack(fill='x', pady=4)
        compose = ttk.LabelFrame(frame, text='Compose', padding=8)
        compose.pack(fill='x', pady=6)
        ttk.Label(compose, text='Recipient').grid(row=0, column=0, sticky='w')
        self.add('recipient-input', ttk.Entry(compose)).grid(row=0, column=1, sticky='ew', padx=6)
        ttk.Label(compose, text='Text').grid(row=1, column=0, sticky='nw', pady=6)
        draft = self.add('message-input', tk.Text(compose, height=5, wrap='word', undo=True))
        draft.grid(row=1, column=1, sticky='nsew', padx=6, pady=6)
        scroll = ttk.Scrollbar(compose, orient='vertical', command=draft.yview)
        scroll.grid(row=1, column=2, sticky='ns')
        draft.configure(yscrollcommand=scroll.set)
        self.add('send-button', ttk.Button(compose, text='Send', command=self.send)).grid(row=2, column=1, sticky='e')
        compose.columnconfigure(1, weight=1)
        ttk.Label(frame, text='Accepted by server is not a delivery or read receipt. Select a row to read its exact text.').pack(anchor='w', pady=5)
        panels = ttk.Panedwindow(frame, orient='horizontal')
        panels.pack(fill='both', expand=True)
        for name, columns in [('inbox',('sender','text','sequence')), ('outbox',('recipient','text','state','error','local_order'))]:
            panel = ttk.LabelFrame(panels, text='Inbox' if name=='inbox' else 'Outgoing', padding=6)
            panels.add(panel, weight=1)
            tree = self.add(name, ttk.Treeview(panel, columns=columns, height=7, selectmode='browse'))
            tree.grid(row=0, column=0, sticky='nsew')
            tree.heading('#0', text='Message ID')
            tree.column('#0', width=100, minwidth=70)
            for col in columns:
                tree.heading(col, text=col.replace('_',' ').capitalize())
                tree.column(col, width=160 if col in ('text','error','state') else 85, minwidth=50)
            vertical = ttk.Scrollbar(panel, orient='vertical', command=tree.yview)
            horizontal = ttk.Scrollbar(panel, orient='horizontal', command=tree.xview)
            vertical.grid(row=0, column=1, sticky='ns')
            horizontal.grid(row=1, column=0, sticky='ew')
            tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
            ttk.Label(panel, text='Selected message text').grid(row=2, column=0, sticky='w', pady=(7,2))
            detail = self.add(name+'-detail', tk.Text(panel, height=5, wrap='word', state='disabled'))
            detail.grid(row=3, column=0, sticky='nsew')
            ds = ttk.Scrollbar(panel, orient='vertical', command=detail.yview)
            ds.grid(row=3, column=1, sticky='ns')
            detail.configure(yscrollcommand=ds.set)
            panel.columnconfigure(0, weight=1)
            panel.rowconfigure(0, weight=2)
            panel.rowconfigure(3, weight=1)
            tree.bind('<<TreeviewSelect>>', lambda event, n=name: self.detail(n))
        self.enable_composer(False)

    def enable_composer(self, enabled):
        for key in ('recipient-input','message-input','send-button'):
            self.widgets[key].configure(state='normal' if enabled else 'disabled')

    def show_error(self, error):
        self.form_error = (error.code + ': ' + error.message) if isinstance(error,Failure) else 'STORAGE_UNAVAILABLE: ' + str(error)
        self.widgets['error-message'].configure(text=self.form_error)

    def action(self, callback):
        try:
            if self.client is None:
                raise Failure('STORAGE_UNAVAILABLE', 'Store unavailable; explicitly reset or select a fresh store.')
            callback()
            self.form_error = ''
            self.render()
        except Exception as e:
            self.show_error(e)

    def login(self):
        self.action(lambda: self.client.login(self.widgets['username-input'].get()))

    def send(self):
        def submit():
            self.client.send(self.widgets['recipient-input'].get(), self.widgets['message-input'].get('1.0','end-1c'))
            self.widgets['message-input'].delete('1.0','end')
        self.action(submit)

    def transport(self, event=None):
        self.action(lambda: self.client.transport(self.widgets['transport-mode'].get()))

    def confirmation(self):
        self.confirm_frame.pack(fill='x', after=self.widgets['reset-button'].master, pady=4)

    def cancel(self):
        self.confirm_frame.pack_forget()

    def reset(self):
        self.cancel()
        try:
            self.ready = False
            if self.client:
                self.client.close()
                self.client = None
            reset_files(self.directory)
            self.client = Client(self.server, self.directory, 'online')
            self.form_error = ''
            self.widgets['transport-mode'].set('online')
            self.widgets['username-input'].configure(state='normal')
            self.widgets['username-input'].delete(0,'end')
            self.enable_composer(True)
            self.widgets['recipient-input'].delete(0,'end')
            self.widgets['message-input'].delete('1.0','end')
            self.render()
            self.ready = True
            self.client.start()
        except Exception as e:
            self.show_error(e)

    def detail(self, name):
        selected = self.widgets[name].selection()
        text = self.row_text[name].get(selected[0], '') if selected else ''
        widget = self.widgets[name+'-detail']
        if widget.get('1.0','end-1c') != text:
            widget.configure(state='normal')
            widget.delete('1.0','end')
            widget.insert('1.0',text)
            widget.configure(state='disabled')

    def render(self):
        if not self.client:
            return
        meta, incoming, outgoing = self.client.store.snapshot()
        status = self.client.status()
        self.widgets['current-user'].configure(text=meta['username'] or '')
        self.widgets['connection-status'].configure(text=status['connection'])
        self.widgets['username-input'].configure(state='disabled' if meta['username'] else 'normal')
        self.widgets['login-button'].configure(state='disabled' if meta['username'] else 'normal')
        self.enable_composer(bool(meta['username']) and not status['sync_paused'])
        error = status['last_error']
        self.widgets['error-message'].configure(text=self.form_error or (error['code']+': '+error['message'] if error else ''))
        for name, rows in [('inbox',incoming),('outbox',outgoing)]:
            tree = self.widgets[name]
            ids = set()
            for row in rows:
                key = row['sender']+':'+row['message_id'] if name=='inbox' else row['message_id']
                ids.add(key)
                self.row_text[name][key] = row['text']
                if name=='inbox':
                    values = (row['sender'],row['text'],row['sequence'])
                else:
                    e = row['error']
                    values = (row['recipient'],row['text'],'accepted by server' if row['state']=='accepted' else row['state'], e['code']+': '+e['message'] if e else '',row['local_order'])
                if tree.exists(key):
                    if tuple(map(str,tree.item(key,'values'))) != tuple(map(str,values)):
                        tree.item(key, text=row['message_id'], values=values)
                else:
                    tree.insert('', 'end', iid=key, text=row['message_id'], values=values)
            for key in tree.get_children():
                if key not in ids:
                    tree.delete(key)
                    self.row_text[name].pop(key,None)
            self.detail(name)

    def refresh(self):
        if self.closed:
            return
        try:
            self.render()
        except Exception as e:
            self.show_error(e)
        self.timer = self.root.after(100,self.refresh)

    def close(self):
        if self.closed:
            return
        self.closed = True
        if hasattr(self,'timer'):
            self.root.after_cancel(self.timer)
        try:
            if self.client:
                self.client.close()
        finally:
            self.root.destroy()
