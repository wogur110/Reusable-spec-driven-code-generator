"""One serialized production scheduler shared by desktop and machine clients."""
import threading
import sqlite3
from model import Store, ClientError, exact, require, integer, username, origin
from transport import request

class Client:
    def __init__(self, server, directory, transport='online', changed=None):
        self.server = origin(server)
        self.store = Store(directory, self.server)
        self.lock = threading.RLock()
        self.mode = transport
        self.connection = 'offline' if transport == 'offline' else 'unknown'
        self.last_error = None
        self.paused = False
        self.users = []
        self.directory_status = 'stale' if transport == 'offline' else 'loading'
        self.receipt_status = 'unknown'
        self.presence_status = 'unknown'
        self.mode_revision = 0
        self.intent = bool(self.store.meta()['username'] and transport == 'online')
        if self.intent:
            self.presence_status = 'pending'
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.changed = changed or (lambda: None)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def login(self, name):
        with self.lock:
            previous = self.store.meta()['username']
            result = self.store.login(name)
            if previous is None and self.mode == 'online':
                self.intent = True
                self.presence_status = 'pending'
            self.changed()
            self.wake.set()
            return result

    def send(self, recipient, text):
        with self.lock:
            if self.paused:
                raise ClientError('CURSOR_INVALID', 'Reset local state for the new server session.')
            result = self.store.enqueue(recipient, text)
            self.changed()
            self.wake.set()
            return result

    def status(self):
        with self.lock, self.store.lock:
            meta = self.store.meta()
            return {'username': meta['username'], 'transport': self.mode, 'connection': self.connection,
                    'cursor': meta['receive_cursor'], 'pending_count': sum(m['state'] == 'queued' for m in self.store.outgoing()),
                    'sync_paused': self.paused, 'last_error': self.last_error}

    def snapshot(self):
        with self.lock, self.store.lock:
            return dict(status=self.status(), inbox=self.store.incoming(), outbox=self.store.outgoing(),
                        users=list(self.users), directory_status=self.directory_status,
                        receipt_status=self.receipt_status, presence_status=self.presence_status)

    def transport(self, mode):
        if mode not in ('online', 'offline'):
            raise ClientError('INVALID_COMMAND', 'Transport must be online or offline.')
        with self.lock:
            if mode != self.mode:
                self.mode = mode
                self.mode_revision += 1
                self.intent = bool(self.store.meta()['username'])
                self.presence_status = 'pending' if self.intent else 'unknown'
                self.connection = 'offline' if mode == 'offline' else 'unknown'
                if mode == 'offline':
                    self.directory_status = 'stale'
                self.wake.set()
            return self.status()

    def refresh(self):
        self.wake.set()

    def active(self):
        with self.lock:
            return not self.stop.is_set() and not self.paused and self.mode == 'online'

    def report(self, error):
        with self.lock:
            self.last_error = error.data()
            self.connection = 'offline' if error.code == 'TRANSPORT_ERROR' or self.mode == 'offline' else 'error'

    def presence(self):
        with self.lock:
            if self.stop.is_set() or self.paused or not self.intent:
                return
            user = self.store.meta()['username']
            if user is None:
                return
            revision, online = self.mode_revision, self.mode == 'online'
            self.intent = False
            self.presence_status = 'pending'
        try:
            status, result = request(self.server, 'POST', '/api/v1/presence', {'username': user, 'online': online}, 2)
            exact(result, ('username', 'online'))
            require(status == 200 and result['username'] == user and type(result['online']) is bool and result['online'] == online)
            ok = True
        except ClientError:
            ok = False
        with self.lock:
            if not self.stop.is_set() and revision == self.mode_revision:
                self.presence_status = 'confirmed' if ok else 'error'
                # Online failures retry once at the start of the next ordinary cycle.

    def boundary(self):
        # Process the latest intent before any ordinary request. Mode changes in a
        # control request are coalesced and dispatched serially, never overlapped.
        while True:
            with self.lock:
                pending = self.intent and not self.stop.is_set() and not self.paused
            if not pending:
                break
            self.presence()
        return self.active()

    def cycle(self, user):
        errors = []
        if not self.boundary():
            return
        queued = [m for m in self.store.outgoing() if m['state'] == 'queued']
        if queued:
            row = queued[0]
            try:
                payload = {k: row[k] for k in ('message_id', 'sender', 'recipient', 'text')}
                status, receipt = request(self.server, 'POST', '/api/v1/messages', payload)
                exact(receipt, ('message_id', 'sender', 'recipient', 'sequence'))
                require(all(receipt[k] == payload[k] for k in ('message_id', 'sender', 'recipient')) and integer(receipt['sequence'], 1))
                if not self.stop.is_set():
                    self.store.outcome(row['message_id'], 'accepted', int(receipt['sequence']))
                    self.changed()
            except ClientError as e:
                errors.append(e)
                if not self.stop.is_set():
                    try:
                        self.store.outcome(row['message_id'], 'failed' if e.permanent else 'queued', error=e)
                        self.changed()
                    except ClientError as write_error:
                        errors.append(write_error)
        if not self.boundary():
            if errors:
                self.report(errors[-1])
            return
        after = self.store.meta()['receive_cursor']
        try:
            status, page = request(self.server, 'GET', '/api/v1/messages?recipient=' + user + '&after=' + str(after))
            require(status == 200)
            if not self.stop.is_set():
                updated = self.store.receive(page, user, after)
                if updated:
                    with self.lock:
                        self.receipt_status = 'pending'
                    self.changed()
        except ClientError as e:
            errors.append(e)
            if e.code == 'CURSOR_INVALID':
                with self.lock:
                    self.paused = True
        if self.stop.is_set():
            return
        with self.lock:
            if errors:
                self.report(errors[-1])
            elif self.mode == 'online':
                self.connection = 'online'
                self.last_error = None
        if not self.boundary():
            return
        through = self.store.meta()['receive_cursor']
        try:
            status, result = request(self.server, 'POST', '/api/v1/receipts', {'recipient': user, 'through': through}, 2)
            exact(result, ('recipient', 'through'))
            require(status == 200 and result['recipient'] == user and integer(result['through']) and result['through'] >= through)
            with self.lock:
                if not self.stop.is_set():
                    self.receipt_status = 'confirmed'
        except ClientError:
            with self.lock:
                self.receipt_status = 'error'
        if not self.boundary():
            return
        announcement_error = None
        try:
            status, result = request(self.server, 'POST', '/api/v1/users', {'username': user}, 2)
            exact(result, ('username',))
            require(status == 200 and result['username'] == user)
        except ClientError as e:
            announcement_error = e
        if not self.boundary():
            return
        directory_error = None
        revision = self.mode_revision
        try:
            status, result = request(self.server, 'GET', '/api/v1/users', timeout=2)
            exact(result, ('users',))
            require(status == 200 and isinstance(result['users'], list))
            previous = ''
            for row in result['users']:
                exact(row, ('username', 'online'))
                require(username(row['username']) and type(row['online']) is bool and row['username'] > previous)
                previous = row['username']
            with self.lock:
                if not self.stop.is_set():
                    self.users = result['users']
        except ClientError as e:
            directory_error = e
        with self.lock:
            if self.mode != 'online' or revision != self.mode_revision:
                self.directory_status = 'stale'
            else:
                err = directory_error or announcement_error
                self.directory_status = ('stale' if err.code == 'TRANSPORT_ERROR' else 'error') if err else 'current'

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            try:
                with self.lock:
                    user = self.store.meta()['username']
                    if user and self.mode == 'online' and self.presence_status == 'error':
                        self.intent = True
                if user and not self.paused:
                    self.boundary()
                    if self.active():
                        self.cycle(user)
                    self.boundary()
            except (ClientError, sqlite3.Error) as e:
                self.report(e if isinstance(e, ClientError) else ClientError('STORAGE_UNAVAILABLE', str(e)))
            if not self.stop.is_set():
                self.wake.wait(1)

    def shutdown(self):
        self.stop.set()
        self.wake.set()
        if self.thread.is_alive():
            self.thread.join()
        self.store.close()
