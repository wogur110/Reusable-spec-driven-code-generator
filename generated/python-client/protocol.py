"""Wire validation and bounded, direct loopback HTTP transport."""
import http.client
import ipaddress
import json
import re
import socket
import threading
from urllib.parse import urlsplit

MAX = 9007199254740991

class ClientError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message
    def data(self):
        return {'code': self.code, 'message': self.message}

def require(condition, message='Invalid server response.'):
    if not condition:
        raise ClientError('PROTOCOL_ERROR', message)

def exact(value, keys):
    return isinstance(value, dict) and set(value) == set(keys.split())

def integer(value, minimum=0):
    return type(value) in (int, float) and minimum <= value <= MAX and value == int(value)

def username(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value, re.ASCII) is not None

def message_id(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value) is not None

def text_valid(value):
    if not isinstance(value, str):
        return False
    try:
        return 1 <= len(value.encode('utf-8')) <= 4096
    except UnicodeError:
        return False

def origin(value):
    try:
        u = urlsplit(value)
        host = u.hostname
        if u.scheme != 'http' or not host or u.username is not None or u.password is not None or u.path or u.query or u.fragment or '?' in value or '#' in value:
            raise ValueError()
        if host != 'localhost' and not ipaddress.ip_address(host).is_loopback:
            raise ValueError()
        port = u.port or 80
        if not 1 <= port <= 65535:
            raise ValueError()
        h = '[' + host + ']' if ':' in host else host
        return 'http://' + h + (':' + str(port) if port != 80 else '')
    except (ValueError, TypeError):
        raise ClientError('INVALID_COMMAND', 'Server must be an HTTP loopback origin without a path, credentials, query or fragment.')

def parse_json(raw):
    def invalid(_):
        raise ValueError('Nonfinite JSON number')
    return json.loads(raw.decode('utf-8'), parse_constant=invalid)

ERRORS = {
    'INVALID_REQUEST': (400, {None}), 'INVALID_JSON': (400, {None}),
    'INVALID_FIELDS': (400, {None}), 'INVALID_MESSAGE_ID': (400, {'message_id'}),
    'INVALID_USERNAME': (400, {'sender', 'recipient', 'username'}),
    'SELF_SEND': (400, {'recipient'}), 'INVALID_TEXT': (400, {'text'}),
    'INVALID_QUERY': (400, {'after', None}), 'NOT_FOUND': (404, {None}),
    'METHOD_NOT_ALLOWED': (405, {None}), 'IDEMPOTENCY_CONFLICT': (409, {'message_id'}),
    'CURSOR_INVALID': (409, {'after', 'through'}), 'PAYLOAD_TOO_LARGE': (413, {None}),
    'UNSUPPORTED_MEDIA_TYPE': (415, {None}), 'SEQUENCE_EXHAUSTED': (503, {None}),
    'INTERNAL_ERROR': (500, {None}), 'INVALID_RECEIPT': (400, {'through'})}

def wire_error(status, data):
    if exact(data, 'error') and exact(data['error'], 'code message field'):
        e = data['error']
        if isinstance(e['code'], str) and e['code'] in ERRORS:
            expected, fields = ERRORS[e['code']]
            if status == expected and isinstance(e['message'], str) and e['message'] and (e['field'] is None or isinstance(e['field'], str)) and e['field'] in fields:
                return ClientError(e['code'], e['message'])
    return ClientError('HTTP_ERROR', 'Server returned HTTP %s; check the server and retry.' % status)

class Transport:
    def __init__(self, server):
        self.url = urlsplit(server)
        self.lock = threading.Lock()
        self.active = None
        self.active_socket = None
    @staticmethod
    def abort(conn):
        try:
            if conn.sock:
                conn.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()
    def cancel(self):
        with self.lock:
            if self.active_socket:
                try:
                    self.active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            if self.active:
                self.abort(self.active)
    def request(self, method, path, payload=None, timeout=5):
        conn = http.client.HTTPConnection(self.url.hostname, self.url.port or 80, timeout=timeout)
        with self.lock:
            self.active = conn
        expired = threading.Event()
        connected_socket = [None]
        def deadline():
            expired.set()
            if connected_socket[0]:
                try:
                    connected_socket[0].shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            self.abort(conn)
        timer = threading.Timer(timeout, deadline)
        timer.daemon = True
        timer.start()
        status = None
        try:
            body = None if payload is None else json.dumps(payload, ensure_ascii=True, allow_nan=False).encode('utf-8')
            conn.request(method, path, body=body, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Connection': 'close'})
            connected_socket[0] = conn.sock
            with self.lock:
                self.active_socket = conn.sock
            if expired.is_set():
                raise ClientError('TRANSPORT_ERROR', 'Request deadline expired.')
            response = conn.getresponse()
            status = response.status
            # A known permanent status is authoritative even with an invalid body.
            try:
                media = response.getheader('Content-Type', '').lower().replace(' ', '')
                require(media in ('application/json', 'application/json;charset=utf-8'))
                require(response.getheader('Content-Encoding') in (None, ''))
                raw = response.read(8 * 1024 * 1024 + 1)
                require(len(raw) <= 8 * 1024 * 1024)
                require(response.length in (None, 0), 'Incomplete HTTP response body.')
                data = parse_json(raw)
                require(not expired.is_set(), 'Response deadline expired.')
            except Exception as exc:
                if 400 <= status < 500 and status not in (408, 429):
                    return status, None
                if isinstance(exc, ClientError):
                    raise
                raise ClientError('PROTOCOL_ERROR', 'Invalid or incomplete JSON response.') from exc
            return status, data
        except ClientError:
            raise
        except (OSError, ValueError, http.client.HTTPException) as exc:
            if status is not None and 400 <= status < 500 and status not in (408, 429):
                return status, None
            raise ClientError('TRANSPORT_ERROR', 'Connection failed or timed out; check the server and reconnect.') from exc
        finally:
            timer.cancel()
            conn.close()
            with self.lock:
                if self.active is conn:
                    self.active = None
                    self.active_socket = None
