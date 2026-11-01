"""Version-one durable store. Every mutation owns one short transaction."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading
import uuid
from protocol import Failure, MAX, username, message_text

SCHEMA = [
 'CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT, server_origin TEXT, receive_cursor INTEGER DEFAULT 0, next_local_order INTEGER DEFAULT 1)',
 "CREATE TABLE outbox (message_id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL, text TEXT NOT NULL, local_order INTEGER UNIQUE, state TEXT CHECK(state IN ('queued','accepted','failed')), server_sequence INTEGER, error_code TEXT, error_message TEXT)",
 'CREATE TABLE inbox (sender TEXT, message_id TEXT, recipient TEXT NOT NULL, text TEXT NOT NULL, sequence INTEGER UNIQUE, PRIMARY KEY(sender,message_id))']

class Store:
    def __init__(self, directory, server):
        self.lock = threading.RLock()
        self.db = None
        try:
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(directory / 'messages.sqlite3', check_same_thread=False, isolation_level=None, timeout=1)
            self.db.row_factory = sqlite3.Row
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if version != 1 and (version != 0 or tables):
                raise Failure('STORE_VERSION_UNSUPPORTED', 'Unsupported store version; select a fresh store or explicitly reset.')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA synchronous=FULL')
            if version == 0:
                with self.transaction():
                    for statement in SCHEMA:
                        self.db.execute(statement)
                    self.db.execute('INSERT INTO metadata VALUES (1,NULL,?,0,1)', (server,))
                    self.db.execute('PRAGMA user_version=1')
            expected = {
                'metadata': 'id username server_origin receive_cursor next_local_order',
                'outbox': 'message_id sender recipient text local_order state server_sequence error_code error_message',
                'inbox': 'sender message_id recipient text sequence'}
            for table, columns in expected.items():
                actual = {r['name'] for r in self.db.execute('PRAGMA table_info(' + table + ')')}
                if actual != set(columns.split()):
                    raise Failure('STORAGE_UNAVAILABLE', 'Incompatible SQLite schema; select a fresh store.')
            meta = self.metadata()
            if not meta or self.db.execute('SELECT count(*) FROM metadata').fetchone()[0] != 1:
                raise Failure('STORAGE_UNAVAILABLE', 'Invalid store metadata.')
            if meta['server_origin'] != server:
                raise Failure('STORE_ORIGIN_MISMATCH', 'Stored server differs; choose an explicitly fresh state directory.')
        except Exception as e:
            if self.db:
                self.db.close()
            if isinstance(e, Failure):
                raise
            raise Failure('STORAGE_UNAVAILABLE', 'Cannot open store: ' + str(e))

    @contextmanager
    def transaction(self):
        with self.lock:
            try:
                self.db.execute('BEGIN IMMEDIATE')
                yield
                self.db.execute('COMMIT')
            except Exception as e:
                if self.db.in_transaction:
                    self.db.execute('ROLLBACK')
                if isinstance(e, Failure):
                    raise
                raise Failure('STORAGE_UNAVAILABLE', 'Storage transaction failed: ' + str(e))

    def metadata(self):
        with self.lock:
            row = self.db.execute('SELECT * FROM metadata WHERE id=1').fetchone()
            return dict(row) if row else None

    def login(self, name):
        username(name)
        with self.transaction():
            old = self.metadata()['username']
            if old is not None and old != name:
                raise Failure('IDENTITY_LOCKED', 'Reset the local store to change identity.')
            self.db.execute('UPDATE metadata SET username=? WHERE id=1', (name,))
        return {'username': name}

    def enqueue(self, recipient, text):
        with self.transaction():
            meta = self.metadata()
            sender = meta['username']
            if sender is None:
                raise Failure('IDENTITY_REQUIRED', 'Log in first.')
            username(recipient)
            if sender == recipient:
                raise Failure('SELF_SEND', 'Choose a different recipient.')
            message_text(text)
            order = meta['next_local_order']
            if order >= MAX:
                raise Failure('LOCAL_ORDER_EXHAUSTED', 'Local message order exhausted; use a fresh store.')
            while True:
                key = str(uuid.uuid4())
                if not self.db.execute('SELECT 1 FROM outbox WHERE message_id=?', (key,)).fetchone():
                    break
            self.db.execute("INSERT INTO outbox VALUES (?,?,?,?,?,'queued',NULL,NULL,NULL)", (key, sender, recipient, text, order))
            self.db.execute('UPDATE metadata SET next_local_order=? WHERE id=1', (order+1,))
        return {'message_id': key, 'state': 'queued', 'local_order': order}

    def snapshot(self):
        with self.lock:
            meta = self.metadata()
            incoming = [dict(r) for r in self.db.execute('SELECT message_id,sender,recipient,text,sequence FROM inbox ORDER BY sequence')]
            outgoing = []
            for row in self.db.execute('SELECT * FROM outbox ORDER BY local_order'):
                r = dict(row)
                code, msg = r.pop('error_code'), r.pop('error_message')
                r['error'] = {'code': code, 'message': msg} if code else None
                outgoing.append(r)
            return meta, incoming, outgoing

    def outcome(self, key, state, sequence, error):
        with self.transaction():
            self.db.execute('UPDATE outbox SET state=?,server_sequence=?,error_code=?,error_message=? WHERE message_id=?', (state, sequence, error.code if error else None, error.message if error else None, key))

    def receive(self, rows, cursor):
        with self.transaction():
            for row in rows:
                existing = self.db.execute('SELECT message_id,sender,recipient,text,sequence FROM inbox WHERE sender=? AND message_id=?', (row['sender'],row['message_id'])).fetchone()
                if existing:
                    if dict(existing) != row:
                        raise Failure('PROTOCOL_ERROR', 'Conflicting incoming message; store unchanged.')
                else:
                    clash = self.db.execute('SELECT 1 FROM inbox WHERE sequence=?', (row['sequence'],)).fetchone()
                    if clash:
                        raise Failure('PROTOCOL_ERROR', 'Conflicting incoming sequence; store unchanged.')
                    self.db.execute('INSERT INTO inbox VALUES (?,?,?,?,?)', (row['sender'],row['message_id'],row['recipient'],row['text'],int(row['sequence'])))
            self.db.execute('UPDATE metadata SET receive_cursor=? WHERE id=1', (cursor,))

    def close(self):
        with self.lock:
            self.db.close()

def reset_files(directory):
    try:
        for suffix in ('', '-journal', '-wal', '-shm'):
            path = Path(directory) / ('messages.sqlite3' + suffix)
            path.unlink(missing_ok=True)
    except OSError as e:
        raise Failure('STORAGE_UNAVAILABLE', 'Reset failed: ' + str(e))
