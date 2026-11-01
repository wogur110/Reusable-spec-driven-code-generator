"""Validation and version-one transactional persistence."""
import ipaddress
import re
import sqlite3
import threading
import uuid
from pathlib import Path
from urllib.parse import urlsplit

MAX = 9007199254740991

class ClientError(Exception):
    def __init__(self, code, message, permanent=False):
        super().__init__(message)
        self.code, self.message, self.permanent = code, message, permanent
    def data(self):
        return {'code': self.code, 'message': self.message}

def require(condition, message='Invalid server response.'):
    if not condition:
        raise ClientError('PROTOCOL_ERROR', message)

def exact(value, keys):
    require(isinstance(value, dict) and set(value) == set(keys))

def integer(value, minimum=0):
    return type(value) in (int, float) and minimum <= value <= MAX and value == int(value)

def username(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value) is not None

def valid_text(value):
    try:
        return isinstance(value, str) and 1 <= len(value.encode('utf-8')) <= 4096
    except UnicodeError:
        return False

def message_id(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', value) is not None

def origin(value):
    try:
        p = urlsplit(value)
        host = p.hostname
        valid = host == 'localhost'
        if not valid:
            valid = ipaddress.ip_address(host).is_loopback
        if p.scheme != 'http' or not valid or p.username is not None or p.password is not None or p.path or p.query or p.fragment or '?' in value or '#' in value:
            raise ValueError()
        port = p.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError()
        return 'http://' + ('[' + host + ']' if ':' in host else host) + (':' + str(port) if port and port != 80 else '')
    except (ValueError, TypeError, AttributeError):
        raise ClientError('INVALID_COMMAND', 'Server must be an HTTP loopback origin without a path, credentials, query or fragment.')

def reset_files(state_dir):
    base = Path(state_dir) / 'messages.sqlite3'
    try:
        for suffix in ('', '-journal', '-wal', '-shm'):
            p = Path(str(base) + suffix)
            if p.exists() or p.is_symlink():
                p.unlink()
    except OSError as e:
        raise ClientError('STORAGE_UNAVAILABLE', str(e))

class Store:
    def __init__(self, directory, server):
        self.lock = threading.RLock()
        self.db = None
        try:
            path = Path(directory) / 'messages.sqlite3'
            path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(str(path), check_same_thread=False, timeout=1)
            self.db.row_factory = sqlite3.Row
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            if version != 1 and (version != 0 or tables):
                raise ClientError('STORE_VERSION_UNSUPPORTED', 'Unsupported store version; choose a fresh store or explicitly reset.')
            self.db.execute('PRAGMA foreign_keys=ON')
            self.db.execute('PRAGMA synchronous=FULL')
            if version == 0:
                with self.transaction():
                    self.db.execute('CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), username TEXT, server_origin TEXT NOT NULL, receive_cursor INTEGER NOT NULL DEFAULT 0, next_local_order INTEGER NOT NULL DEFAULT 1)')
                    self.db.execute("CREATE TABLE outbox (message_id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL, text TEXT NOT NULL, local_order INTEGER UNIQUE, state TEXT CHECK(state IN ('queued','accepted','failed')), server_sequence INTEGER, error_code TEXT, error_message TEXT)")
                    self.db.execute('CREATE TABLE inbox (sender TEXT, message_id TEXT, recipient TEXT NOT NULL, text TEXT NOT NULL, sequence INTEGER UNIQUE, PRIMARY KEY(sender,message_id))')
                    self.db.execute('INSERT INTO metadata VALUES (1,NULL,?,0,1)', (server,))
                    self.db.execute('PRAGMA user_version=1')
            meta = self.meta()
            if meta['server_origin'] != server:
                raise ClientError('STORE_ORIGIN_MISMATCH', 'This store belongs to another server origin. Choose a fresh store.')
            self.db.execute('SELECT message_id,sender,recipient,text,local_order,state,server_sequence,error_code,error_message FROM outbox LIMIT 0')
            self.db.execute('SELECT sender,message_id,recipient,text,sequence FROM inbox LIMIT 0')
            if (meta['username'] is not None and not username(meta['username'])) or not integer(meta['receive_cursor']) or not integer(meta['next_local_order'], 1):
                raise ClientError('STORAGE_UNAVAILABLE', 'Invalid stored metadata.')
        except Exception as e:
            if self.db:
                self.db.close()
            if isinstance(e, ClientError):
                raise
            raise ClientError('STORAGE_UNAVAILABLE', str(e))

    def transaction(self):
        from contextlib import contextmanager
        @contextmanager
        def tx():
            with self.lock:
                try:
                    self.db.execute('BEGIN IMMEDIATE')
                    yield
                    self.db.commit()
                except Exception as e:
                    self.db.rollback()
                    if isinstance(e, ClientError):
                        raise
                    raise ClientError('STORAGE_UNAVAILABLE', str(e))
        return tx()

    def meta(self):
        with self.lock:
            row = self.db.execute('SELECT id,username,server_origin,receive_cursor,next_local_order FROM metadata WHERE id=1').fetchone()
            if not row:
                raise ClientError('STORAGE_UNAVAILABLE', 'Missing store metadata.')
            return dict(row)

    def login(self, name):
        if not username(name):
            raise ClientError('INVALID_USERNAME', 'Use 1–32 lowercase ASCII letters, digits or underscore, beginning with a letter.')
        with self.transaction():
            previous = self.meta()['username']
            if previous is not None and previous != name:
                raise ClientError('IDENTITY_LOCKED', 'Reset the store to change identity.')
            self.db.execute('UPDATE metadata SET username=? WHERE id=1', (name,))
        return {'username': name}

    def enqueue(self, recipient, text):
        with self.transaction():
            meta = self.meta()
            sender = meta['username']
            if sender is None:
                raise ClientError('IDENTITY_REQUIRED', 'Log in before composing.')
            if not username(recipient):
                raise ClientError('INVALID_USERNAME', 'Enter a valid recipient username.')
            if recipient == sender:
                raise ClientError('SELF_SEND', 'Choose a different recipient.')
            if not valid_text(text):
                raise ClientError('INVALID_TEXT', 'Text must contain 1–4096 UTF-8 bytes of Unicode scalar data.')
            order = meta['next_local_order']
            if order >= MAX:
                raise ClientError('LOCAL_ORDER_EXHAUSTED', 'The local order allocator is exhausted.')
            while True:
                key = str(uuid.uuid4())
                if not self.db.execute('SELECT 1 FROM outbox WHERE message_id=?', (key,)).fetchone():
                    break
            self.db.execute("INSERT INTO outbox VALUES (?,?,?,?,?,'queued',NULL,NULL,NULL)", (key, sender, recipient, text, order))
            self.db.execute('UPDATE metadata SET next_local_order=? WHERE id=1', (order + 1,))
        return {'message_id': key, 'state': 'queued', 'local_order': order}

    def outgoing(self):
        with self.lock:
            result = []
            for row in self.db.execute('SELECT * FROM outbox ORDER BY local_order'):
                d = dict(row)
                code, msg = d.pop('error_code'), d.pop('error_message')
                d['error'] = {'code': code, 'message': msg} if code else None
                result.append(d)
            return result

    def incoming(self):
        with self.lock:
            return [dict(r) for r in self.db.execute('SELECT message_id,sender,recipient,text,sequence FROM inbox ORDER BY sequence')]

    def outcome(self, key, state, sequence=None, error=None):
        with self.transaction():
            self.db.execute('UPDATE outbox SET state=?,server_sequence=?,error_code=?,error_message=? WHERE message_id=?', (state, sequence, error.code if error else None, error.message if error else None, key))

    def receive(self, page, user, after):
        exact(page, ('messages', 'next_after'))
        rows = page['messages']
        require(isinstance(rows, list) and len(rows) <= 100 and integer(page['next_after']))
        seen = set()
        seq = after
        for m in rows:
            exact(m, ('message_id', 'sender', 'recipient', 'text', 'sequence'))
            require(message_id(m['message_id']) and username(m['sender']) and m['recipient'] == user and m['sender'] != user and valid_text(m['text']))
            seq += 1
            require(integer(m['sequence'], 1) and m['sequence'] == seq)
            key = (m['sender'], m['message_id'])
            require(key not in seen)
            seen.add(key)
        require(page['next_after'] == seq)
        with self.transaction():
            require(self.meta()['receive_cursor'] == after, 'Stale receive page.')
            for m in rows:
                old = self.db.execute('SELECT message_id,sender,recipient,text,sequence FROM inbox WHERE sender=? AND message_id=?', (m['sender'], m['message_id'])).fetchone()
                if old:
                    require(dict(old) == m, 'Conflicting duplicate message.')
                else:
                    require(not self.db.execute('SELECT 1 FROM inbox WHERE sequence=?', (m['sequence'],)).fetchone(), 'Conflicting sequence.')
                    self.db.execute('INSERT INTO inbox VALUES (?,?,?,?,?)', (m['sender'], m['message_id'], m['recipient'], m['text'], int(m['sequence'])))
            self.db.execute('UPDATE metadata SET receive_cursor=? WHERE id=1', (int(seq),))
        return bool(rows)

    def close(self):
        with self.lock:
            self.db.close()
