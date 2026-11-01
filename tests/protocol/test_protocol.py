"""Independent HTTP assertions derived from PROTOCOL and AT-08/11/14."""
import concurrent.futures
import http.client
import json
import socket
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

from server.main import Server


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'index.html').write_text('<h1>Local</h1>')
        (self.root / 'main.js').write_text('export {};')
        self.server = Server(('127.0.0.1', 0), self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, method='GET', path='/health', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=7)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        conn.close()
        return result

    def send(self, data):
        status, headers, body = self.request('POST', '/api/v1/messages', json.dumps(data).encode(), {'Content-Type': 'application/json'})
        return status, json.loads(body)

    def payload(self, **changes):
        return dict({'message_id': str(uuid.uuid4()), 'sender': 'alice', 'recipient': 'bob', 'text': 'Hello'}, **changes)

    def error(self, response, status, code, field=None):
        actual, headers, body = response
        self.assertEqual(actual, status)
        value = json.loads(body)
        self.assertEqual(set(value), {'error'})
        self.assertEqual(set(value['error']), {'code', 'message', 'field'})
        self.assertEqual((value['error']['code'], value['error']['field']), (code, field))
        self.assertTrue(value['error']['message'])
        self.assertEqual(headers['Cache-Control'], 'no-store')

    def test_AT14_health_static_and_methods(self):
        status, headers, body = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {'status': 'ok', 'protocol_version': 1})
        self.assertEqual(self.request(path='/')[2], b'<h1>Local</h1>')
        self.assertIn('javascript', self.request(path='/main.js')[1]['Content-Type'])
        self.assertEqual(self.request('HEAD', '/')[2], b'')
        self.assertEqual(self.request(path='/absent')[0], 404)
        self.assertEqual(self.request(path='/../outside')[0], 404)
        (self.root / 'escape').symlink_to('/etc/passwd')
        self.assertEqual(self.request(path='/escape')[0], 404)
        self.error(self.request(path='/api/missing'), 404, 'NOT_FOUND')
        self.error(self.request('DELETE', '/api/v1/messages'), 405, 'METHOD_NOT_ALLOWED')
        self.error(self.request('TRACE', '/api/v1/messages'), 405, 'METHOD_NOT_ALLOWED')
        self.assertEqual(self.request('DELETE', '/api/v1/messages')[1]['Allow'], 'GET, POST')
        self.error(self.request(path='/health?extra=1'), 400, 'INVALID_QUERY')
        self.error(self.request('GET', '/health', b'x'), 400, 'INVALID_REQUEST')

    def test_AT08_replay_conflicts_and_sender_namespace(self):
        data = self.payload()
        code, first = self.send(data)
        self.assertEqual(code, 201)
        self.assertEqual(first, {k: data[k] for k in ('message_id', 'sender', 'recipient')} | {'sequence': 1})
        self.assertEqual(self.send(data), (200, first))
        for changed in (dict(data, text='different'), dict(data, recipient='carol')):
            code, body = self.send(changed)
            self.assertEqual((code, body['error']['code']), (409, 'IDEMPOTENCY_CONFLICT'))
        self.assertEqual(self.send(dict(data, sender='carol'))[1]['sequence'], 2)
        page = json.loads(self.request(path='/api/v1/messages?recipient=bob&after=0')[2])
        self.assertEqual(len(page['messages']), 2)

    def test_AT08_concurrent_retries(self):
        data = self.payload()
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.send(data), range(6)))
        self.assertEqual([s for s, _ in results].count(201), 1)
        self.assertEqual([s for s, _ in results].count(200), 5)
        self.assertTrue(all(r['sequence'] == 1 for _, r in results))

    def test_AT10_pagination_and_unregistered_recipient(self):
        for i in range(205):
            self.assertEqual(self.send(self.payload(text=str(i)))[0], 201)
        after = 0
        for count, last in [(100, 100), (100, 200), (5, 205), (0, 205)]:
            page = json.loads(self.request(path=f'/api/v1/messages?recipient=bob&after={after}')[2])
            self.assertEqual(set(page), {'messages', 'next_after'})
            self.assertEqual(len(page['messages']), count)
            self.assertEqual(page['next_after'], last)
            self.assertEqual([m['sequence'] for m in page['messages']], list(range(after + 1, last + 1)))
            after = last
        empty = json.loads(self.request(path='/api/v1/messages?recipient=carol&after=0')[2])
        self.assertEqual(empty, {'messages': [], 'next_after': 0})
        self.error(self.request(path='/api/v1/messages?recipient=bob&after=206'), 409, 'CURSOR_INVALID', 'after')

    def test_AT11_payload_limits_and_preservation(self):
        for text in [' ', '  한글 😀\nsecond line  ', 'a' * 4096, '😀' * 1024]:
            data = self.payload(text=text)
            self.assertEqual(self.send(data)[0], 201)
        for text in ['', 'a' * 4097, '😀' * 1025, '\ud800', None, 1, True]:
            code, body = self.send(self.payload(text=text))
            self.assertEqual((code, body['error']['code'], body['error']['field']), (400, 'INVALID_TEXT', 'text'))
        page = json.loads(self.request(path='/api/v1/messages?recipient=bob&after=0')[2])
        self.assertEqual(page['messages'][1]['text'], '  한글 😀\nsecond line  ')

    def test_AT11_name_id_and_schema_validation(self):
        for field, value, expected in [('sender', 'Alice', 'INVALID_USERNAME'), ('recipient', 'bob ', 'INVALID_USERNAME'), ('recipient', 'a' * 33, 'INVALID_USERNAME'), ('recipient', 'alice', 'SELF_SEND'), ('message_id', 'invalid', 'INVALID_MESSAGE_ID')]:
            code, body = self.send(self.payload(**{field: value}))
            self.assertEqual((code, body['error']['code'], body['error']['field']), (400, expected, field))
        for data in [[], {}, self.payload(extra=True)]:
            self.assertEqual(self.send(data)[1]['error']['code'], 'INVALID_FIELDS')
        self.assertEqual(self.send(self.payload(recipient='a' * 32))[0], 201)

    def test_AT14_queries(self):
        for query in ['', 'recipient=bob', 'recipient=bob&after=0&x=1', 'recipient=bob&recipient=bob', 'recipient=%zz&after=0', 'recipient=%ff&after=0']:
            self.error(self.request(path='/api/v1/messages?' + query), 400, 'INVALID_QUERY')
        for after in ['01', '-1', '1.5', '%20', '9007199254740992', '+0']:
            self.error(self.request(path='/api/v1/messages?recipient=bob&after=' + after), 400, 'INVALID_QUERY', 'after')
        self.error(self.request(path='/api/v1/messages?recipient=Bob&after=0'), 400, 'INVALID_USERNAME', 'recipient')

    def test_AT14_json_and_media(self):
        for raw in [b'{', b'\xff', b'\xef\xbb\xbf{}', b'{"x":1,"x":2}', b'{"text":NaN}']:
            self.error(self.request('POST', '/api/v1/messages', raw, {'Content-Type': 'application/json'}), 400, 'INVALID_JSON')
        self.error(self.request('POST', '/api/v1/messages', b'{}', {'Content-Type': 'text/plain'}), 415, 'UNSUPPORTED_MEDIA_TYPE')
        self.error(self.request('POST', '/api/v1/messages', b'{}', {'Content-Type': 'application/json', 'Content-Encoding': 'gzip'}), 415, 'UNSUPPORTED_MEDIA_TYPE')
        self.error(self.request('POST', '/api/v1/messages', b'x' * 32769, {'Content-Type': 'application/json'}), 413, 'PAYLOAD_TOO_LARGE')

    def test_AT14_raw_framing(self):
        for headers, body in [(b'', b''), (b'Content-Length: 2\r\nContent-Length: 2\r\n', b'{}'), (b'Content-Length: -1\r\n', b''), (b'Transfer-Encoding: chunked\r\n', b'0\r\n\r\n'), (b'Content-Length: 10\r\n', b'{}')]:
            with socket.create_connection(('127.0.0.1', self.server.server_port), timeout=7) as sock:
                sock.sendall(b'POST /api/v1/messages HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n' + headers + b'\r\n' + body)
                sock.shutdown(socket.SHUT_WR)
                response = http.client.HTTPResponse(sock)
                response.begin()
                self.assertEqual(response.status, 400)
                self.assertEqual(json.loads(response.read())['error']['code'], 'INVALID_REQUEST')
