"""Retained, in-memory implementation of specs/PROTOCOL.md."""
import argparse
from collections import deque
import json
import mimetypes
import re
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

MAX_INT = 9007199254740991
NAME = re.compile(r"[a-z][a-z0-9_]{0,31}\Z", re.ASCII)
UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z", re.ASCII)


class Problem(Exception):
    def __init__(self, status, code, field=None):
        self.status, self.code, self.field = status, code, field


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError("nonfinite JSON token")


def validate(data):
    if not isinstance(data, dict) or set(data) != {"message_id", "sender", "recipient", "text"}:
        raise Problem(400, "INVALID_FIELDS")
    if not isinstance(data['message_id'], str) or not UUID.fullmatch(data['message_id']):
        raise Problem(400, "INVALID_MESSAGE_ID", "message_id")
    for field in ('sender', 'recipient'):
        if not isinstance(data[field], str) or not NAME.fullmatch(data[field]):
            raise Problem(400, "INVALID_USERNAME", field)
    if data['sender'] == data['recipient']:
        raise Problem(400, "SELF_SEND", "recipient")
    try:
        valid = isinstance(data['text'], str) and 1 <= len(data['text'].encode('utf-8')) <= 4096
    except UnicodeEncodeError:
        valid = False
    if not valid:
        raise Problem(400, "INVALID_TEXT", "text")


class Store:
    def __init__(self, clock=None):
        self.lock = threading.Lock()
        self.streams = {}
        self.receipts = {}
        self.recent = deque(maxlen=200)
        self.clock = clock or time.monotonic
        self.users = {}
        self.acknowledged = {}
        self.explicit_offline = set()

    def send(self, data):
        validate(data)
        key = (data['sender'], data['message_id'])
        with self.lock:
            old = self.receipts.get(key)
            if old:
                if old['recipient'] != data['recipient'] or old['text'] != data['text']:
                    raise Problem(409, 'IDEMPOTENCY_CONFLICT', 'message_id')
                message, status = old, 200
            else:
                stream = self.streams.setdefault(data['recipient'], [])
                if len(stream) >= MAX_INT:
                    raise Problem(503, 'SEQUENCE_EXHAUSTED')
                message = dict(data, sequence=len(stream) + 1)
                stream.append(message)
                self.receipts[key] = message
                self.recent.append(message)
                status = 201
            self.users.setdefault(data['sender'], None)
            self.users.setdefault(data['recipient'], None)
            return status, {k: message[k] for k in ('message_id', 'sender', 'recipient', 'sequence')}

    def _directory_locked(self):
        now = self.clock()
        return [{'username': name, 'online': name not in self.explicit_offline and seen is not None and now - seen < 15}
                for name, seen in sorted(self.users.items())]

    def announce(self, data):
        if not isinstance(data, dict) or set(data) != {'username'}:
            raise Problem(400, 'INVALID_FIELDS')
        name = data['username']
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise Problem(400, 'INVALID_USERNAME', 'username')
        with self.lock:
            if name not in self.explicit_offline:
                self.users[name] = self.clock()
        return {'username': name}

    def presence(self, data):
        if not isinstance(data, dict) or set(data) != {'username', 'online'}:
            raise Problem(400, 'INVALID_FIELDS')
        name, online = data['username'], data['online']
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise Problem(400, 'INVALID_USERNAME', 'username')
        if type(online) is not bool:
            raise Problem(400, 'INVALID_PRESENCE', 'online')
        with self.lock:
            if online:
                self.explicit_offline.discard(name)
                self.users[name] = self.clock()
            else:
                self.explicit_offline.add(name)
                self.users[name] = None
        return {'username': name, 'online': online}

    def directory(self):
        with self.lock:
            return {'users': self._directory_locked()}

    def acknowledge(self, data):
        if not isinstance(data, dict) or set(data) != {'recipient', 'through'}:
            raise Problem(400, 'INVALID_FIELDS')
        recipient, through = data['recipient'], data['through']
        if not isinstance(recipient, str) or not NAME.fullmatch(recipient):
            raise Problem(400, 'INVALID_USERNAME', 'recipient')
        if type(through) not in (int, float) or not 0 <= through <= MAX_INT or int(through) != through:
            raise Problem(400, 'INVALID_RECEIPT', 'through')
        through = int(through)
        with self.lock:
            if through > len(self.streams.get(recipient, [])):
                raise Problem(409, 'CURSOR_INVALID', 'through')
            self.users.setdefault(recipient, None)
            self.acknowledged[recipient] = max(self.acknowledged.get(recipient, 0), through)
            return {'recipient': recipient, 'through': self.acknowledged[recipient]}

    def snapshot(self, selected_user=None):
        with self.lock:
            activity = {'sent': [], 'received': [], 'queued': []}
            if selected_user in self.users:
                for message in self.receipts.values():
                    state = 'received' if message['sequence'] <= self.acknowledged.get(message['recipient'], 0) else 'queued'
                    if message['sender'] == selected_user:
                        activity['sent'].append(dict(message, state=state))
                    if message['recipient'] == selected_user:
                        activity[state].append(dict(message, state=state))
            return dict(message_count=len(self.receipts), messages=[dict(m) for m in self.recent],
                        users=self._directory_locked(), activity=activity)

    def receive(self, recipient, after):
        with self.lock:
            stream = self.streams.get(recipient, [])
            if after > len(stream):
                raise Problem(409, 'CURSOR_INVALID', 'after')
            messages = stream[after:after + 100]
            return {'messages': messages, 'next_after': messages[-1]['sequence'] if messages else after}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, static_dir, clock=None):
        self.store = Store(clock)
        self.monitor_lock = threading.Lock()
        self.responses = 0
        self.errors = 0
        self.recent_responses = deque(maxlen=200)
        self.connection_lock = threading.Lock()
        self.connections = set()
        self.static_dir = Path(static_dir).resolve()
        super().__init__(address, Handler)


    def record_response(self, method, path, status):
        with self.monitor_lock:
            self.responses += 1
            self.errors += int(status >= 400)
            self.recent_responses.append((method, path, status))

    def snapshot(self, selected_user=None):
        data = self.store.snapshot(selected_user)
        with self.monitor_lock:
            data.update(responses=self.responses, errors=self.errors, requests=list(self.recent_responses))
        return data

    def process_request(self, request, address):
        with self.connection_lock:
            self.connections.add(request)
        try:
            super().process_request(request, address)
        except Exception:
            with self.connection_lock:
                self.connections.discard(request)
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            with self.connection_lock:
                self.connections.discard(request)

    def close_connections(self):
        with self.connection_lock:
            connections = list(self.connections)
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def reply(self, status, value, mime='application/json; charset=utf-8', allow=None):
        body = json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode() if isinstance(value, dict) else value
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        if allow:
            self.send_header('Allow', allow)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)
        self.server.record_response(self.command, urlsplit(self.path).path, status)

    def length(self, required=False):
        values = self.headers.get_all('Content-Length', [])
        if self.headers.get_all('Transfer-Encoding') or len(values) > 1:
            raise Problem(400, 'INVALID_REQUEST')
        if not values:
            if required:
                raise Problem(400, 'INVALID_REQUEST')
            return 0
        if not re.fullmatch(r'[0-9]+', values[0], re.ASCII):
            raise Problem(400, 'INVALID_REQUEST')
        try:
            size = int(values[0])
        except ValueError:
            raise Problem(400, 'INVALID_REQUEST')
        if size > 32768:
            raise Problem(413, 'PAYLOAD_TOO_LARGE')
        return size

    def read_json(self):
        length = self.length(required=True)
        media = self.headers.get('Content-Type', '')
        if self.headers.get('Content-Encoding') or not re.fullmatch(r'application/json(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?\s*', media, re.I):
            raise Problem(415, 'UNSUPPORTED_MEDIA_TYPE')
        deadline = time.monotonic() + 5
        chunks = bytearray()
        while len(chunks) < length:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Problem(400, 'INVALID_REQUEST')
            self.connection.settimeout(remaining)
            chunk = self.rfile.read1(length - len(chunks))
            if not chunk:
                raise Problem(400, 'INVALID_REQUEST')
            chunks.extend(chunk)
        try:
            data = json.loads(chunks.decode('utf-8'), object_pairs_hook=pairs_unique, parse_constant=invalid_constant)
        except (ValueError, UnicodeError, RecursionError):
            raise Problem(400, 'INVALID_JSON')
        return data

    def dispatch(self):
        route = urlsplit(self.path)
        path = route.path
        routes = {'/api/v1/messages': ('GET', 'POST'), '/api/v1/users': ('GET', 'POST'),
                  '/api/v1/receipts': ('POST',), '/api/v1/presence': ('POST',), '/health': ('GET',)}
        if path in routes:
            allowed = routes[path]
            if self.command not in allowed:
                self.allowed = ', '.join(allowed)
                raise Problem(405, 'METHOD_NOT_ALLOWED')
            if path in ('/health', '/api/v1/users') or self.command == 'POST':
                if route.query:
                    raise Problem(400, 'INVALID_QUERY')
            if self.command == 'GET':
                if self.length():
                    raise Problem(400, 'INVALID_REQUEST')
                if path == '/health':
                    return self.reply(200, {'status': 'ok', 'protocol_version': 1})
                if path == '/api/v1/users':
                    return self.reply(200, self.server.store.directory())
                if re.search(r'%(?![0-9a-fA-F]{2})', route.query):
                    raise Problem(400, 'INVALID_QUERY')
                try:
                    pairs = parse_qsl(route.query, keep_blank_values=True, strict_parsing=True, encoding='utf-8', errors='strict')
                except (ValueError, UnicodeError):
                    raise Problem(400, 'INVALID_QUERY')
                if len(pairs) != 2 or {k for k, v in pairs} != {'recipient', 'after'}:
                    raise Problem(400, 'INVALID_QUERY')
                query = dict(pairs)
                if not NAME.fullmatch(query['recipient']):
                    raise Problem(400, 'INVALID_USERNAME', 'recipient')
                after = query['after']
                if not re.fullmatch(r'0|[1-9][0-9]*', after, re.ASCII) or len(after) > 16 or int(after) > MAX_INT:
                    raise Problem(400, 'INVALID_QUERY', 'after')
                return self.reply(200, self.server.store.receive(query['recipient'], int(after)))
            data = self.read_json()
            if path == '/api/v1/presence':
                return self.reply(200, self.server.store.presence(data))
            if path == '/api/v1/users':
                return self.reply(200, self.server.store.announce(data))
            if path == '/api/v1/receipts':
                return self.reply(200, self.server.store.acknowledge(data))
            status, receipt = self.server.store.send(data)
            return self.reply(status, receipt)
        if path.startswith('/api/'):
            raise Problem(404, 'NOT_FOUND')
        if self.command not in ('GET', 'HEAD'):
            self.allowed = 'GET, HEAD'
            raise Problem(405, 'METHOD_NOT_ALLOWED')
        try:
            decoded = unquote(path, encoding='utf-8', errors='strict')
            target = (self.server.static_dir / (decoded.lstrip('/') or 'index.html')).resolve()
            target.relative_to(self.server.static_dir)
            if not target.is_file():
                raise ValueError('missing file')
            body = target.read_bytes()
        except (ValueError, UnicodeError, OSError):
            return self.reply(404, b'Not found', 'text/plain; charset=utf-8')
        mime = {'.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html'}.get(target.suffix, mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        self.reply(200, body, mime)

    def handle_request(self):
        try:
            self._handle_request()
        except (BrokenPipeError, ConnectionResetError):
            # A GUI Stop may close a socket while an error response is written.
            pass

    def _handle_request(self):
        # Close each response: no unread body can become a subsequent request.
        self.close_connection = True
        self.allowed = None
        try:
            self.dispatch()
        except Problem as exc:
            self.reply(exc.status, {'error': {'code': exc.code, 'message': exc.code.replace('_', ' ').capitalize() + '.', 'field': exc.field}}, allow=self.allowed)
        except (TimeoutError, socket.timeout):
            self.reply(400, {'error': {'code': 'INVALID_REQUEST', 'message': 'Incomplete request body.', 'field': None}})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.reply(500, {'error': {'code': 'INTERNAL_ERROR', 'message': 'Server could not process the request.', 'field': None}})

    do_GET = do_POST = do_HEAD = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = handle_request

    def __getattr__(self, name):
        # BaseHTTPRequestHandler otherwise emits 501 before route-level validation.
        if name.startswith('do_'):
            return self.handle_request
        raise AttributeError(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=['127.0.0.1'], default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--static-dir', default='generated/typescript-web/dist')
    args = parser.parse_args()
    with Server((args.host, args.port), args.static_dir) as server:
        print(json.dumps({'event': 'ready', 'origin': f'http://{args.host}:{server.server_port}'}), flush=True)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
