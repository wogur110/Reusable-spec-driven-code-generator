"""Desktop entry point and display-free JSON-lines production interface."""
import argparse
import json
from pathlib import Path
import signal
import sys
import threading
from client import Client
from protocol import ClientError, origin

OUTPUT_LOCK = threading.Lock()

def emit(value):
    with OUTPUT_LOCK:
        sys.stdout.write(json.dumps(value, ensure_ascii=True, allow_nan=False) + '\n')
        sys.stdout.flush()

def decode_command(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON member')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite number')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=invalid)

def valid_id(value):
    return isinstance(value, str) and 1 <= len(value) <= 64 and value.isascii()

def machine(args):
    client = Client(args.server, args.state_dir, args.transport,
                    lambda revision: emit({'type':'event','event':'state_changed','revision':revision}))
    status = client.status()
    emit({'type':'event','event':'ready','username':status['username'], 'transport':status['transport'],'cursor':status['cursor']})
    client.start()
    params = {'login': ('username',), 'send': ('recipient','text'), 'inbox': (), 'outbox': (), 'status': (), 'transport': ('mode',), 'quit': ()}
    try:
        while True:
            raw = sys.stdin.buffer.readline(65537)
            if not raw:
                break
            correlation = None
            quitting = False
            try:
                if len(raw) > 65536:
                    while not raw.endswith(b'\n'):
                        raw = sys.stdin.buffer.readline(65537)
                        if not raw:
                            break
                    raise ClientError('INVALID_COMMAND', 'Command line exceeds 65536 bytes.')
                try:
                    obj = decode_command(raw)
                except (UnicodeError, ValueError, RecursionError):
                    raise ClientError('INVALID_COMMAND', 'Use one valid UTF-8 JSON command with unique members.')
                if isinstance(obj, dict) and valid_id(obj.get('id')):
                    correlation = obj['id']
                command = obj.get('command') if isinstance(obj, dict) else None
                if correlation is None or not isinstance(command, str) or command not in params:
                    raise ClientError('INVALID_COMMAND', 'A valid id and known command are required.')
                if set(obj) != {'id','command',*params[command]} or any(not isinstance(obj[k],str) for k in params[command]):
                    raise ClientError('INVALID_COMMAND', 'Command fields and parameter types must match the interface.')
                if command == 'login':
                    data = client.login(obj['username'])
                elif command == 'send':
                    data = client.send(obj['recipient'], obj['text'])
                elif command in ('inbox','outbox'):
                    snapshot = client.snapshot()
                    data = {'messages':snapshot[command]}
                elif command == 'status':
                    data = client.status()
                elif command == 'transport':
                    data = client.transport(obj['mode'])
                else:
                    data, quitting = {}, True
                emit({'type':'result','id':correlation,'ok':True,'data':data})
            except ClientError as exc:
                emit({'type':'result','id':correlation,'ok':False,'error':exc.data()})
            if quitting:
                break
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        emit({'type':'event','event':'shutdown'})
    return 0

def main():
    parser = argparse.ArgumentParser(description='Local Messenger Python desktop (or JSON-lines machine interface).')
    parser.add_argument('--server', default='http://127.0.0.1:8765')
    parser.add_argument('--state-dir', default='var/python-client')
    parser.add_argument('--machine', action='store_true')
    parser.add_argument('--transport', choices=('online','offline'), default='online')
    parser.add_argument('--reset-state', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    try:
        args.server = origin(args.server)
        if args.reset_state:
            if not args.yes:
                raise ClientError('INVALID_COMMAND', '--reset-state requires --yes and a stopped client.')
            directory = Path(args.state_dir)
            for suffix in ('', '-journal','-wal','-shm'):
                path = directory / ('messages.sqlite3' + suffix)
                if path.exists() or path.is_symlink():
                    path.unlink()
            return 0
        if args.machine:
            return machine(args)
        try:
            import tkinter as tk
            from gui import DesktopApp
            root = tk.Tk()
        except Exception as exc:
            print('GUI unavailable: install native tkinter/Tcl/Tk 8.6 and use a working desktop display. ' + str(exc), file=sys.stderr)
            return 2
        app = DesktopApp(root, args.server, args.state_dir, args.transport)
        signal.signal(signal.SIGINT, lambda *_: app.close())
        root.mainloop()
        return 0 if app.client is not None else 2
    except (ClientError, OSError) as exc:
        print((exc.code + ': ' + exc.message) if isinstance(exc, ClientError) else str(exc), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
