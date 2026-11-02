"""Version-one durable state; transactions and snapshots share one short lock."""
import sqlite3
import threading
import uuid
from pathlib import Path
from protocol import ClientError, MAX, username, valid_text

SCHEMA = [
    '''CREATE TABLE metadata(id INTEGER PRIMARY KEY CHECK(id=1), username TEXT,
       server_origin TEXT, receive_cursor INTEGER DEFAULT 0, next_local_order INTEGER DEFAULT 1)''',
    '''CREATE TABLE outbox(message_id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL,
       text TEXT NOT NULL, local_order INTEGER UNIQUE, state TEXT CHECK(state IN ('queued','accepted','failed')),
       server_sequence INTEGER, error_code TEXT, error_message TEXT)''',
    '''CREATE TABLE inbox(sender TEXT, message_id TEXT, recipient TEXT NOT NULL, text TEXT NOT NULL,
       sequence INTEGER UNIQUE, PRIMARY KEY(sender,message_id))'''
]
COLUMNS = {
    'metadata': ['id','username','server_origin','receive_cursor','next_local_order'],
    'outbox': ['message_id','sender','recipient','text','local_order','state','server_sequence','error_code','error_message'],
    'inbox': ['sender','message_id','recipient','text','sequence']
}

class Store:
    def __init__(self, directory, origin):
        self.lock = threading.RLock()
        self.path = Path(directory) / 'messages.sqlite3'
        self.db = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(self.path, check_same_thread=False, timeout=1)
            self.db.row_factory = sqlite3.Row
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if version != 1 and (version != 0 or tables):
                raise ClientError('STORE_VERSION_UNSUPPORTED', 'Unsupported store version; explicitly select a fresh store or reset it.')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA synchronous=FULL')
            if version == 0:
                self.db.execute('BEGIN IMMEDIATE')
                try:
                    for sql in SCHEMA:
                        self.db.execute(sql)
                    self.db.execute('INSERT INTO metadata VALUES(1,NULL,?,0,1)', (origin,))
                    self.db.execute('PRAGMA user_version=1')
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    raise
            for table, cols in COLUMNS.items():
                actual = [r['name'] for r in self.db.execute('PRAGMA table_info(' + table + ')')]
                if actual != cols:
                    raise ClientError('STORAGE_UNAVAILABLE', 'Incompatible store schema; select a fresh store.')
            rows = self.db.execute('SELECT * FROM metadata').fetchall()
            if len(rows) != 1 or rows[0]['id'] != 1:
                raise ClientError('STORAGE_UNAVAILABLE', 'Invalid store metadata.')
            if rows[0]['server_origin'] != origin:
                raise ClientError('STORE_ORIGIN_MISMATCH', 'Store belongs to another server origin; choose a fresh state directory.')
        except Exception as exc:
            if self.db:
                self.db.close()
            if isinstance(exc, ClientError):
                raise
            raise ClientError('STORAGE_UNAVAILABLE', 'Cannot open store: ' + str(exc))

    def transaction(self, fn):
        with self.lock:
            try:
                self.db.execute('BEGIN IMMEDIATE')
                result = fn(self.db)
                self.db.commit()
                return result
            except Exception as exc:
                self.db.rollback()
                if isinstance(exc, ClientError):
                    raise
                raise ClientError('STORAGE_UNAVAILABLE', 'Local transaction failed: ' + str(exc))

    def snapshot(self):
        with self.lock:
            try:
                self.db.execute('BEGIN')
                meta = dict(self.db.execute('SELECT * FROM metadata WHERE id=1').fetchone())
                inbox = [dict(r) for r in self.db.execute('SELECT message_id,sender,recipient,text,sequence FROM inbox ORDER BY sequence')]
                outbox = []
                for row in self.db.execute('SELECT * FROM outbox ORDER BY local_order'):
                    r = dict(row)
                    code, msg = r.pop('error_code'), r.pop('error_message')
                    r['error'] = {'code':code,'message':msg} if code else None
                    outbox.append(r)
                self.db.commit()
                return meta, inbox, outbox
            except Exception as exc:
                self.db.rollback()
                raise ClientError('STORAGE_UNAVAILABLE', 'Cannot read store: ' + str(exc))

    def login(self, name):
        if not username(name):
            raise ClientError('INVALID_USERNAME', 'Use 1–32 lowercase ASCII letters, digits or underscores, beginning with a letter.')
        def action(db):
            old = db.execute('SELECT username FROM metadata WHERE id=1').fetchone()[0]
            if old is not None and old != name:
                raise ClientError('IDENTITY_LOCKED', 'Reset the local store explicitly to change identity.')
            db.execute('UPDATE metadata SET username=? WHERE id=1', (name,))
            return {'username':name}
        return self.transaction(action)

    def enqueue(self, recipient, text):
        if not username(recipient):
            raise ClientError('INVALID_USERNAME', 'Enter a valid lowercase recipient username.')
        if not valid_text(text):
            raise ClientError('INVALID_TEXT', 'Text must contain 1–4096 UTF-8 bytes and no surrogate code points.')
        def action(db):
            meta = db.execute('SELECT * FROM metadata WHERE id=1').fetchone()
            if meta['username'] is None:
                raise ClientError('IDENTITY_REQUIRED', 'Log in before sending.')
            if meta['username'] == recipient:
                raise ClientError('SELF_SEND', 'Choose a different recipient.')
            order = meta['next_local_order']
            if order >= MAX:
                raise ClientError('LOCAL_ORDER_EXHAUSTED', 'Local message order is exhausted; use a fresh store.')
            mid = str(uuid.uuid4())
            while db.execute('SELECT 1 FROM outbox WHERE message_id=?', (mid,)).fetchone():
                mid = str(uuid.uuid4())
            db.execute('INSERT INTO outbox VALUES(?,?,?,?,?,\'queued\',NULL,NULL,NULL)', (mid,meta['username'],recipient,text,order))
            db.execute('UPDATE metadata SET next_local_order=? WHERE id=1', (order+1,))
            return {'message_id':mid,'state':'queued','local_order':order}
        return self.transaction(action)

    def outcome(self, mid, state, sequence=None, error=None):
        def action(db):
            db.execute('UPDATE outbox SET state=?,server_sequence=?,error_code=?,error_message=? WHERE message_id=?',
                       (state,sequence,error.code if error else None,error.message if error else None,mid))
        self.transaction(action)

    def receive(self, page, after):
        def action(db):
            current = db.execute('SELECT receive_cursor FROM metadata WHERE id=1').fetchone()[0]
            if current != after:
                raise ClientError('PROTOCOL_ERROR', 'Receive page no longer matches the committed cursor.')
            for msg in page['messages']:
                old = db.execute('SELECT message_id,sender,recipient,text,sequence FROM inbox WHERE sender=? AND message_id=?', (msg['sender'],msg['message_id'])).fetchone()
                seq = db.execute('SELECT sender,message_id FROM inbox WHERE sequence=?', (msg['sequence'],)).fetchone()
                if old is not None:
                    if dict(old) != msg:
                        raise ClientError('PROTOCOL_ERROR', 'Conflicting duplicate incoming message.')
                elif seq is not None:
                    raise ClientError('PROTOCOL_ERROR', 'Conflicting incoming sequence.')
                else:
                    db.execute('INSERT INTO inbox(sender,message_id,recipient,text,sequence) VALUES(?,?,?,?,?)',
                               (msg['sender'],msg['message_id'],msg['recipient'],msg['text'],msg['sequence']))
            db.execute('UPDATE metadata SET receive_cursor=? WHERE id=1', (int(page['next_after']),))
        self.transaction(action)

    def close(self):
        with self.lock:
            self.db.close()

def reset_files(directory):
    base = Path(directory)
    try:
        for suffix in ('','-journal','-wal','-shm'):
            path = base / ('messages.sqlite3' + suffix)
            if path.exists() or path.is_symlink():
                path.unlink()
    except OSError as exc:
        raise ClientError('STORAGE_UNAVAILABLE', 'Cannot reset local store: ' + str(exc))
