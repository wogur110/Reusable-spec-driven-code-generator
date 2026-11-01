#!/usr/bin/env python3
"""Independent standard-library messaging CLI and JSON-lines interface."""
import sys
sys.dont_write_bytecode = True
import argparse
import json
import threading
from pathlib import Path
from protocol import ClientError, origin, parse_json, exact
from storage import Store
from client import Client

PARAMETERS = {'login': ('username',), 'send': ('recipient', 'text'), 'inbox': (),
              'outbox': (), 'status': (), 'transport': ('mode',), 'quit': ()}
HELP = ('Commands: send RECIPIENT TEXT | send-json RECIPIENT "JSON string" | inbox | outbox | '
        'status | transport online | transport offline | help | quit.\n'
        'Accepted by server does not mean delivered or read. Reset stopped stores explicitly after a server restart.')

class Presentation:
    def __init__(self, machine):
        self.machine = machine
        self.lock = threading.RLock()
        self.revision = 0
        self.client = None
        self.seen_incoming = set()
        self.seen_outgoing = {}
        self.prompt = ''
        self.previous_error = None

    def error(self, error):
        if not self.machine and error != self.previous_error:
            self.previous_error = error
            self.human(error['code'] + ': ' + error['message'])

    def emit(self, value):
        with self.lock:
            print(json.dumps(value, ensure_ascii=True, allow_nan=False), flush=True)

    def human(self, text):
        with self.lock:
            # readline owns the draft; redraw it after asynchronous notifications.
            if self.prompt and sys.stdin.isatty() and sys.stdout.isatty():
                try:
                    import readline
                    draft = readline.get_line_buffer()
                except ImportError:
                    draft = ''
                sys.stdout.write('\r\033[2K' + text + '\n' + self.prompt + draft)
                sys.stdout.flush()
            else:
                print(text, flush=True)

    def changed(self):
        with self.lock:
            self.revision += 1
            if self.machine:
                self.emit({'type': 'event', 'event': 'state_changed', 'revision': self.revision})
            elif self.client is not None:
                _, outgoing, incoming = self.client.store.snapshot()
                for row in incoming:
                    key = (row['sender'], row['message_id'])
                    if key not in self.seen_incoming:
                        self.seen_incoming.add(key)
                        self.human('From ' + row['sender'] + ': ' + row['text'])
                for row in outgoing:
                    marker = (row['state'], str(row['error']))
                    if self.seen_outgoing.get(row['message_id']) != marker:
                        self.seen_outgoing[row['message_id']] = marker
                        label = 'accepted by server' if row['state'] == 'accepted' else row['state']
                        self.human(row['message_id'] + ': ' + label + (' — ' + row['error']['message'] if row['error'] else ''))


def valid_id(value):
    return isinstance(value, str) and 1 <= len(value) <= 64 and value.isascii()


def machine_loop(client, output):
    stream = sys.stdin.buffer
    while not client.stop.is_set():
        raw = stream.readline(65537)
        if not raw:
            break
        ident = None
        try:
            if len(raw) > 65536:
                while not raw.endswith(b'\n'):
                    raw = stream.readline(65537)
                    if not raw:
                        break
                raise ClientError('INVALID_COMMAND', 'Input line exceeds 65536 bytes.')
            try:
                value = parse_json(raw, strict=True)
            except (ValueError, UnicodeError, RecursionError):
                raise ClientError('INVALID_COMMAND', 'Expected one strict UTF-8 JSON object.')
            if isinstance(value, dict) and valid_id(value.get('id')):
                ident = value['id']
            if ident is None or not isinstance(value.get('command'), str):
                raise ClientError('INVALID_COMMAND', 'A nonempty ASCII id and a command are required.')
            command = value['command']
            if command not in PARAMETERS or not exact(value, 'id command ' + ' '.join(PARAMETERS[command])):
                raise ClientError('INVALID_COMMAND', 'Unknown command or incorrect members.')
            if any(not isinstance(value[key], str) for key in PARAMETERS[command]):
                raise ClientError('INVALID_COMMAND', 'Command parameters must be strings.')
            data = client.operate(command, value)
            output.emit({'type': 'result', 'id': ident, 'ok': True, 'data': data})
        except ClientError as exc:
            output.emit({'type': 'result', 'id': ident, 'ok': False, 'error': exc.data()})


def human_loop(client, output):
    output.human('Server: ' + client.server + '\n' + HELP)
    while not client.stop.is_set():
        who = client.store.metadata()['username']
        output.prompt = 'Username:' if who is None else who + '> '
        try:
            line = input(output.prompt)
        except EOFError:
            break
        finally:
            output.prompt = ''
        try:
            if who is None:
                client.operate('login', {'username': line})
                output.human('Logged in as ' + line)
                continue
            if line == 'help':
                output.human(HELP)
                continue
            if line.startswith('send ') or line.startswith('send-json '):
                kind, rest = line.split(' ', 1)
                recipient, separator, text = rest.partition(' ')
                if not separator:
                    raise ClientError('INVALID_COMMAND', 'Use send RECIPIENT TEXT.')
                if kind == 'send-json':
                    try:
                        text = parse_json(text)
                    except (ValueError, UnicodeError):
                        raise ClientError('INVALID_COMMAND', 'Expected exactly one JSON string.')
                    if not isinstance(text, str):
                        raise ClientError('INVALID_COMMAND', 'Expected exactly one JSON string.')
                client.operate('send', {'recipient': recipient, 'text': text})
                continue
            if line.startswith('transport '):
                data = client.operate('transport', {'mode': line[len('transport '):]})
            elif line in ('inbox', 'outbox', 'status', 'quit'):
                data = client.operate(line, {})
            else:
                raise ClientError('INVALID_COMMAND', 'Unknown command. Type help for commands.')
            if line != 'quit':
                rendered = json.dumps(data, ensure_ascii=False, indent=2)
                if line == 'outbox':
                    # Change the label only, never message text in the displayed snapshot.
                    rows = [{**r, 'state': 'accepted by server' if r['state'] == 'accepted' else r['state']} for r in data['messages']]
                    rendered = json.dumps({'messages': rows}, ensure_ascii=False, indent=2)
                output.human(rendered)
        except ClientError as exc:
            output.human(exc.code + ': ' + exc.message)


def main():
    parser = argparse.ArgumentParser(description='Local durable messaging client')
    parser.add_argument('--server', default='http://127.0.0.1:8765')
    parser.add_argument('--state-dir', default='var/python-client')
    parser.add_argument('--machine', action='store_true')
    parser.add_argument('--transport', choices=['online', 'offline'], default='online')
    parser.add_argument('--reset-state', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    output = Presentation(args.machine)
    client = None
    try:
        server = origin(args.server)
        if args.reset_state:
            if not args.yes:
                raise ClientError('INVALID_COMMAND', 'Reset requires --yes and a stopped client.')
            for suffix in ('', '-journal', '-wal', '-shm'):
                path = Path(args.state_dir) / ('messages.sqlite3' + suffix)
                path.unlink(missing_ok=True)
            return 0
        store = Store(args.state_dir, server)
        client = Client(store, server, args.transport, output.changed)
        output.client = client
        client.notify_error = output.error
        meta = store.metadata()
        if args.machine:
            output.emit({'type': 'event', 'event': 'ready', 'username': meta['username'], 'transport': args.transport, 'cursor': meta['receive_cursor']})
        else:
            output.changed()
            if meta['username'] is not None:
                output.human('Restored username: ' + meta['username'])
        client.thread.start()
        try:
            (machine_loop if args.machine else human_loop)(client, output)
        except KeyboardInterrupt:
            pass
        finally:
            client.close()
        if args.machine:
            output.emit({'type': 'event', 'event': 'shutdown'})
        return 0
    except (ClientError, OSError) as exc:
        error = exc if isinstance(exc, ClientError) else ClientError('STORAGE_UNAVAILABLE', str(exc))
        print(error.code + ': ' + error.message, file=sys.stderr, flush=True)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
