"""Wire validation and deadline-bounded, direct loopback HTTP transport."""
import http.client
import ipaddress
import json
import re
import socket
import threading
from urllib.parse import urlsplit

MAX_INT = 9007199254740991

class ClientError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

    def data(self):
        return {"code": self.code, "message": self.message}


def require(condition, message="Invalid server response."):
    if not condition:
        raise ClientError("PROTOCOL_ERROR", message)


def exact(value, keys):
    return isinstance(value, dict) and set(value) == set(keys.split())


def integer(value, low=0):
    return type(value) in (int, float) and low <= value <= MAX_INT and int(value) == value


def username(value):
    return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,31}", value, re.ASCII) is not None


def message_id(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value) is not None


def valid_text(value):
    try:
        return isinstance(value, str) and 1 <= len(value.encode("utf-8")) <= 4096
    except UnicodeError:
        return False


def validate_name(value):
    if not username(value):
        raise ClientError("INVALID_USERNAME", "Use 1–32 lowercase ASCII letters, digits or underscores, starting with a letter.")


def validate_text(value):
    if not valid_text(value):
        raise ClientError("INVALID_TEXT", "Enter 1–4096 UTF-8 bytes of Unicode scalar text.")


def origin(value):
    try:
        u = urlsplit(value)
        host = u.hostname
        if u.scheme != "http" or not host or u.username is not None or u.password is not None or u.path or u.query or u.fragment or '?' in value or '#' in value:
            raise ValueError()
        if host.lower() != "localhost" and not ipaddress.ip_address(host).is_loopback:
            raise ValueError()
        port = u.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError()
        if u.netloc.endswith(':'):
            raise ValueError()
        host = host.lower()
        name = '[' + host + ']' if ':' in host else host
        return 'http://' + name + (':' + str(port) if port not in (None, 80) else '')
    except (ValueError, TypeError):
        raise ClientError("INVALID_COMMAND", "Server must be an HTTP localhost or literal loopback origin without a path.")


def parse_json(raw, strict=False):
    def bad_constant(value):
        raise ValueError("Nonfinite number")
    def pairs(items):
        result = {}
        for key, val in items:
            if key in result:
                raise ValueError("Duplicate member")
            result[key] = val
        return result
    text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
    return json.loads(text, parse_constant=bad_constant, object_pairs_hook=pairs if strict else None)


def receipt(value, sent):
    require(exact(value, 'message_id sender recipient sequence'))
    require(all(value[k] == sent[k] for k in ('message_id', 'sender', 'recipient')) and integer(value['sequence'], 1))
    return int(value['sequence'])


def page(value, who, after):
    require(exact(value, 'messages next_after'))
    rows = value['messages']
    require(isinstance(rows, list) and len(rows) <= 100 and integer(value['next_after']))
    seen = set()
    for index, row in enumerate(rows):
        require(exact(row, 'message_id sender recipient text sequence'))
        require(message_id(row['message_id']) and username(row['sender']) and username(row['recipient']))
        require(row['recipient'] == who and row['sender'] != who and valid_text(row['text']))
        require(integer(row['sequence'], 1) and row['sequence'] == after + index + 1)
        key = (row['sender'], row['message_id'])
        require(key not in seen)
        seen.add(key)
    require(value['next_after'] == after + len(rows))
    return rows, int(value['next_after'])

ERRORS = {
    'INVALID_REQUEST': (400, {None}), 'INVALID_JSON': (400, {None}),
    'INVALID_FIELDS': (400, {None}), 'INVALID_MESSAGE_ID': (400, {'message_id'}),
    'INVALID_USERNAME': (400, {'sender', 'recipient'}), 'SELF_SEND': (400, {'recipient'}),
    'INVALID_TEXT': (400, {'text'}), 'INVALID_QUERY': (400, {None, 'after'}),
    'NOT_FOUND': (404, {None}), 'METHOD_NOT_ALLOWED': (405, {None}),
    'IDEMPOTENCY_CONFLICT': (409, {'message_id'}), 'CURSOR_INVALID': (409, {'after'}),
    'PAYLOAD_TOO_LARGE': (413, {None}), 'UNSUPPORTED_MEDIA_TYPE': (415, {None}),
    'SEQUENCE_EXHAUSTED': (503, {None}), 'INTERNAL_ERROR': (500, {None})}


def server_error(status, value):
    if exact(value, 'error') and exact(value['error'], 'code message field'):
        err = value['error']
        code = err['code']
        if isinstance(code, str) and code in ERRORS:
            expected, fields = ERRORS[code]
            if status == expected and (err['field'] is None or isinstance(err['field'], str)) and err['field'] in fields and isinstance(err['message'], str) and err['message']:
                try:
                    err['message'].encode('utf-8')
                    return ClientError(code, err['message'])
                except UnicodeError:
                    pass
    return ClientError('HTTP_ERROR', 'Server returned HTTP %s; check the server and retry or submit a corrected message.' % status)


def request(server, method, path, payload=None):
    """A timer shuts down the socket even when headers/body arrive as a slow drip."""
    u = urlsplit(server)
    connection = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=5)
    sock = [None]
    expired = threading.Event()
    def timeout():
        expired.set()
        s = sock[0] or connection.sock
        if s is not None:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()
    timer = threading.Timer(5, timeout)
    timer.daemon = True
    status = None
    timer.start()
    try:
        connection.connect()
        sock[0] = connection.sock
        if expired.is_set():
            raise TimeoutError()
        body = None if payload is None else json.dumps(payload, ensure_ascii=True, allow_nan=False).encode('utf-8')
        connection.request(method, path, body=body, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'Connection': 'close'})
        response = connection.getresponse()
        status = response.status
        raw = response.read(4 * 1024 * 1024 + 1)
        if expired.is_set():
            raise TimeoutError()
        require(len(raw) <= 4 * 1024 * 1024, 'Response exceeds the 4 MiB receive limit.')
        media = response.getheader('Content-Type', '')
        require(re.fullmatch(r'\s*application/json\s*(?:;\s*charset\s*=\s*(?:utf-8|"utf-8")\s*)?', media, re.I) is not None, 'Expected UTF-8 application/json.')
        require(response.getheader('Content-Encoding') is None, 'Unsupported content encoding.')
        try:
            value = parse_json(raw)
        except (ValueError, UnicodeError, RecursionError):
            raise ClientError('PROTOCOL_ERROR', 'Malformed UTF-8 JSON response.')
        return status, value
    except (OSError, http.client.HTTPException, ClientError, ValueError) as exc:
        # A known permanent status takes precedence over an unreadable body.
        if status is not None and 400 <= status < 600:
            return status, None
        if isinstance(exc, ClientError):
            raise
        raise ClientError('TRANSPORT_ERROR', 'Request failed or exceeded five seconds; check the local server and connection.') from exc
    finally:
        timer.cancel()
        connection.close()
        if sock[0] is not None:
            sock[0].close()
