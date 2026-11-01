"""Desktop entry point and display-free JSON-lines interface."""
import argparse
import json
import signal
import sys
import threading
from core import Client
from protocol import Failure, loads, origin
from storage import reset_files


def machine(args):
    output_lock = threading.Lock()
    revision = 0
    def emit(value):
        with output_lock:
            print(json.dumps(value, ensure_ascii=True, separators=(',', ':')), flush=True)
    def changed():
        nonlocal revision
        with output_lock:
            revision += 1
            print(json.dumps({'type':'event','event':'state_changed','revision':revision}), flush=True)
    client = Client(args.server, args.state_dir, args.transport, changed)
    state = client.status()
    emit({'type':'event','event':'ready','username':state['username'],'transport':state['transport'],'cursor':state['cursor']})
    client.start()
    fields = {'login':{'username'}, 'send':{'recipient','text'}, 'inbox':set(), 'outbox':set(), 'status':set(), 'transport':{'mode'}, 'quit':set()}
    try:
        while True:
            raw = sys.stdin.buffer.readline(65537)
            if not raw:
                break
            correlation = None
            quit_requested = False
            try:
                if len(raw) > 65536:
                    while raw and not raw.endswith(b'\n'):
                        raw = sys.stdin.buffer.readline(65537)
                    raise Failure('INVALID_COMMAND', 'Input line exceeds 65536 bytes.')
                try:
                    command = loads(raw, duplicates=True)
                except (ValueError, UnicodeError):
                    raise Failure('INVALID_COMMAND', 'Expected one valid UTF-8 JSON object with unique members.')
                if not isinstance(command, dict):
                    raise Failure('INVALID_COMMAND', 'Expected a command object.')
                key = command.get('id')
                if isinstance(key, str) and 1 <= len(key) <= 64 and key.isascii():
                    correlation = key
                name = command.get('command')
                if correlation is None or not isinstance(name,str) or name not in fields or set(command) != fields[name] | {'id','command'} or any(not isinstance(command[k],str) for k in fields[name]):
                    raise Failure('INVALID_COMMAND', 'Invalid command ID, name, fields or parameter types.')
                if name == 'login':
                    result = client.login(command['username'])
                elif name == 'send':
                    result = client.send(command['recipient'], command['text'])
                elif name in ('inbox','outbox'):
                    snapshot = client.store.snapshot()
                    result = {'messages': snapshot[1 if name=='inbox' else 2]}
                elif name == 'transport':
                    result = client.transport(command['mode'])
                elif name == 'status':
                    result = client.status()
                else:
                    result = {}
                    quit_requested = True
                emit({'type':'result','id':correlation,'ok':True,'data':result})
            except Exception as e:
                error = e if isinstance(e,Failure) else Failure('STORAGE_UNAVAILABLE', str(e))
                emit({'type':'result','id':correlation,'ok':False,'error':error.data()})
            if quit_requested:
                break
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        emit({'type':'event','event':'shutdown'})
    return 0


def main():
    parser = argparse.ArgumentParser(description='Local Messenger: desktop GUI, or --machine JSON-lines interface.')
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
                raise Failure('INVALID_COMMAND', 'Stopped-store reset requires --yes confirmation.')
            reset_files(args.state_dir)
            return 0
        if args.machine:
            return machine(args)
        try:
            import tkinter as tk
            from gui import DesktopApp
            root = tk.Tk()
        except (ImportError, RuntimeError) as e:
            raise Failure('GUI_UNAVAILABLE', 'Install python3-tk (Tcl/Tk 8.6) and use a working desktop display: ' + str(e))
        except Exception as e:
            raise Failure('GUI_UNAVAILABLE', 'Cannot open desktop display; check Tk and DISPLAY/WSLg: ' + str(e))
        app = DesktopApp(root, args.server, args.state_dir, args.transport)
        signal.signal(signal.SIGINT, lambda *_: app.close())
        root.mainloop()
        return 0 if app.ready else 2
    except Failure as e:
        print(e.code + ': ' + e.message, file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
