"""Production messaging engine shared by both frontends."""
import threading
from protocol import ClientError, Transport, exact, integer, message, require, username, wire_error
from storage import Store

class Client:
    def __init__(self, server_origin, state_dir, transport='online', changed=None):
        self.store = Store(state_dir, server_origin)
        self.http = Transport(server_origin)
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.changed = changed or (lambda: None)
        self.mode = transport
        self.mode_revision = 0
        self.connection = 'offline' if transport == 'offline' else 'unknown'
        self.last_error = None
        self.paused = False
        self.presence_status = 'unknown'
        self.presence_pending = False
        self.directory_status = 'stale' if transport == 'offline' else 'loading'
        self.receipt_status = 'unknown'
        self.users = []
        self.feature_error = ''
        if self.store.snapshot()[0]['username'] and transport == 'online':
            self.presence_pending = True
            self.presence_status = 'pending'
        self.thread = threading.Thread(target=self.run, name='messenger-sync', daemon=True)
        self.thread.start()

    def snapshot(self):
        with self.lock:
            meta, inbox, outbox = self.store.snapshot()
            status = {'username':meta['username'], 'transport':self.mode, 'connection':self.connection,
                      'cursor':meta['receive_cursor'], 'pending_count':sum(r['state']=='queued' for r in outbox),
                      'sync_paused':self.paused, 'last_error':self.last_error}
            return {'status':status,'inbox':inbox,'outbox':outbox,'users':list(self.users),
                    'directory_status':self.directory_status,'receipt_status':self.receipt_status,
                    'presence_status':self.presence_status,'feature_error':self.feature_error}

    def login(self, name):
        with self.lock:
            old = self.store.snapshot()[0]['username']
            result = self.store.login(name)
            if old is None and self.mode == 'online':
                self.presence_pending = True
                self.presence_status = 'pending'
        self.changed()
        self.wake.set()
        return result

    def send(self, recipient, text):
        with self.lock:
            if self.paused:
                raise ClientError('CURSOR_INVALID', 'Synchronization is paused. Explicitly reset the local store for this server session.')
            result = self.store.enqueue(recipient, text)
        self.changed()
        self.wake.set()
        return result

    def transport(self, mode):
        if mode not in ('online','offline'):
            raise ClientError('INVALID_COMMAND', 'Transport must be online or offline.')
        with self.lock:
            if self.mode != mode:
                self.mode = mode
                self.mode_revision += 1
                self.connection = 'offline' if mode == 'offline' else ('error' if self.paused else 'unknown')
                if mode == 'offline':
                    self.directory_status = 'stale'
                if self.store.snapshot()[0]['username']:
                    self.presence_pending = True
                    self.presence_status = 'pending'
        self.wake.set()
        return self.snapshot()['status']

    def refresh(self):
        self.wake.set()

    def shutdown(self):
        self.stop.set()
        self.wake.set()
        self.thread.join()
        self.store.close()

    def allowed(self, revision):
        with self.lock:
            return not self.stop.is_set() and not self.paused and self.mode == 'online' and self.mode_revision == revision

    def core_error(self, error):
        with self.lock:
            self.last_error = error.object()
            self.connection = 'offline' if self.mode == 'offline' or error.code == 'TRANSPORT_ERROR' else 'error'
            if error.code == 'CURSOR_INVALID':
                self.paused = True
                self.connection = 'error'
                self.last_error = {'code':'CURSOR_INVALID','message':'Server cursor is invalid. Explicitly reset the local store for this server session.'}

    def perform_presence(self, name, revision, mode):
        payload = {'username':name,'online':mode=='online'}
        error = None
        with self.lock:
            if self.stop.is_set() or self.paused or revision != self.mode_revision:
                return
            self.presence_status = 'pending'
        try:
            status, body = self.http.request('POST','/api/v1/presence',payload,2)
            if status != 200:
                raise wire_error(status, body)
            require(exact(body,'username online') and body['username']==name and type(body['online']) is bool and body['online']==payload['online'])
        except ClientError as exc:
            error = exc
        with self.lock:
            if self.stop.is_set() or revision != self.mode_revision:
                return
            self.presence_status = 'error' if error else 'confirmed'
            self.presence_pending = bool(error and mode == 'online')

    def send_one(self, row):
        error, state, sequence = None, 'queued', None
        try:
            payload = {k:row[k] for k in ('message_id','sender','recipient','text')}
            status, body = self.http.request('POST','/api/v1/messages',payload)
            if status in (200,201):
                require(exact(body,'message_id sender recipient sequence') and all(body[k]==row[k] for k in ('message_id','sender','recipient')) and integer(body['sequence'],1), 'Invalid acceptance receipt; original message will retry.')
                state, sequence = 'accepted', int(body['sequence'])
            elif 400 <= status < 600:
                error = wire_error(status,body)
                if 400 <= status < 500 and status not in (408,429):
                    state = 'failed'
            else:
                error = ClientError('PROTOCOL_ERROR','Unexpected HTTP response; original message will retry.')
        except ClientError as exc:
            error = exc
        if self.stop.is_set():
            return None
        try:
            self.store.outcome(row['message_id'], state, sequence, error)
            self.changed()
        except ClientError as exc:
            error = exc
        if error:
            self.core_error(error)
        return error

    def receive(self, name):
        after = self.store.snapshot()[0]['receive_cursor']
        status, body = self.http.request('GET', '/api/v1/messages?recipient=' + name + '&after=' + str(after))
        if self.stop.is_set():
            return
        if status != 200:
            err = wire_error(status,body)
            if err.code == 'CURSOR_INVALID' and (not exact(body,'error') or body['error']['field'] != 'after'):
                err = ClientError('PROTOCOL_ERROR','Invalid cursor error response.')
            raise err
        require(exact(body,'messages next_after') and isinstance(body['messages'],list) and len(body['messages']) <= 100 and integer(body['next_after']))
        seen = set()
        for index, row in enumerate(body['messages']):
            require(message(row) and row['recipient']==name and row['sequence']==after+index+1, 'Invalid incoming message or noncontiguous page.')
            key = row['sender'],row['message_id']
            require(key not in seen, 'Duplicate key in incoming page.')
            seen.add(key)
        require(body['next_after']==after+len(body['messages']), 'Incoming page cursor does not match its messages.')
        self.store.receive(body,after)
        if body['messages']:
            with self.lock:
                self.receipt_status = 'pending'
            self.changed()

    def auxiliary(self, name, revision):
        if not self.allowed(revision):
            return
        through = self.store.snapshot()[0]['receive_cursor']
        try:
            status, body = self.http.request('POST','/api/v1/receipts',{'recipient':name,'through':through},2)
            if status != 200:
                raise wire_error(status,body)
            require(exact(body,'recipient through') and body['recipient']==name and integer(body['through']) and body['through']>=through)
            with self.lock:
                if not self.stop.is_set():
                    self.receipt_status = 'confirmed'
        except ClientError as exc:
            with self.lock:
                self.receipt_status = 'error'
                self.feature_error = 'Receipt: ' + exc.message
        if not self.allowed(revision):
            return
        announce_error = None
        try:
            status, body = self.http.request('POST','/api/v1/users',{'username':name},2)
            if status != 200:
                raise wire_error(status,body)
            require(exact(body,'username') and body['username']==name)
        except ClientError as exc:
            announce_error = exc
        if not self.allowed(revision):
            return
        directory_error = None
        try:
            status, body = self.http.request('GET','/api/v1/users',None,2)
            if status != 200:
                raise wire_error(status,body)
            require(exact(body,'users') and isinstance(body['users'],list))
            names = []
            for row in body['users']:
                require(exact(row,'username online') and username(row['username']) and type(row['online']) is bool)
                names.append(row['username'])
            require(names==sorted(set(names)), 'Directory must have sorted unique users.')
            with self.lock:
                if not self.stop.is_set() and revision == self.mode_revision and self.mode == 'online':
                    self.users = body['users']
        except ClientError as exc:
            directory_error = exc
        with self.lock:
            if self.stop.is_set():
                return
            errors = [e for e in (announce_error,directory_error) if e]
            if self.mode == 'offline' or revision != self.mode_revision:
                self.directory_status = 'stale'
            elif errors:
                self.directory_status = 'stale' if any(e.code=='TRANSPORT_ERROR' for e in errors) else 'error'
                self.feature_error = 'Directory: ' + '; '.join(e.message for e in errors)
            else:
                self.directory_status = 'current'
                if self.receipt_status != 'error':
                    self.feature_error = ''

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            try:
                with self.lock:
                    meta, _, rows = self.store.snapshot()
                    name, mode, revision = meta['username'],self.mode,self.mode_revision
                    paused, pending = self.paused,self.presence_pending
                if name and not paused:
                    if pending:
                        self.perform_presence(name, revision, mode)
                    if self.stop.is_set():
                        break
                    if revision != self.mode_revision:
                        continue
                    if self.allowed(revision):
                        cycle_error = None
                        first = next((r for r in rows if r['state']=='queued'),None)
                        if first:
                            cycle_error = self.send_one(first)
                        if self.allowed(revision):
                            try:
                                self.receive(name)
                            except ClientError as exc:
                                self.core_error(exc)
                                cycle_error = exc
                        if self.allowed(revision):
                            if cycle_error is None:
                                with self.lock:
                                    self.last_error = None
                                    self.connection = 'online'
                            self.auxiliary(name,revision)
                if revision != self.mode_revision:
                    continue
            except ClientError as exc:
                self.core_error(exc)
            except Exception as exc:
                self.core_error(ClientError('STORAGE_UNAVAILABLE','Synchronization failed: ' + str(exc)))
            self.wake.wait(1)
