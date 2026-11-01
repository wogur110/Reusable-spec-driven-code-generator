"""Shared production operations and a single serial synchronization worker."""
import threading
from urllib.parse import urlencode
from protocol import Failure, request, receipt, page, wire_error, origin
from storage import Store

class Client:
    def __init__(self, server, directory, transport='online', changed=None):
        self.server = origin(server)
        self.store = Store(directory, self.server)
        self.mode = transport
        self.connection = 'offline' if transport == 'offline' else 'unknown'
        self.error = None
        self.paused = False
        self.changed = changed or (lambda: None)
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.worker = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.worker.start()

    def login(self, name):
        result = self.store.login(name)
        self.changed()
        self.wake.set()
        return result

    def send(self, recipient, text):
        if self.paused:
            raise Failure('CURSOR_INVALID', 'Synchronization paused; explicitly reset the local store.')
        result = self.store.enqueue(recipient, text)
        self.changed()
        return result

    def transport(self, mode):
        if mode not in ('online', 'offline'):
            raise Failure('INVALID_COMMAND', 'Transport must be online or offline.')
        self.mode = mode
        self.connection = 'offline' if mode == 'offline' else 'unknown'
        self.wake.set()
        return self.status()

    def status(self):
        meta, _, out = self.store.snapshot()
        return {'username': meta['username'], 'transport': self.mode, 'connection': self.connection,
                'cursor': meta['receive_cursor'], 'pending_count': sum(r['state']=='queued' for r in out),
                'sync_paused': self.paused, 'last_error': self.error.data() if self.error else None}

    def enabled(self):
        return not self.stop.is_set() and self.mode == 'online' and not self.paused

    def send_one(self, row):
        sent = {k: row[k] for k in ('message_id','sender','recipient','text')}
        status, data, failure = request(self.server, 'POST', '/api/v1/messages', sent)
        error = wire_error(status, data) if data is not None else None
        state, sequence = 'queued', None
        if status is not None and 400 <= status < 500 and status not in (408,429):
            state = 'failed'
            error = error or Failure('HTTP_ERROR', 'Server rejected message (HTTP %s).' % status)
        elif status in (200,201) and failure is None:
            try:
                sequence = receipt(data, sent)
                state = 'accepted'
                error = None
            except Failure as e:
                error = e
        else:
            error = error or failure or Failure('HTTP_ERROR' if status in (408,429) or status and status >= 500 else 'PROTOCOL_ERROR', 'Unexpected HTTP response %s; retrying unchanged message.' % status)
        self.store.outcome(row['message_id'], state, sequence, error)
        self.changed()
        return error

    def receive_one(self, user, cursor):
        status, data, failure = request(self.server, 'GET', '/api/v1/messages?' + urlencode({'recipient':user,'after':cursor}))
        error = wire_error(status, data) if data is not None else None
        if error and error.code == 'CURSOR_INVALID':
            self.paused = True
            raise Failure('CURSOR_INVALID', 'Server cursor is invalid. Explicitly reset the local store before continuing.')
        if status != 200 or failure:
            raise error or failure or Failure('HTTP_ERROR', 'Cannot receive messages (HTTP %s); retrying.' % status)
        rows, next_cursor = page(data, user, cursor)
        self.store.receive(rows, next_cursor)
        if rows:
            self.changed()

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            if self.enabled():
                cycle_error = None
                try:
                    meta, _, out = self.store.snapshot()
                    if meta['username']:
                        queued = next((r for r in out if r['state']=='queued'), None)
                        if queued and self.enabled():
                            try:
                                cycle_error = self.send_one(queued)
                            except Failure as e:
                                cycle_error = e
                        if self.enabled():
                            try:
                                self.receive_one(meta['username'], self.store.metadata()['receive_cursor'])
                            except Failure as e:
                                if self.paused or cycle_error is None or e.code == 'STORAGE_UNAVAILABLE':
                                    cycle_error = e
                        if not self.stop.is_set():
                            self.error = cycle_error
                            self.connection = ('offline' if cycle_error and cycle_error.code == 'TRANSPORT_ERROR' else 'error' if cycle_error else 'online') if self.mode == 'online' else 'offline'
                except Exception as e:
                    self.error = e if isinstance(e, Failure) else Failure('STORAGE_UNAVAILABLE', str(e))
                    self.connection = 'error'
            self.wake.wait(1)

    def close(self):
        self.stop.set()
        self.wake.set()
        if self.worker.is_alive():
            self.worker.join()
        self.store.close()
