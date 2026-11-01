"""Version-one durable state; all transactions use one application lock."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading
import uuid
from protocol import ClientError, MAX, username, text_valid

COLUMNS = {
    'metadata': ['id', 'username', 'server_origin', 'receive_cursor', 'next_local_order'],
    'outbox': ['message_id', 'sender', 'recipient', 'text', 'local_order', 'state', 'server_sequence', 'error_code', 'error_message'],
    'inbox': ['sender', 'message_id', 'recipient', 'text', 'sequence']}

class Store:
    def __init__(self, directory, server):
        self.lock = threading.RLock()
        self.db = None
        try:
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / 'messages.sqlite3'
            existed = path.exists()
            self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None, timeout=1)
            self.db.row_factory = sqlite3.Row
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if existed and (version != 1):
                raise ClientError('STORE_VERSION_UNSUPPORTED', 'Unsupported store version; choose a fresh store or explicitly reset this one.')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA synchronous=FULL')
            if not existed:
                with self.transaction():
                    self.db.execute('CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT, server_origin TEXT NOT NULL, receive_cursor INTEGER NOT NULL DEFAULT 0, next_local_order INTEGER NOT NULL DEFAULT 1)')
                    self.db.execute("CREATE TABLE outbox (message_id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL, text TEXT NOT NULL, local_order INTEGER UNIQUE NOT NULL, state TEXT NOT NULL CHECK(state IN ('queued','accepted','failed')), server_sequence INTEGER, error_code TEXT, error_message TEXT)")
                    self.db.execute('CREATE TABLE inbox (sender TEXT NOT NULL, message_id TEXT NOT NULL, recipient TEXT NOT NULL, text TEXT NOT NULL, sequence INTEGER UNIQUE NOT NULL, PRIMARY KEY(sender,message_id))')
                    self.db.execute('INSERT INTO metadata VALUES(1,NULL,?,0,1)', (server,))
                    self.db.execute('PRAGMA user_version=1')
            for table, columns in COLUMNS.items():
                actual = [r['name'] for r in self.db.execute('PRAGMA table_info(' + table + ')')]
                if set(actual) != set(columns):
                    raise ClientError('STORAGE_UNAVAILABLE', 'Incompatible SQLite schema; choose a fresh store.')
            meta = self.meta()
            if meta['server_origin'] != server:
                raise ClientError('STORE_ORIGIN_MISMATCH', 'This store belongs to a different server origin; choose a fresh state directory.')
        except Exception as exc:
            if self.db:
                self.db.close()
            if isinstance(exc, ClientError):
                raise
            raise ClientError('STORAGE_UNAVAILABLE', 'Cannot open the state store: ' + str(exc)) from exc

    @contextmanager
    def transaction(self):
        with self.lock:
            try:
                self.db.execute('BEGIN IMMEDIATE')
                yield
                self.db.execute('COMMIT')
            except Exception as exc:
                if self.db.in_transaction:
                    self.db.execute('ROLLBACK')
                if isinstance(exc, ClientError):
                    raise
                raise ClientError('STORAGE_UNAVAILABLE', 'Could not commit local state: ' + str(exc)) from exc

    def meta(self):
        with self.lock:
            try:
                rows = self.db.execute('SELECT * FROM metadata').fetchall()
                if len(rows) != 1 or rows[0]['id'] != 1:
                    raise ValueError('Invalid metadata singleton')
                return dict(rows[0])
            except (sqlite3.Error, ValueError) as exc:
                raise ClientError('STORAGE_UNAVAILABLE', 'Cannot read local metadata: ' + str(exc)) from exc

    def login(self, name):
        if not username(name):
            raise ClientError('INVALID_USERNAME', 'Use 1–32 lowercase ASCII letters, digits or underscores, beginning with a letter.')
        with self.transaction():
            saved = self.meta()['username']
            if saved is not None and saved != name:
                raise ClientError('IDENTITY_LOCKED', 'Reset the local store before changing identity.')
            self.db.execute('UPDATE metadata SET username=? WHERE id=1', (name,))
        return {'username': name}

    def enqueue(self, recipient, text):
        with self.transaction():
            meta = self.meta()
            sender = meta['username']
            if sender is None:
                raise ClientError('IDENTITY_REQUIRED', 'Log in before sending.')
            if not username(recipient):
                raise ClientError('INVALID_USERNAME', 'Enter a valid lowercase recipient username.')
            if recipient == sender:
                raise ClientError('SELF_SEND', 'Choose a different recipient.')
            if not text_valid(text):
                raise ClientError('INVALID_TEXT', 'Message must contain 1–4096 UTF-8 bytes of Unicode scalar text.')
            order = meta['next_local_order']
            if order >= MAX:
                raise ClientError('LOCAL_ORDER_EXHAUSTED', 'Local message order is exhausted; use an explicit fresh store.')
            while True:
                mid = str(uuid.uuid4())
                if not self.db.execute('SELECT 1 FROM outbox WHERE message_id=?', (mid,)).fetchone():
                    break
            self.db.execute("INSERT INTO outbox VALUES(?,?,?,?,?,'queued',NULL,NULL,NULL)", (mid, sender, recipient, text, order))
            self.db.execute('UPDATE metadata SET next_local_order=? WHERE id=1', (order + 1,))
        return {'message_id': mid, 'state': 'queued', 'local_order': order}

    def snapshot(self):
        with self.lock:
            try:
                meta = self.meta()
                inbox = [dict(r) for r in self.db.execute('SELECT * FROM inbox ORDER BY sequence')]
                outbox = []
                for row in self.db.execute('SELECT * FROM outbox ORDER BY local_order'):
                    row = dict(row)
                    code, message = row.pop('error_code'), row.pop('error_message')
                    row['error'] = {'code': code, 'message': message} if code else None
                    outbox.append(row)
                return meta, inbox, outbox
            except sqlite3.Error as exc:
                raise ClientError('STORAGE_UNAVAILABLE', 'Cannot read stored messages: ' + str(exc)) from exc

    def outcome(self, mid, state, sequence=None, error=None):
        with self.transaction():
            self.db.execute('UPDATE outbox SET state=?,server_sequence=?,error_code=?,error_message=? WHERE message_id=? AND state=\'queued\'',
                            (state, sequence, error.code if error else None, error.message if error else None, mid))

    def receive(self, messages, after, next_after):
        with self.transaction():
            if self.meta()['receive_cursor'] != after:
                raise ClientError('PROTOCOL_ERROR', 'Stale receive page; retry from the durable cursor.')
            for msg in messages:
                old = self.db.execute('SELECT * FROM inbox WHERE sender=? AND message_id=?', (msg['sender'], msg['message_id'])).fetchone()
                if old:
                    if dict(old) != msg:
                        raise ClientError('PROTOCOL_ERROR', 'Conflicting duplicate inbox message.')
                else:
                    if self.db.execute('SELECT 1 FROM inbox WHERE sequence=?', (msg['sequence'],)).fetchone():
                        raise ClientError('PROTOCOL_ERROR', 'Conflicting inbox sequence.')
                    self.db.execute('INSERT INTO inbox(sender,message_id,recipient,text,sequence) VALUES(?,?,?,?,?)', tuple(msg[k] for k in ('sender','message_id','recipient','text','sequence')))
            self.db.execute('UPDATE metadata SET receive_cursor=? WHERE id=1', (next_after,))

    def reset(self):
        with self.transaction():
            self.db.execute('DELETE FROM inbox')
            self.db.execute('DELETE FROM outbox')
            self.db.execute('UPDATE metadata SET username=NULL,receive_cursor=0,next_local_order=1 WHERE id=1')

    def close(self):
        with self.lock:
            self.db.close()
