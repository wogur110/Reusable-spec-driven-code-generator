"""Production messaging operations shared by desktop and JSON-lines frontends."""
import threading
from urllib.parse import urlencode
from protocol import (ClientError, Transport, exact, integer, username, message_id,
                      text_valid, require, wire_error, origin)
from storage import Store

class Client:
    def __init__(self, server, directory, transport='online', changed=None):
        self.server = origin(server)
        self.store = Store(directory, self.server)
        self.lock = self.store.lock
        self.http = Transport(self.server)
        self.mode = transport
        self.connection = 'offline' if transport == 'offline' else 'unknown'
        self.last_error = None
        self.paused = False
        self.users = []
        self.directory_status = 'stale' if transport == 'offline' else 'loading'
        self.receipt_status = 'unknown'
        self.feature_error = ''
        self.generation = 0
        self.revision = 0
        self.changed = changed
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.thread = None

    def notify(self):
        self.revision += 1
        if self.changed:
            self.changed(self.revision)

    def start(self):
        self.stop.clear()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def status(self):
        with self.lock:
            m, _, rows = self.store.snapshot()
            return {'username': m['username'], 'transport': self.mode, 'connection': self.connection,
                    'cursor': m['receive_cursor'], 'pending_count': sum(r['state'] == 'queued' for r in rows),
                    'sync_paused': self.paused, 'last_error': self.last_error}

    def snapshot(self):
        with self.lock:
            _, inbox, outbox = self.store.snapshot()
            return {'status': self.status(), 'inbox': inbox, 'outbox': outbox,
                    'users': list(self.users), 'directory_status': self.directory_status,
                    'receipt_status': self.receipt_status, 'feature_error': self.feature_error}

    def login(self, name):
        with self.lock:
            result = self.store.login(name)
            self.notify()
        self.wake.set()
        return result

    def send(self, recipient, text):
        with self.lock:
            if self.paused:
                raise ClientError('CURSOR_INVALID', 'Reset the local store for this server session before sending.')
            result = self.store.enqueue(recipient, text)
            self.notify()
        self.wake.set()
        return result

    def transport(self, mode):
        if mode not in ('online', 'offline'):
            raise ClientError('INVALID_COMMAND', 'Transport must be online or offline.')
        with self.lock:
            self.mode = mode
            self.connection = 'offline' if mode == 'offline' else ('error' if self.paused else 'unknown')
            if mode == 'offline':
                self.directory_status = 'stale'
        self.wake.set()
        return self.status()

    def valid(self, gen):
        return not self.stop.is_set() and self.generation == gen

    def allowed(self, gen):
        return self.valid(gen) and self.mode == 'online' and not self.paused

    def request(self, gen, method, path, data=None, timeout=5):
        with self.lock:
            if not self.allowed(gen):
                raise ClientError('CANCELED', 'Request canceled.')
        return self.http.request(method, path, data, timeout)

    def send_one(self, gen, row):
        payload = {k: row[k] for k in ('message_id', 'sender', 'recipient', 'text')}
        state, sequence, error = 'queued', None, None
        try:
            status, data = self.request(gen, 'POST', '/api/v1/messages', payload)
            if status in (200, 201):
                require(exact(data, 'message_id sender recipient sequence'))
                require(all(data[k] == payload[k] for k in ('message_id', 'sender', 'recipient')) and integer(data['sequence'], 1))
                state, sequence = 'accepted', int(data['sequence'])
            elif 400 <= status < 600:
                error = wire_error(status, data)
                if 400 <= status < 500 and status not in (408, 429):
                    state = 'failed'
            else:
                error = ClientError('PROTOCOL_ERROR', 'Unexpected HTTP status or redirect; acceptance is uncertain.')
        except ClientError as exc:
            error = exc
        with self.lock:
            if not self.valid(gen) or (error and error.code == 'CANCELED'):
                return None
            self.store.outcome(row['message_id'], state, sequence, error)
            self.notify()
        return error

    def receive(self, gen, name, after):
        status, data = self.request(gen, 'GET', '/api/v1/messages?' + urlencode({'recipient': name, 'after': after}))
        if status != 200:
            error = wire_error(status, data)
            if error.code == 'CURSOR_INVALID' and data['error']['field'] == 'after':
                with self.lock:
                    if self.valid(gen):
                        self.paused = True
            raise error
        require(exact(data, 'messages next_after'))
        require(isinstance(data['messages'], list) and len(data['messages']) <= 100)
        require(integer(data['next_after']))
        keys = set()
        for i, msg in enumerate(data['messages'], after + 1):
            require(exact(msg, 'message_id sender recipient text sequence'))
            require(message_id(msg['message_id']) and username(msg['sender']) and username(msg['recipient']))
            require(msg['recipient'] == name and msg['sender'] != name and text_valid(msg['text']))
            require(integer(msg['sequence'], 1) and msg['sequence'] == i)
            key = (msg['sender'], msg['message_id'])
            require(key not in keys)
            keys.add(key)
        require(data['next_after'] == after + len(data['messages']))
        with self.lock:
            if self.valid(gen):
                self.store.receive(data['messages'], after, int(data['next_after']))
                if data['messages']:
                    self.receipt_status = 'pending'
                    self.notify()

    def auxiliaries(self, gen, name):
        with self.lock:
            if not self.allowed(gen):
                return
            cursor = self.store.meta()['receive_cursor']
        try:
            status, data = self.request(gen, 'POST', '/api/v1/receipts', {'recipient': name, 'through': cursor}, 2)
            if status != 200:
                raise wire_error(status, data)
            require(exact(data, 'recipient through') and data['recipient'] == name and integer(data['through']) and data['through'] >= cursor)
            with self.lock:
                if self.valid(gen):
                    self.receipt_status = 'confirmed'
        except ClientError as exc:
            with self.lock:
                if self.valid(gen) and exc.code != 'CANCELED':
                    self.receipt_status = 'error'
                    self.feature_error = 'Receipt report: ' + exc.message
        announce_error = None
        try:
            status, data = self.request(gen, 'POST', '/api/v1/users', {'username': name}, 2)
            if status != 200:
                raise wire_error(status, data)
            require(exact(data, 'username') and data['username'] == name)
        except ClientError as exc:
            announce_error = exc
        try:
            status, data = self.request(gen, 'GET', '/api/v1/users', timeout=2)
            if status != 200:
                raise wire_error(status, data)
            require(exact(data, 'users') and isinstance(data['users'], list))
            previous = ''
            for user in data['users']:
                require(exact(user, 'username online') and username(user['username']) and type(user['online']) is bool)
                require(user['username'] > previous)
                previous = user['username']
            with self.lock:
                if self.valid(gen):
                    self.users = data['users']
            if announce_error:
                raise announce_error
            with self.lock:
                if self.valid(gen):
                    self.directory_status = 'current' if self.mode == 'online' else 'stale'
                    if self.receipt_status != 'error':
                        self.feature_error = ''
        except ClientError as exc:
            with self.lock:
                if self.valid(gen):
                    self.directory_status = 'stale' if self.mode == 'offline' or exc.code in ('TRANSPORT_ERROR', 'CANCELED') else 'error'
                    if exc.code != 'CANCELED':
                        self.feature_error = 'Directory: ' + exc.message

    def cycle(self):
        with self.lock:
            gen = self.generation
            if not self.allowed(gen):
                return
            meta, _, rows = self.store.snapshot()
            name = meta['username']
            if name is None:
                return
            head = next((r for r in rows if r['state'] == 'queued'), None)
        errors = []
        if head:
            try:
                error = self.send_one(gen, head)
                if error:
                    errors.append(error)
            except ClientError as exc:
                errors.append(exc)
        if self.allowed(gen):
            try:
                self.receive(gen, name, self.store.meta()['receive_cursor'])
            except ClientError as exc:
                if exc.code != 'CANCELED':
                    errors.append(exc)
        with self.lock:
            if not self.valid(gen):
                return
            if self.paused:
                error = ClientError('CURSOR_INVALID', 'Server cursor is invalid. Explicitly reset the local store for this server session.')
            else:
                error = next((e for e in errors if e.code == 'STORAGE_UNAVAILABLE'), errors[0] if errors else None)
            self.last_error = error.data() if error else None
            self.connection = ('offline' if self.mode == 'offline' else
                               ('offline' if error and error.code == 'TRANSPORT_ERROR' else 'error' if error else 'online'))
        if self.allowed(gen):
            self.auxiliaries(gen, name)

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            try:
                self.cycle()
            except Exception as exc:
                with self.lock:
                    error = exc if isinstance(exc, ClientError) else ClientError('STORAGE_UNAVAILABLE', str(exc))
                    self.last_error = error.data()
                    self.connection = 'error'
            if not self.stop.is_set():
                self.wake.wait(1)

    def halt(self):
        with self.lock:
            self.generation += 1
            self.stop.set()
            self.wake.set()
        self.http.cancel()
        if self.thread:
            self.thread.join(5.5)
        if self.thread and self.thread.is_alive():
            raise ClientError('TRANSPORT_ERROR', 'Worker has not stopped; state was preserved.')

    def reset(self):
        self.halt()
        with self.lock:
            self.store.reset()
            self.users = []
            self.mode, self.connection, self.paused = 'online', 'unknown', False
            self.last_error, self.feature_error = None, ''
            self.directory_status, self.receipt_status = 'loading', 'unknown'
            self.notify()
        self.start()

    def close(self):
        self.halt()
        self.store.close()
