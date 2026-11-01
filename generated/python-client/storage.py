"""Atomic SQLite persistence; no network operation holds this module's lock."""
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from protocol import ClientError, MAX_INT, validate_name, validate_text

SCHEMA = [
    '''CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT,
       server_origin TEXT NOT NULL, receive_cursor INTEGER NOT NULL DEFAULT 0,
       next_local_order INTEGER NOT NULL DEFAULT 1)''',
    '''CREATE TABLE outbox (message_id TEXT PRIMARY KEY, sender TEXT NOT NULL,
       recipient TEXT NOT NULL, text TEXT NOT NULL, local_order INTEGER NOT NULL UNIQUE,
       state TEXT NOT NULL CHECK(state IN ('queued','accepted','failed')),
       server_sequence INTEGER, error_code TEXT, error_message TEXT)''',
    '''CREATE TABLE inbox (sender TEXT NOT NULL, message_id TEXT NOT NULL,
       recipient TEXT NOT NULL, text TEXT NOT NULL, sequence INTEGER NOT NULL UNIQUE,
       PRIMARY KEY(sender,message_id))''']
COLUMNS = {
    'metadata': ['id', 'username', 'server_origin', 'receive_cursor', 'next_local_order'],
    'outbox': ['message_id', 'sender', 'recipient', 'text', 'local_order', 'state', 'server_sequence', 'error_code', 'error_message'],
    'inbox': ['sender', 'message_id', 'recipient', 'text', 'sequence']}

class Store:
    def __init__(self, directory, server):
        self.lock = threading.RLock()
        self.db = None
        try:
            path = Path(directory) / 'messages.sqlite3'
            existed = path.exists()
            path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=0.5)
            self.db.row_factory = sqlite3.Row
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            if existed and version != 1:
                raise ClientError('STORE_VERSION_UNSUPPORTED', 'Store version is unsupported; choose a fresh store or explicitly reset it.')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA synchronous=FULL')
            if not existed:
                with self.transaction() as db:
                    for sql in SCHEMA:
                        db.execute(sql)
                    db.execute('INSERT INTO metadata VALUES (1,NULL,?,0,1)', (server,))
                    db.execute('PRAGMA user_version=1')
            for table, columns in COLUMNS.items():
                info = list(self.db.execute('PRAGMA table_info(' + table + ')'))
                actual = [r['name'] for r in info]
                integer_columns = {'id', 'receive_cursor', 'next_local_order', 'local_order', 'server_sequence', 'sequence'}
                types_ok = all(r['type'].upper() == ('INTEGER' if r['name'] in integer_columns else 'TEXT') for r in info)
                if set(actual) != set(columns) or not types_ok:
                    raise ClientError('STORAGE_UNAVAILABLE', 'Incompatible store schema; choose a fresh store.')
            meta = self.metadata()
            if len(self.db.execute('SELECT * FROM metadata').fetchall()) != 1 or meta['id'] != 1:
                raise ClientError('STORAGE_UNAVAILABLE', 'Invalid store metadata.')
            if meta['server_origin'] != server:
                raise ClientError('STORE_ORIGIN_MISMATCH', 'This store belongs to a different server origin; choose a fresh state directory.')
            if meta['username'] is not None:
                validate_name(meta['username'])
            if type(meta['receive_cursor']) is not int or not 0 <= meta['receive_cursor'] <= MAX_INT or type(meta['next_local_order']) is not int or not 1 <= meta['next_local_order'] <= MAX_INT:
                raise ClientError('STORAGE_UNAVAILABLE', 'Invalid store cursor or allocator.')
        except (sqlite3.Error, OSError) as exc:
            self.close()
            raise ClientError('STORAGE_UNAVAILABLE', 'Cannot open compatible writable storage: ' + str(exc)) from exc
        except Exception:
            self.close()
            raise

    @contextmanager
    def transaction(self):
        with self.lock:
            try:
                self.db.execute('BEGIN IMMEDIATE')
                yield self.db
                self.db.execute('COMMIT')
            except Exception as exc:
                if self.db.in_transaction:
                    self.db.execute('ROLLBACK')
                if isinstance(exc, sqlite3.Error):
                    raise ClientError('STORAGE_UNAVAILABLE', 'Storage transaction failed; free disk space/check permissions: ' + str(exc)) from exc
                raise

    def metadata(self):
        with self.lock:
            try:
                row = self.db.execute('SELECT * FROM metadata WHERE id=1').fetchone()
                if row is None:
                    raise ClientError('STORAGE_UNAVAILABLE', 'Missing store metadata.')
                return dict(row)
            except sqlite3.Error as exc:
                raise ClientError('STORAGE_UNAVAILABLE', str(exc)) from exc

    def login(self, name):
        validate_name(name)
        with self.transaction() as db:
            old = db.execute('SELECT username FROM metadata WHERE id=1').fetchone()[0]
            if old is not None and old != name:
                raise ClientError('IDENTITY_LOCKED', 'Reset a stopped client store explicitly to change identity.')
            db.execute('UPDATE metadata SET username=? WHERE id=1', (name,))
        return old is None

    def enqueue(self, recipient, text):
        validate_name(recipient)
        validate_text(text)
        with self.transaction() as db:
            meta = dict(db.execute('SELECT * FROM metadata WHERE id=1').fetchone())
            who = meta['username']
            if who is None:
                raise ClientError('IDENTITY_REQUIRED', 'Log in before sending.')
            if who == recipient:
                raise ClientError('SELF_SEND', 'Choose a different recipient.')
            order = meta['next_local_order']
            if order >= MAX_INT:
                raise ClientError('LOCAL_ORDER_EXHAUSTED', 'Local order exhausted; use an explicitly chosen fresh store.')
            while True:
                ident = str(uuid.uuid4())
                if db.execute('SELECT 1 FROM outbox WHERE message_id=?', (ident,)).fetchone() is None:
                    break
            db.execute('INSERT INTO outbox VALUES (?,?,?,?,?,\'queued\',NULL,NULL,NULL)', (ident, who, recipient, text, order))
            db.execute('UPDATE metadata SET next_local_order=? WHERE id=1', (order + 1,))
        return {'message_id': ident, 'state': 'queued', 'local_order': order}

    def snapshot(self):
        with self.lock:
            try:
                meta = self.metadata()
                outgoing = []
                for row in self.db.execute('SELECT * FROM outbox ORDER BY local_order'):
                    item = dict(row)
                    code, message = item.pop('error_code'), item.pop('error_message')
                    item['error'] = None if code is None else {'code': code, 'message': message}
                    outgoing.append(item)
                incoming = [dict(row) for row in self.db.execute('SELECT * FROM inbox ORDER BY sequence')]
                return meta, outgoing, incoming
            except sqlite3.Error as exc:
                raise ClientError('STORAGE_UNAVAILABLE', str(exc)) from exc

    def outcome(self, ident, state, sequence=None, error=None):
        with self.transaction() as db:
            db.execute('UPDATE outbox SET state=?,server_sequence=?,error_code=?,error_message=? WHERE message_id=? AND state=\'queued\'',
                       (state, sequence, error.code if error else None, error.message if error else None, ident))

    def receive(self, rows, after, next_after):
        with self.transaction() as db:
            cursor = db.execute('SELECT receive_cursor FROM metadata WHERE id=1').fetchone()[0]
            if cursor != after:
                raise ClientError('PROTOCOL_ERROR', 'Stale receive page; retry from the persisted cursor.')
            for row in rows:
                existing = db.execute('SELECT * FROM inbox WHERE sender=? AND message_id=?', (row['sender'], row['message_id'])).fetchone()
                if existing is not None:
                    if dict(existing) != row:
                        raise ClientError('PROTOCOL_ERROR', 'Conflicting duplicate inbox message.')
                else:
                    if db.execute('SELECT 1 FROM inbox WHERE sequence=?', (row['sequence'],)).fetchone():
                        raise ClientError('PROTOCOL_ERROR', 'Conflicting inbox sequence.')
                    db.execute('INSERT INTO inbox VALUES (?,?,?,?,?)', (row['sender'], row['message_id'], row['recipient'], row['text'], int(row['sequence'])))
            db.execute('UPDATE metadata SET receive_cursor=? WHERE id=1', (next_after,))

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
