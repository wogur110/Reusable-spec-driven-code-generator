"""Production client operations and one serialized synchronization worker."""
import threading
from urllib.parse import urlencode
from protocol import ClientError, request, receipt, page, server_error

class Client:
    def __init__(self, store, server, mode, changed):
        self.store, self.server, self.changed = store, server, changed
        self.guard = threading.RLock()
        self.mode = mode
        self.connection = 'offline' if mode == 'offline' else 'unknown'
        self.last_error = None
        self.paused = False
        self.notify_error = lambda error: None
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.thread = threading.Thread(target=self.run, name='synchronizer', daemon=True)

    def status(self):
        with self.guard:
            meta, outgoing, _ = self.store.snapshot()
            return {'username': meta['username'], 'transport': self.mode,
                    'connection': self.connection, 'cursor': meta['receive_cursor'],
                    'pending_count': sum(r['state'] == 'queued' for r in outgoing),
                    'sync_paused': self.paused, 'last_error': self.last_error}

    def observe_error(self, exc):
        with self.guard:
            if self.paused and exc.code != 'CURSOR_INVALID':
                return
            self.last_error = exc.data()
            self.connection = ('offline' if exc.code == 'TRANSPORT_ERROR' else
                               'error' if exc.code in ('PROTOCOL_ERROR', 'STORAGE_UNAVAILABLE', 'CURSOR_INVALID') else 'online')
            if exc.code == 'CURSOR_INVALID':
                self.paused = True
                self.last_error = {'code': exc.code, 'message': 'Server cursor is invalid. Stop and explicitly reset the local store for this server session.'}
            self.notify_error(self.last_error)

    def operate(self, command, args):
        try:
            if command == 'login':
                if self.store.login(args['username']):
                    self.changed()
                    self.wake.set()
                return {'username': args['username']}
            if command == 'send':
                with self.guard:
                    if self.paused:
                        raise ClientError('CURSOR_INVALID', 'Explicitly reset the stopped client store before sending.')
                    result = self.store.enqueue(args['recipient'], args['text'])
                self.changed()
                return result
            if command in ('inbox', 'outbox'):
                _, outgoing, incoming = self.store.snapshot()
                return {'messages': incoming if command == 'inbox' else outgoing}
            if command == 'status':
                return self.status()
            if command == 'transport':
                if args['mode'] not in ('online', 'offline'):
                    raise ClientError('INVALID_COMMAND', 'Transport must be online or offline.')
                with self.guard:
                    self.mode = args['mode']
                    if self.mode == 'offline' and not self.paused:
                        self.connection = 'offline'
                    if self.mode == 'online':
                        self.wake.set()
                return self.status()
            if command == 'quit':
                self.stop.set()
                self.wake.set()
                return {}
            raise ClientError('INVALID_COMMAND', 'Unknown command.')
        except ClientError as exc:
            if exc.code == 'STORAGE_UNAVAILABLE':
                self.observe_error(exc)
            raise

    def active(self):
        with self.guard:
            return not self.stop.is_set() and self.mode == 'online' and not self.paused

    def exchange(self, method, path, payload=None):
        if not self.active():
            raise ClientError('TRANSPORT_ERROR', 'Transport is offline; switch online to synchronize.')
        return request(self.server, method, path, payload)

    def send_one(self, row):
        payload = {key: row[key] for key in ('message_id', 'sender', 'recipient', 'text')}
        error = None
        state, sequence = 'queued', None
        try:
            status, value = self.exchange('POST', '/api/v1/messages', payload)
            if status in (200, 201):
                sequence = receipt(value, payload)
                state = 'accepted'
            elif 400 <= status < 500 and status not in (408, 429):
                state = 'failed'
                error = server_error(status, value)
            elif status in (408, 429) or 500 <= status < 600:
                error = server_error(status, value)
            else:
                error = ClientError('PROTOCOL_ERROR', 'Unexpected HTTP response; retrying the original message ID.')
        except ClientError as exc:
            error = exc
        self.store.outcome(row['message_id'], state, sequence, error)
        self.changed()
        return error

    def receive_one(self):
        meta = self.store.metadata()
        who, after = meta['username'], meta['receive_cursor']
        status, value = self.exchange('GET', '/api/v1/messages?' + urlencode({'recipient': who, 'after': after}))
        if status != 200:
            raise server_error(status, value) if 400 <= status < 600 else ClientError('PROTOCOL_ERROR', 'Unexpected receive HTTP response.')
        rows, next_after = page(value, who, after)
        self.store.receive(rows, after, next_after)
        if rows:
            self.changed()

    def cycle(self):
        meta, outgoing, _ = self.store.snapshot()
        if meta['username'] is None or not self.active():
            return
        error = None
        head = next((row for row in outgoing if row['state'] == 'queued'), None)
        if head:
            try:
                error = self.send_one(head)
            except ClientError as exc:
                error = exc
        if self.active():
            try:
                self.receive_one()
            except ClientError as exc:
                if error is None or exc.code in ('CURSOR_INVALID', 'STORAGE_UNAVAILABLE'):
                    error = exc
        with self.guard:
            if error:
                self.observe_error(error)
            elif self.active():
                self.connection = 'online'
                self.last_error = None

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            try:
                self.cycle()
            except ClientError as exc:
                self.observe_error(exc)
            except Exception:
                self.observe_error(ClientError('PROTOCOL_ERROR', 'Synchronization failed unexpectedly; inspect the store and server.'))
            self.wake.wait(1)

    def close(self):
        self.stop.set()
        self.wake.set()
        self.thread.join()
        self.store.close()
