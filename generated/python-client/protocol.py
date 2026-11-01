"""Wire validation and bounded, direct loopback HTTP transport."""
import http.client
import ipaddress
import json
import re
import socket
import threading
from urllib.parse import urlsplit

MAX = 9007199254740991

class Failure(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
    def data(self):
        return {'code': self.code, 'message': self.message}

def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise Failure('PROTOCOL_ERROR', 'Unexpected response fields.')

def integer(value, low=0):
    return type(value) in (int, float) and low <= value <= MAX and int(value) == value

def username(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value, re.ASCII):
        raise Failure('INVALID_USERNAME', 'Use 1–32 lowercase ASCII letters, digits or underscores, starting with a letter.')
    return value

def message_text(value):
    try:
        valid = isinstance(value, str) and 1 <= len(value.encode('utf-8')) <= 4096
    except UnicodeError:
        valid = False
    if not valid:
        raise Failure('INVALID_TEXT', 'Text must contain 1–4096 UTF-8 bytes without lone surrogates.')

def message_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', value):
        raise Failure('PROTOCOL_ERROR', 'Invalid message ID.')

def origin(value):
    try:
        p = urlsplit(value)
        host = p.hostname
        if p.scheme != 'http' or not host or p.username is not None or p.password is not None or p.path or p.query or p.fragment or '?' in value or '#' in value:
            raise ValueError()
        if host.lower() != 'localhost' and not ipaddress.ip_address(host).is_loopback:
            raise ValueError()
        port = p.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError()
        host = host.lower()
        return 'http://' + ('[' + host + ']' if ':' in host else host) + (':' + str(port) if port and port != 80 else '')
    except (ValueError, TypeError):
        raise Failure('INVALID_COMMAND', 'Server must be an HTTP loopback origin without credentials, path, query or fragment.')

def loads(raw, duplicates=False):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON member')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)), object_pairs_hook=pairs if duplicates else dict)

ERRORS = {
 'INVALID_REQUEST': (400, {None}), 'INVALID_JSON': (400, {None}),
 'INVALID_FIELDS': (400, {None}), 'INVALID_MESSAGE_ID': (400, {'message_id'}),
 'INVALID_USERNAME': (400, {'sender','recipient'}), 'SELF_SEND': (400, {'recipient'}),
 'INVALID_TEXT': (400, {'text'}), 'INVALID_QUERY': (400, {None,'after'}),
 'NOT_FOUND': (404, {None}), 'METHOD_NOT_ALLOWED': (405, {None}),
 'IDEMPOTENCY_CONFLICT': (409, {'message_id'}), 'CURSOR_INVALID': (409, {'after'}),
 'PAYLOAD_TOO_LARGE': (413, {None}), 'UNSUPPORTED_MEDIA_TYPE': (415, {None}),
 'SEQUENCE_EXHAUSTED': (503, {None}), 'INTERNAL_ERROR': (500, {None})}

def wire_error(status, value):
    try:
        exact(value, 'error')
        e = value['error']
        exact(e, 'code message field')
        expected, fields = ERRORS[e['code']]
        if expected != status or e['field'] not in fields or not isinstance(e['message'], str) or not e['message']:
            return None
        return Failure(e['code'], e['message'])
    except (Failure, KeyError, TypeError):
        return None

def request(server, method, path, payload=None):
    p = urlsplit(server)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=5)
    expired = threading.Event()
    active_socket = [None]
    def abort():
        expired.set()
        sock = active_socket[0] or conn.sock
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
    timer = threading.Timer(5, abort)
    timer.daemon = True
    timer.start()
    status = None
    try:
        body = None if payload is None else json.dumps(payload, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
        conn.connect()
        active_socket[0] = conn.sock
        if expired.is_set():
            raise OSError('Request deadline exceeded')
        conn.request(method, path, body, {'Content-Type': 'application/json', 'Cache-Control': 'no-store'})
        response = conn.getresponse()
        status = response.status
        media = response.getheader('Content-Type', '').lower().replace(' ', '')
        if media not in ('application/json', 'application/json;charset=utf-8') or response.getheader('Content-Encoding'):
            raise Failure('PROTOCOL_ERROR', 'Expected UTF-8 application/json without content encoding.')
        raw = response.read(4 * 1024 * 1024 + 1)
        if expired.is_set():
            raise OSError('Request deadline exceeded')
        if len(raw) > 4 * 1024 * 1024:
            raise Failure('PROTOCOL_ERROR', 'Response exceeds supported page size.')
        try:
            data = loads(raw)
        except (ValueError, UnicodeError):
            raise Failure('PROTOCOL_ERROR', 'Response is not valid UTF-8 JSON.')
        return status, data, None
    except Failure as e:
        return status, None, e
    except (OSError, http.client.HTTPException) as e:
        return status, None, Failure('TRANSPORT_ERROR', 'Request failed; retrying: ' + str(e))
    finally:
        timer.cancel()
        conn.close()

def receipt(value, sent):
    exact(value, 'message_id sender recipient sequence')
    if any(value[k] != sent[k] for k in ('message_id','sender','recipient')) or not integer(value['sequence'], 1):
        raise Failure('PROTOCOL_ERROR', 'Receipt does not match the queued message.')
    return int(value['sequence'])

def page(value, user, cursor):
    try:
        exact(value, 'messages next_after')
        rows = value['messages']
        if not isinstance(rows, list) or len(rows) > 100 or not integer(value['next_after']):
            raise ValueError()
        keys = set()
        for index, row in enumerate(rows):
            exact(row, 'message_id sender recipient text sequence')
            message_id(row['message_id'])
            username(row['sender'])
            username(row['recipient'])
            message_text(row['text'])
            key = (row['sender'], row['message_id'])
            if key in keys or row['recipient'] != user or row['sender'] == user or not integer(row['sequence'], 1) or row['sequence'] != cursor + index + 1:
                raise ValueError()
            keys.add(key)
        if value['next_after'] != cursor + len(rows):
            raise ValueError()
        return rows, int(value['next_after'])
    except (ValueError, KeyError, TypeError, Failure):
        raise Failure('PROTOCOL_ERROR', 'Invalid incoming page; inbox and cursor were preserved.')
