"""Tk desktop presentation. All messaging uses the production Client core."""
import threading
import tkinter as tk
from tkinter import ttk
from core import Client
from model import ClientError, reset_files

class DesktopApp:
    def __init__(self, root, server_origin, state_dir, transport='online'):
        self.root, self.server, self.state_dir = root, server_origin, state_dir
        self.widgets = {}
        self.ready = False
        self.startup_failed = False
        self.client = None
        self.closing = False
        self.resetting = False
        self.form_error = ''
        self.last_snapshot = None
        self.root.title('Local Messenger - Python')
        self.root.geometry('1100x780')
        self.root.minsize(700, 540)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.build()
        try:
            self.client = Client(server_origin, state_dir, transport)
            self.render()
            self.ready = True
            self.client.start()
        except ClientError as e:
            self.startup_failed = True
            self.form_error = e.code + ': ' + e.message
            self.widgets['error-message'].configure(text=self.form_error)
            self.widgets['login-button'].configure(state='disabled')
            self.widgets['send-button'].configure(state='disabled')
        self.root.after(100, self.poll)

    def widget(self, key, widget):
        self.widgets[key] = widget
        return widget

    def build(self):
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer)
        header.pack(fill='x')
        self.login_frame = ttk.Frame(header)
        self.login_frame.pack(side='left')
        ttk.Label(self.login_frame, text='Username').pack(side='left')
        self.widget('username-input', ttk.Entry(self.login_frame, width=25)).pack(side='left', padx=5)
        self.widget('login-button', ttk.Button(self.login_frame, text='Log in', command=self.login)).pack(side='left')
        ttk.Label(header, text='Current user:').pack(side='left', padx=(12, 2))
        self.widget('current-user', ttk.Label(header, text='')).pack(side='left')
        ttk.Label(header, text='Connection:').pack(side='left', padx=(12, 2))
        self.widget('connection-status', ttk.Label(header, text='unknown')).pack(side='left')
        self.widget('reset-button', ttk.Button(header, text='Reset local store', command=self.ask_reset)).pack(side='right')
        self.confirm_frame = ttk.Frame(outer)
        ttk.Label(self.confirm_frame, text='Clear identity and all local messages?').pack(side='left')
        self.widget('reset-confirm', ttk.Button(self.confirm_frame, text='Confirm reset', command=self.confirm_reset)).pack(side='left')
        self.widget('reset-cancel', ttk.Button(self.confirm_frame, text='Cancel', command=self.cancel_reset)).pack(side='left')
        modes = ttk.Frame(outer)
        modes.pack(fill='x', pady=5)
        ttk.Label(modes, text='Development transport').pack(side='left')
        mode = self.widget('transport-mode', ttk.Combobox(modes, values=('online', 'offline'), state='readonly', width=10))
        mode.set('online')
        mode.pack(side='left', padx=6)
        mode.bind('<<ComboboxSelected>>', self.change_mode)
        for label, key in [('Presence report:', 'presence-status'), ('Directory:', 'directory-status'), ('Receipt report:', 'receipt-status')]:
            ttk.Label(modes, text=label).pack(side='left', padx=(10, 2))
            self.widget(key, ttk.Label(modes, text='unknown')).pack(side='left')
        ttk.Label(outer, text='Presence reports the selected mode to the server. Real network loss may delay server Offline status.').pack(anchor='w')
        self.widget('error-message', ttk.Label(outer, text='', foreground='#a02020', wraplength=1000)).pack(fill='x', pady=3)
        compose = ttk.Frame(outer)
        compose.pack(fill='x')
        directory = ttk.LabelFrame(compose, text='Known recipients (advisory presence)', padding=5)
        directory.pack(side='left', fill='both', padx=(0, 10))
        controls = ttk.Frame(directory)
        controls.pack(fill='x')
        filt = self.widget('user-filter', ttk.Entry(controls, width=20))
        filt.pack(side='left')
        filt.bind('<KeyRelease>', lambda e: self.render_directory())
        self.widget('user-refresh', ttk.Button(controls, text='Refresh', command=self.refresh)).pack(side='left')
        tree = self.widget('user-directory', ttk.Treeview(directory, columns=('username', 'presence'), show='headings', height=5))
        tree.heading('username', text='Username')
        tree.heading('presence', text='Presence')
        tree.column('username', width=110)
        tree.column('presence', width=130)
        tree.pack(fill='both', expand=True)
        tree.bind('<<TreeviewSelect>>', self.select_user)
        form = ttk.Frame(compose)
        form.pack(side='left', fill='both', expand=True)
        ttk.Label(form, text='Recipient').pack(anchor='w')
        self.widget('recipient-input', ttk.Entry(form)).pack(fill='x')
        ttk.Label(form, text='Message (Enter inserts a newline)').pack(anchor='w')
        self.widget('message-input', tk.Text(form, height=5, wrap='word')).pack(fill='both', expand=True)
        self.widget('send-button', ttk.Button(form, text='Send', command=self.send)).pack(anchor='e', pady=3)
        ttk.Label(outer, text='Accepted by server is not a delivery/read receipt. Receipt report confirms durable incoming storage, not reading.').pack(anchor='w', pady=5)
        histories = ttk.Panedwindow(outer, orient='horizontal')
        histories.pack(fill='both', expand=True)
        for key, title, columns in [('inbox', 'Inbox', ('sender', 'text', 'sequence')), ('outbox', 'Outgoing', ('recipient', 'text', 'state', 'error', 'local_order'))]:
            panel = ttk.LabelFrame(histories, text=title, padding=4)
            histories.add(panel, weight=1)
            rows = ttk.Frame(panel)
            rows.pack(fill='both', expand=True)
            rows.rowconfigure(0, weight=1)
            rows.columnconfigure(0, weight=1)
            table = self.widget(key, ttk.Treeview(rows, columns=columns, height=8, selectmode='browse'))
            table.heading('#0', text='Message ID')
            table.column('#0', width=130, stretch=False)
            for col in columns:
                table.heading(col, text=col.replace('_', ' ').title())
                table.column(col, width=160 if col in ('text', 'error') else 110, stretch=False)
            table.grid(row=0, column=0, sticky='nsew')
            sy = ttk.Scrollbar(rows, orient='vertical', command=table.yview)
            sx = ttk.Scrollbar(rows, orient='horizontal', command=table.xview)
            table.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
            sy.grid(row=0, column=1, sticky='ns')
            sx.grid(row=1, column=0, sticky='ew')
            detailframe = ttk.Frame(panel)
            detailframe.pack(fill='both', pady=(5, 0))
            detail = self.widget(key + '-detail', tk.Text(detailframe, height=6, wrap='word', state='disabled'))
            detail.pack(side='left', fill='both', expand=True)
            scroll = ttk.Scrollbar(detailframe, orient='vertical', command=detail.yview)
            scroll.pack(side='right', fill='y')
            detail.configure(yscrollcommand=scroll.set)
            table.bind('<<TreeviewSelect>>', lambda e, k=key: self.select_message(k))

    def operation(self, action):
        try:
            action()
            self.form_error = ''
        except Exception as e:
            self.form_error = (e.code + ': ' + e.message) if isinstance(e, ClientError) else 'STORAGE_UNAVAILABLE: ' + str(e)
        self.render()

    def login(self):
        if self.client and not self.resetting:
            self.operation(lambda: self.client.login(self.widgets['username-input'].get()))

    def send(self):
        if not self.client or self.resetting:
            return
        def action():
            self.client.send(self.widgets['recipient-input'].get(), self.widgets['message-input'].get('1.0', 'end-1c'))
            self.widgets['message-input'].delete('1.0', 'end')
        self.operation(action)

    def change_mode(self, event=None):
        if self.client and not self.resetting:
            self.operation(lambda: self.client.transport(self.widgets['transport-mode'].get()))

    def refresh(self):
        if self.client and not self.resetting:
            self.client.refresh()

    def ask_reset(self):
        if not self.resetting:
            self.confirm_frame.pack(fill='x', after=self.widgets['reset-button'].master)

    def cancel_reset(self):
        self.confirm_frame.pack_forget()

    def confirm_reset(self):
        if self.resetting or self.closing:
            return
        self.resetting = True
        self.ready = False
        self.cancel_reset()
        self.widgets['login-button'].configure(state='disabled')
        self.widgets['send-button'].configure(state='disabled')
        self.widgets['reset-button'].configure(state='disabled')
        self.widgets['username-input'].configure(state='disabled')
        old = self.client
        self.client = None
        self.reset_result = None
        def work():
            try:
                if old:
                    old.shutdown()
                reset_files(self.state_dir)
                replacement = Client(self.server, self.state_dir, 'online')
                self.reset_result = (replacement, None)
            except Exception as e:
                self.reset_result = (None, e)
        threading.Thread(target=work, daemon=True).start()
        self.root.after(30, self.finish_reset)

    def finish_reset(self):
        if self.closing:
            return
        if self.reset_result is None:
            self.root.after(30, self.finish_reset)
            return
        self.client, error = self.reset_result
        self.clear_rendered()
        self.resetting = False
        self.widgets['reset-button'].configure(state='normal')
        self.form_error = '' if error is None else 'STORAGE_UNAVAILABLE: ' + str(error)
        if self.client:
            self.render()
            self.ready = True
            self.client.start()
        else:
            self.widgets['error-message'].configure(text=self.form_error)

    def clear_rendered(self):
        self.last_snapshot = None
        for key in ('inbox', 'outbox', 'user-directory'):
            tree = self.widgets[key]
            for iid in tree.get_children():
                tree.delete(iid)
        for key in ('inbox-detail', 'outbox-detail'):
            self.set_detail(key, '')
        for key in ('username-input', 'recipient-input', 'user-filter'):
            self.widgets[key].configure(state='normal')
            self.widgets[key].delete(0, 'end')
        self.widgets['message-input'].configure(state='normal')
        self.widgets['message-input'].delete('1.0', 'end')

    def set_detail(self, key, text):
        w = self.widgets[key]
        if w.get('1.0', 'end-1c') != text:
            w.configure(state='normal')
            w.delete('1.0', 'end')
            w.insert('1.0', text)
            w.configure(state='disabled')

    def select_message(self, key):
        tree = self.widgets[key]
        selected = tree.selection()
        text = ''
        if selected and self.last_snapshot:
            for row in self.last_snapshot[key]:
                iid = row['sender'] + ':' + row['message_id'] if key == 'inbox' else row['message_id']
                if iid == selected[0]:
                    text = row['text']
                    break
        self.set_detail(key + '-detail', text)

    def select_user(self, event=None):
        selected = self.widgets['user-directory'].selection()
        if selected and self.client and not self.resetting:
            entry = self.widgets['recipient-input']
            entry.delete(0, 'end')
            entry.insert(0, selected[0])

    def reconcile_tree(self, tree, rows):
        wanted = {iid for iid, text, values in rows}
        for iid in tree.get_children():
            if iid not in wanted:
                tree.delete(iid)
        for index, (iid, text, values) in enumerate(rows):
            if tree.exists(iid):
                # Avoid repeated item writes and selection events while editing.
                if tuple(str(x) for x in tree.item(iid, 'values')) != tuple(str(x) for x in values):
                    tree.item(iid, text=text, values=values)
            else:
                tree.insert('', 'end', iid=iid, text=text, values=values)
            tree.move(iid, '', index)

    def render_directory(self):
        if not self.last_snapshot:
            return
        s = self.last_snapshot
        query = self.widgets['user-filter'].get().lower()
        rows = [(u['username'], '', (u['username'], 'recently seen' if u['online'] else 'not recently seen')) for u in s['users'] if u['username'] != s['status']['username'] and query in u['username'].lower()]
        self.reconcile_tree(self.widgets['user-directory'], rows)

    def render(self):
        if not self.client or self.resetting or self.closing:
            return
        try:
            snap = self.client.snapshot()
        except Exception as e:
            self.widgets['error-message'].configure(text='STORAGE_UNAVAILABLE: ' + str(e))
            return
        self.last_snapshot = snap
        status = snap['status']
        # Reconcile all rows before exposing login after a reset.
        for key in ('inbox', 'outbox'):
            rows = []
            for row in snap[key]:
                if key == 'inbox':
                    iid = row['sender'] + ':' + row['message_id']
                    values = (row['sender'], row['text'], row['sequence'])
                else:
                    iid = row['message_id']
                    err = row['error']
                    values = (row['recipient'], row['text'], 'accepted by server' if row['state'] == 'accepted' else row['state'], (err['code'] + ': ' + err['message']) if err else '', row['local_order'])
                rows.append((iid, row['message_id'], values))
            self.reconcile_tree(self.widgets[key], rows)
            self.select_message(key)
        self.render_directory()
        self.widgets['current-user'].configure(text=status['username'] or '')
        self.widgets['connection-status'].configure(text=status['connection'])
        for key in ('directory', 'receipt', 'presence'):
            self.widgets[key + '-status'].configure(text=snap[key + '_status'])
        self.widgets['transport-mode'].set(status['transport'])
        error = status['last_error']
        self.widgets['error-message'].configure(text=self.form_error or (error['code'] + ': ' + error['message'] if error else ''))
        enabled = bool(status['username']) and not status['sync_paused']
        for key in ('recipient-input', 'message-input', 'send-button'):
            self.widgets[key].configure(state='normal' if enabled else 'disabled')
        if status['username']:
            self.login_frame.pack_forget()
        else:
            if not self.login_frame.winfo_manager():
                self.login_frame.pack(side='left', before=self.widgets['current-user'].master.winfo_children()[1])
            self.widgets['username-input'].configure(state='normal')
            self.widgets['login-button'].configure(state='normal')

    def poll(self):
        if self.closing:
            return
        if not self.resetting:
            self.render()
        self.root.after(100, self.poll)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.ready = False
        if self.client:
            self.client.shutdown()
            self.client = None
        if self.resetting:
            # A reset owns at most one bounded request; do not abandon its store.
            import time
            while self.reset_result is None:
                time.sleep(0.01)
            if self.reset_result[0]:
                self.reset_result[0].shutdown()
        self.root.destroy()
