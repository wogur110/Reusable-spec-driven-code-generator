"""Drive the real Python application's specified JSON-lines interface."""
import json
import os
import queue
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name)
        self.process = None
        self.start()

    def start(self):
        self.process = subprocess.Popen([sys.executable, str(ROOT/'generated/python-client/main.py'), '--machine', '--transport', 'offline', '--state-dir', str(self.state)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        self.lines = queue.Queue()
        def reader():
            for line in self.process.stdout:
                self.lines.put(json.loads(line))
        threading.Thread(target=reader, daemon=True).start()
        ready = self.lines.get(timeout=5)
        self.assertEqual(ready['event'], 'ready')

    def command(self, command, **params):
        self.process.stdin.write(json.dumps({'id': 'q', 'command': command, **params}, ensure_ascii=True) + '\n')
        self.process.stdin.flush()
        while True:
            result = self.lines.get(timeout=5)
            if result.get('type') == 'result':
                self.assertEqual(result['id'], 'q')
                return result

    def close(self):
        if self.process and self.process.poll() is None:
            self.command('quit')
            self.assertEqual(self.process.wait(timeout=6), 0)
        if self.process:
            for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
                stream.close()
        self.process = None

    def tearDown(self):
        try:
            self.close()
        finally:
            self.temp.cleanup()

    def test_AT01_AT09_identity_queue_and_restart(self):
        self.assertFalse(self.command('login', username='Alice')['ok'])
        self.assertTrue(self.command('login', username='alice')['ok'])
        self.assertTrue(self.command('login', username='alice')['ok'])
        self.assertEqual(self.command('login', username='bob')['error']['code'], 'IDENTITY_LOCKED')
        sent = self.command('send', recipient='bob', text='  한글 😀\nsecond line  ')['data']
        before = self.command('outbox')['data']
        self.assertEqual(before['messages'][0]['state'], 'queued')
        self.assertEqual(before['messages'][0]['message_id'], sent['message_id'])
        self.close(); self.start()
        self.assertEqual(self.command('status')['data']['username'], 'alice')
        self.assertEqual(self.command('outbox')['data'], before)

    def test_AT11_invalid_commands_and_text(self):
        self.assertFalse(self.command('send', recipient='bob', text='a')['ok'])
        self.command('login', username='alice')
        for recipient, text in [('alice', 'x'), ('Bob', 'x'), ('bob', ''), ('bob', 'a'*4097), ('bob', '\ud800')]:
            self.assertFalse(self.command('send', recipient=recipient, text=text)['ok'])
        self.assertEqual(self.command('outbox')['data'], {'messages': []})
        self.assertTrue(self.command('send', recipient='bob', text=' ')['ok'])
        self.assertFalse(self.command('unknown')['ok'])

    def test_AT01_AT16_reset_and_unsupported_version(self):
        self.command('login', username='alice'); self.close()
        unrelated = self.state/'keep.txt'; unrelated.write_text('keep')
        cmd = [sys.executable, str(ROOT/'generated/python-client/main.py'), '--state-dir', str(self.state), '--reset-state']
        self.assertNotEqual(subprocess.run(cmd, capture_output=True, timeout=6).returncode, 0)
        db = self.state/'messages.sqlite3'
        self.assertTrue(db.exists())
        with sqlite3.connect(db) as connection:
            connection.execute('PRAGMA user_version=999')
        before = db.read_bytes()
        result = subprocess.run([sys.executable, str(ROOT/'generated/python-client/main.py'), '--state-dir', str(self.state), '--machine'], capture_output=True, timeout=6)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(db.read_bytes(), before)
        self.assertEqual(subprocess.run(cmd+['--yes'], capture_output=True, timeout=6).returncode, 0)
        self.assertFalse(db.exists()); self.assertEqual(unrelated.read_text(), 'keep')

    def test_AT16_origin_mismatch_preserves_store(self):
        self.command('login', username='alice'); self.close()
        db = self.state/'messages.sqlite3'; before = db.read_bytes()
        result = subprocess.run([sys.executable, str(ROOT/'generated/python-client/main.py'), '--state-dir', str(self.state), '--server', 'http://127.0.0.1:8766', '--machine'], capture_output=True, timeout=6)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(db.read_bytes(), before)
