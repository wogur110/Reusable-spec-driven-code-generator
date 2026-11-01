"""Direct loopback HTTP with absolute request deadlines and strict wire validation."""
import http.client
import json
import socket
import threading
import time
from urllib.parse import urlsplit
from model import ClientError, exact, require

ERRORS = {
    'INVALID_REQUEST': (400, None), 'INVALID_JSON': (400, None),
    'INVALID_FIELDS': (400, None), 'INVALID_MESSAGE_ID': (400, 'message_id'),
    'INVALID_USERNAME': (400, ('sender', 'recipient', 'username')),
    'SELF_SEND': (400, 'recipient'), 'INVALID_TEXT': (400, 'text'),
    'INVALID_QUERY': (400, (None, 'after')), 'NOT_FOUND': (404, None),
    'METHOD_NOT_ALLOWED': (405, None), 'IDEMPOTENCY_CONFLICT': (409, 'message_id'),
    'CURSOR_INVALID': (409, ('after', 'through')), 'PAYLOAD_TOO_LARGE': (413, None),
    'UNSUPPORTED_MEDIA_TYPE': (415, None), 'SEQUENCE_EXHAUSTED': (503, None),
    'INTERNAL_ERROR': (500, None), 'INVALID_RECEIPT': (400, 'through'),
    'INVALID_PRESENCE': (400, 'online')}

def decode(raw, headers):
    media = headers.get('Content-Type', '').lower().split(';')
    require(media[0].strip() == 'application/json' and all(x.strip() == 'charset=utf-8' for x in media[1:]))
    require(not headers.get('Content-Encoding'))
    try:
        return json.loads(raw.decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (UnicodeError, ValueError):
        raise ClientError('PROTOCOL_ERROR', 'Malformed UTF-8 JSON response.')

def request(server, method, path, data=None, timeout=5):
    p = urlsplit(server)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=timeout)
    sock = None
    timer = None
    status = None
    deadline = time.monotonic() + timeout
    expired = threading.Event()
    def expire():
        expired.set()
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
    try:
        conn.connect()
        sock = conn.sock
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Request deadline expired.')
        sock.settimeout(remaining)
        timer = threading.Timer(remaining, expire)
        timer.daemon = True
        timer.start()
        body = None if data is None else json.dumps(data, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
        conn.request(method, path, body=body, headers={'Content-Type': 'application/json', 'Connection': 'close'} if body is not None else {'Connection': 'close'})
        response = conn.getresponse()
        status = response.status
        raw = response.read(8 * 1024 * 1024 + 1)
        if expired.is_set() or time.monotonic() >= deadline:
            raise TimeoutError('Request deadline expired.')
        if response.length is not None and response.length > 0 and len(raw) <= 8 * 1024 * 1024:
            raise http.client.IncompleteRead(raw, response.length)
        require(len(raw) <= 8 * 1024 * 1024, 'Response exceeds the allowed buffer.')
        if status not in (200, 201):
            permanent = 400 <= status < 500 and status not in (408, 429)
            code, message = 'HTTP_ERROR', 'Server returned HTTP ' + str(status) + '.'
            try:
                obj = decode(raw, response.headers)
                exact(obj, ('error',))
                err = obj['error']
                exact(err, ('code', 'message', 'field'))
                mapping = ERRORS.get(err['code'])
                require(mapping is not None and mapping[0] == status and isinstance(err['message'], str) and bool(err['message']))
                fields = mapping[1] if isinstance(mapping[1], tuple) else (mapping[1],)
                require(err['field'] in fields)
                code, message = err['code'], err['message']
            except (ClientError, TypeError):
                pass
            if not (400 <= status <= 599):
                code = 'PROTOCOL_ERROR'
            raise ClientError(code, message, permanent)
        return status, decode(raw, response.headers)
    except ClientError:
        raise
    except (OSError, http.client.HTTPException, ValueError) as e:
        if status is not None and 400 <= status < 500 and status not in (408, 429):
            raise ClientError('HTTP_ERROR', 'Server returned HTTP ' + str(status) + '.', True)
        raise ClientError('TRANSPORT_ERROR', 'Connection failed; queued messages will retry: ' + str(e))
    finally:
        if timer:
            timer.cancel()
        conn.close()
        if sock:
            sock.close()
