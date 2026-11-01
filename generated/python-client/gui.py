"""Tk presentation of the production client; widgets are also automation locators."""
import queue
import threading
import tkinter as tk
from tkinter import ttk
from client import Client
from protocol import ClientError

class DesktopApp:
    def __init__(self, root, server_origin, state_dir, transport='online'):
        self.root = root
        self.widgets = {}
        self.ready = False
        self.closing = False
        self.resetting = False
        self.reset_thread = None
        self.client = None
        self.form_error = ''
        self.last_snapshot = None
        self.completions = queue.Queue()
        root.title('Local Messenger - Python')
        root.geometry('1100x800')
        root.minsize(960, 640)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.build()
        try:
            self.client = Client(server_origin, state_dir, transport)
            self.render()
            self.ready = True
            self.client.start()
        except Exception as exc:
            self.form_error = self.describe(exc)
            self.widgets['error-message'].configure(text=self.form_error)
            self.set_composition(False)
            self.widgets['login-button'].configure(state='disabled')
        self.root.after(80, self.tick)

    @staticmethod
    def describe(exc):
        return (exc.code + ': ' + exc.message) if isinstance(exc, ClientError) else str(exc)

    def add(self, key, widget):
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
        self.add('username-input', ttk.Entry(self.login_frame, width=24)).pack(side='left', padx=5)
        self.add('login-button', ttk.Button(self.login_frame, text='Log in', command=self.login)).pack(side='left')
        self.identity_label = ttk.Label(header, text='   Current user: ')
        self.identity_label.pack(side='left')
        self.add('current-user', ttk.Label(header, text='')).pack(side='left')
        ttk.Label(header, text='   Connection: ').pack(side='left')
        self.add('connection-status', ttk.Label(header, text='unknown')).pack(side='left')
        toolbar = ttk.Frame(outer)
        toolbar.pack(fill='x', pady=6)
        ttk.Label(toolbar, text='Development transport').pack(side='left')
        combo = self.add('transport-mode', ttk.Combobox(toolbar, values=('online', 'offline'), state='readonly', width=10))
        combo.set('online')
        combo.pack(side='left', padx=6)
        combo.bind('<<ComboboxSelected>>', self.transport)
        self.add('reset-button', ttk.Button(toolbar, text='Reset local store', command=self.confirmation)).pack(side='left')
        self.confirm_frame = ttk.Frame(outer)
        ttk.Label(self.confirm_frame, text='Clear this identity and all local messages?').pack(side='left')
        self.add('reset-confirm', ttk.Button(self.confirm_frame, text='Confirm reset', command=self.reset)).pack(side='left', padx=5)
        self.add('reset-cancel', ttk.Button(self.confirm_frame, text='Cancel', command=self.cancel_reset)).pack(side='left')
        self.add('error-message', ttk.Label(outer, text='', foreground='#a32121', wraplength=1000)).pack(fill='x')
        directory = ttk.LabelFrame(outer, text='Known recipients — presence is advisory', padding=5)
        directory.pack(fill='x', pady=5)
        bar = ttk.Frame(directory)
        bar.pack(fill='x')
        ttk.Label(bar, text='Filter usernames').pack(side='left')
        entry = self.add('user-filter', ttk.Entry(bar, width=25))
        entry.pack(side='left', padx=5)
        entry.bind('<KeyRelease>', lambda event: self.render_directory())
        self.add('user-refresh', ttk.Button(bar, text='Refresh', command=self.refresh)).pack(side='left')
        ttk.Label(bar, text='  Directory: ').pack(side='left')
        self.add('directory-status', ttk.Label(bar, text='loading')).pack(side='left')
        ttk.Label(bar, text='  Durable receipt report: ').pack(side='left')
        self.add('receipt-status', ttk.Label(bar, text='unknown')).pack(side='left')
        tree = self.add('user-directory', ttk.Treeview(directory, columns=('username','presence'), show='headings', height=3))
        tree.heading('username', text='Username')
        tree.heading('presence', text='Recent presence')
        tree.pack(fill='x')
        tree.bind('<<TreeviewSelect>>', self.select_user)
        self.feature_label = ttk.Label(directory, text='', wraplength=1000)
        self.feature_label.pack(fill='x')
        compose = ttk.LabelFrame(outer, text='Compose', padding=5)
        compose.pack(fill='x')
        row = ttk.Frame(compose)
        row.pack(fill='x')
        ttk.Label(row, text='Recipient').pack(side='left')
        self.add('recipient-input', ttk.Entry(row)).pack(side='left', fill='x', expand=True, padx=5)
        self.add('send-button', ttk.Button(row, text='Send', command=self.send)).pack(side='right')
        self.add('message-input', tk.Text(compose, height=4, wrap='word')).pack(fill='x', pady=4)
        ttk.Label(outer, text='Accepted by server is not a delivery/read receipt. Receipt reporting confirms durable storage, not reading.').pack(fill='x', pady=4)
        panels = ttk.Panedwindow(outer, orient='horizontal')
        panels.pack(fill='both', expand=True)
        for key, title, columns in [('inbox', 'Inbox', ('sender','text','sequence')), ('outbox', 'Outgoing', ('recipient','text','state','error','local_order'))]:
            panel = ttk.LabelFrame(panels, text=title)
            panels.add(panel, weight=1)
            holder = ttk.Frame(panel)
            holder.pack(fill='both', expand=True)
            tree = self.add(key, ttk.Treeview(holder, columns=columns, height=7))
            tree.heading('#0', text='Message ID')
            tree.column('#0', width=110)
            for col in columns:
                tree.heading(col, text=col.replace('_', ' ').title())
                tree.column(col, width=140 if col in ('text','state','error') else 85)
            y = ttk.Scrollbar(holder, orient='vertical', command=tree.yview)
            x = ttk.Scrollbar(holder, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
            tree.grid(row=0, column=0, sticky='nsew')
            y.grid(row=0, column=1, sticky='ns')
            x.grid(row=1, column=0, sticky='ew')
            holder.rowconfigure(0, weight=1)
            holder.columnconfigure(0, weight=1)
            detail_frame = ttk.Frame(panel)
            detail_frame.pack(fill='both', expand=True)
            detail = self.add(key + '-detail', tk.Text(detail_frame, height=5, wrap='word', state='disabled'))
            scroll = ttk.Scrollbar(detail_frame, command=detail.yview)
            detail.configure(yscrollcommand=scroll.set)
            detail.pack(side='left', fill='both', expand=True)
            scroll.pack(side='right', fill='y')
            tree.bind('<<TreeviewSelect>>', lambda event, k=key: self.show_detail(k))

    def set_composition(self, enabled):
        for key in ('recipient-input','message-input','send-button'):
            self.widgets[key].configure(state='normal' if enabled else 'disabled')

    def action(self, operation):
        try:
            result = operation()
            self.form_error = ''
            self.render()
            return result
        except Exception as exc:
            self.form_error = self.describe(exc)
            self.widgets['error-message'].configure(text=self.form_error)
            return None

    def login(self):
        if self.client and not self.resetting:
            self.action(lambda: self.client.login(self.widgets['username-input'].get()))

    def send(self):
        if not self.client or not self.ready:
            return
        result = self.action(lambda: self.client.send(self.widgets['recipient-input'].get(), self.widgets['message-input'].get('1.0','end-1c')))
        if result is not None:
            self.widgets['message-input'].delete('1.0', 'end')

    def transport(self, event=None):
        if self.client and not self.resetting:
            self.action(lambda: self.client.transport(self.widgets['transport-mode'].get()))

    def refresh(self):
        if self.client and not self.resetting:
            self.client.wake.set()

    def confirmation(self):
        if not self.resetting:
            self.confirm_frame.pack(fill='x', before=self.widgets['error-message'])

    def cancel_reset(self):
        self.confirm_frame.pack_forget()

    def reset(self):
        if not self.client or self.resetting:
            return
        self.cancel_reset()
        self.resetting = True
        self.ready = False
        self.login_frame.pack_forget()
        self.set_composition(False)
        for key in ('login-button','username-input','reset-button','transport-mode'):
            self.widgets[key].configure(state='disabled')
        def work():
            try:
                self.client.reset()
                self.completions.put(None)
            except Exception as exc:
                self.completions.put(exc)
        self.reset_thread = threading.Thread(target=work, daemon=True)
        self.reset_thread.start()

    def sync_tree(self, tree, rows):
        wanted = {iid for iid, _, _ in rows}
        for iid in tree.get_children():
            if iid not in wanted:
                tree.delete(iid)
        for index, (iid, label, values) in enumerate(rows):
            if tree.exists(iid):
                # Updating in place preserves focus, scroll position and selection.
                current = tree.item(iid)
                if current['text'] != label or tuple(map(str, current['values'])) != tuple(map(str, values)):
                    tree.item(iid, text=label, values=values)
                if tree.index(iid) != index:
                    tree.move(iid, '', index)
            else:
                tree.insert('', 'end', iid=iid, text=label, values=values)

    def render_directory(self):
        if self.last_snapshot is None:
            return
        snap = self.last_snapshot
        query = self.widgets['user-filter'].get().lower()
        current = snap['status']['username']
        rows = [(u['username'], '', (u['username'], 'recently seen' if u['online'] else 'not recently seen')) for u in snap['users'] if u['username'] != current and query in u['username'].lower()]
        self.sync_tree(self.widgets['user-directory'], rows)

    def select_user(self, event=None):
        if not self.ready or not self.last_snapshot or not self.last_snapshot['status']['username']:
            return
        selected = self.widgets['user-directory'].selection()
        if selected:
            entry = self.widgets['recipient-input']
            if str(entry.cget('state')) != 'disabled':
                entry.delete(0, 'end')
                entry.insert(0, selected[0])

    def show_detail(self, key):
        selected = self.widgets[key].selection()
        text = ''
        if selected and self.last_snapshot:
            for row in self.last_snapshot[key]:
                iid = row['sender'] + ':' + row['message_id'] if key == 'inbox' else row['message_id']
                if iid == selected[0]:
                    text = row['text']
                    break
        widget = self.widgets[key + '-detail']
        if widget.get('1.0','end-1c') != text:
            widget.configure(state='normal')
            widget.delete('1.0','end')
            widget.insert('1.0', text)
            widget.configure(state='disabled')

    def render(self):
        if not self.client or self.resetting:
            return
        snap = self.client.snapshot()
        self.last_snapshot = snap
        status = snap['status']
        logged = status['username'] is not None
        self.widgets['current-user'].configure(text=status['username'] or '')
        self.widgets['connection-status'].configure(text=status['connection'])
        self.widgets['username-input'].configure(state='disabled' if logged else 'normal')
        self.widgets['login-button'].configure(state='disabled' if logged else 'normal')
        self.widgets['reset-button'].configure(state='normal')
        self.widgets['transport-mode'].configure(state='readonly')
        self.widgets['transport-mode'].set(status['transport'])
        self.set_composition(logged and not status['sync_paused'])
        error = status['last_error']
        self.widgets['error-message'].configure(text=self.form_error or ((error['code'] + ': ' + error['message']) if error else ''))
        for key in ('directory-status','receipt-status'):
            self.widgets[key].configure(text=snap[key.replace('-', '_')])
        self.feature_label.configure(text=snap['feature_error'])
        self.sync_tree(self.widgets['inbox'], [(r['sender'] + ':' + r['message_id'], r['message_id'], (r['sender'],r['text'],r['sequence'])) for r in snap['inbox']])
        self.sync_tree(self.widgets['outbox'], [(r['message_id'],r['message_id'],(r['recipient'],r['text'],'accepted by server' if r['state']=='accepted' else r['state'], (r['error']['code'] + ': ' + r['error']['message']) if r['error'] else '',r['local_order'])) for r in snap['outbox']])
        self.render_directory()
        self.show_detail('inbox')
        self.show_detail('outbox')
        # Expose login only after the complete durable snapshot is rendered.
        # Reset keeps this frame hidden until the worker has finished clearing
        # the store, so visible login always accompanies the cleared rows.
        if logged:
            self.login_frame.pack_forget()
        else:
            self.login_frame.pack(side='left', before=self.identity_label)

    def tick(self):
        if self.closing:
            return
        try:
            if self.resetting:
                try:
                    result = self.completions.get_nowait()
                except queue.Empty:
                    pass
                else:
                    self.resetting = False
                    self.form_error = '' if result is None else self.describe(result)
                    if result is None:
                        for key in ('username-input', 'recipient-input'):
                            self.widgets[key].configure(state='normal')
                            self.widgets[key].delete(0,'end')
                        self.widgets['message-input'].configure(state='normal')
                        self.widgets['message-input'].delete('1.0','end')
                    self.render()
                    self.ready = result is None
            else:
                self.render()
        except Exception as exc:
            self.widgets['error-message'].configure(text=self.describe(exc))
        self.root.after(100, self.tick)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.ready = False
        try:
            if self.reset_thread and self.reset_thread.is_alive():
                self.client.http.cancel()
                self.reset_thread.join(5.5)
            if self.client:
                # Closing cancels the same bounded transport used by all routes.
                self.client.close()
        finally:
            self.root.destroy()
