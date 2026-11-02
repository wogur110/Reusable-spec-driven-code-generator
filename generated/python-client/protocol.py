"""Strict wire values and deadline-bounded, direct loopback HTTP."""
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
    def object(self):
        return {'code': self.code, 'message': self.message}

def require(ok, message='Invalid server response.'):
    if not ok:
        raise ClientError('PROTOCOL_ERROR', message)

def exact(value, keys):
    return isinstance(value, dict) and set(value) == set(keys.split())

def integer(v, minimum=0):
    return type(v) in (int, float) and minimum <= v <= MAX and v == int(v)

def username(v):
    return isinstance(v, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,31}', v, flags=re.ASCII) is not None

def valid_text(v):
    try:
        return isinstance(v, str) and 1 <= len(v.encode('utf-8')) <= 4096
    except UnicodeError:
        return False

def message_id(v):
    return isinstance(v, str) and re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', v) is not None

def message(v):
    return (exact(v, 'message_id sender recipient text sequence') and
            message_id(v['message_id']) and username(v['sender']) and username(v['recipient']) and
            v['sender'] != v['recipient'] and valid_text(v['text']) and integer(v['sequence'], 1))

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
        if ':' in host:
            host = '[' + host + ']'
        return 'http://' + host + ((':' + str(port)) if port and port != 80 else '')
    except (ValueError, TypeError):
        raise ClientError('INVALID_COMMAND', 'Server must be an HTTP localhost or literal loopback origin without path, credentials, query or fragment.')

def loads(raw, duplicates=False):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Duplicate JSON member')
            result[k] = v
        return result
    def invalid(v):
        raise ValueError('Nonfinite JSON number')
    return json.loads(raw.decode('utf-8'), parse_constant=invalid, object_pairs_hook=pairs if duplicates else None)

ERRORS = {
    'INVALID_REQUEST': (400, None), 'INVALID_JSON': (400, None), 'INVALID_FIELDS': (400, None),
    'INVALID_MESSAGE_ID': (400, 'message_id'), 'INVALID_USERNAME': (400, ('sender','recipient','username')),
    'INVALID_RECEIPT': (400,'through'), 'INVALID_PRESENCE': (400,'online'), 'SELF_SEND': (400,'recipient'),
    'INVALID_TEXT': (400,'text'), 'INVALID_QUERY': (400, (None,'after')), 'NOT_FOUND': (404,None),
    'METHOD_NOT_ALLOWED': (405,None), 'IDEMPOTENCY_CONFLICT': (409,'message_id'),
    'CURSOR_INVALID': (409, ('after','through')), 'PAYLOAD_TOO_LARGE': (413,None),
    'UNSUPPORTED_MEDIA_TYPE': (415,None), 'SEQUENCE_EXHAUSTED': (503,None), 'INTERNAL_ERROR': (500,None)
}

def wire_error(status, body):
    if exact(body, 'error') and exact(body['error'], 'code message field'):
        e = body['error']
        rule = ERRORS.get(e['code']) if isinstance(e['code'], str) else None
        if rule and status == rule[0] and isinstance(e['message'], str) and e['message'] and (e['field'] in rule[1] if isinstance(rule[1],tuple) else e['field'] == rule[1]):
            return ClientError(e['code'], e['message'])
    return ClientError('HTTP_ERROR', 'Server returned HTTP %s; retry or inspect the server.' % status)

class Transport:
    def __init__(self, base):
        self.base = urlsplit(base)

    def request(self, method, path, payload=None, timeout=5):
        conn = http.client.HTTPConnection(self.base.hostname, self.base.port or 80, timeout=timeout)
        expired = threading.Event()
        active_socket = [None]
        def expire():
            expired.set()
            # HTTPConnection detaches its socket for Connection: close responses.
            # Retain the actual socket so the total deadline also bounds body reads.
            sock = active_socket[0] or conn.sock
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass
        timer = threading.Timer(timeout, expire)
        timer.daemon = True
        timer.start()
        status = None
        try:
            raw = None if payload is None else json.dumps(payload, ensure_ascii=True, allow_nan=False).encode('utf-8')
            headers = {'Accept':'application/json', 'Connection':'close'}
            if raw is not None:
                headers['Content-Type'] = 'application/json; charset=utf-8'
            conn.request(method, path, body=raw, headers=headers)
            active_socket[0] = conn.sock
            if expired.is_set():
                expire()
                raise ClientError('TRANSPORT_ERROR', 'Request exceeded its total deadline; will retry.')
            response = conn.getresponse()
            status = response.status
            media = response.getheader('Content-Type', '').lower().replace(' ', '')
            encoding = response.getheader('Content-Encoding')
            try:
                data = response.read(4 * 1024 * 1024 + 1)
                require(len(data) <= 4 * 1024 * 1024, 'Server response is too large.')
                require(response.length in (None, 0), 'Incomplete response body.')
                require(media in ('application/json','application/json;charset=utf-8') and encoding is None, 'Expected UTF-8 JSON without content encoding.')
                body = loads(data)
            except (ValueError, UnicodeError, ClientError, OSError, http.client.HTTPException) as exc:
                if 400 <= status < 600:
                    return status, None
                raise ClientError('PROTOCOL_ERROR', 'Invalid or incomplete JSON response: ' + str(exc))
            if expired.is_set():
                raise ClientError('TRANSPORT_ERROR', 'Request exceeded its total deadline; will retry.')
            return status, body
        except ClientError:
            raise
        except (OSError, http.client.HTTPException) as exc:
            if status is not None and 400 <= status < 500:
                return status, None
            raise ClientError('TRANSPORT_ERROR', 'Cannot reach server: ' + str(exc))
        finally:
            timer.cancel()
            conn.close()
