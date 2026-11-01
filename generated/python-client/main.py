"""Desktop launcher and display-free JSON-lines interface."""
import argparse
import json
import signal
import sys
import threading
from model import ClientError, origin, reset_files
from core import Client


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate member.')
        result[key] = value
    return result


def machine(args):
    output_lock = threading.Lock()
    revision = 0
    def emit(value):
        with output_lock:
            sys.stdout.write(json.dumps(value, ensure_ascii=True, separators=(',', ':')) + '\n')
            sys.stdout.flush()
    def changed():
        nonlocal revision
        revision += 1
        emit({'type': 'event', 'event': 'state_changed', 'revision': revision})
    client = Client(args.server, args.state_dir, args.transport, changed)
    s = client.status()
    emit({'type': 'event', 'event': 'ready', 'username': s['username'], 'transport': s['transport'], 'cursor': s['cursor']})
    client.start()
    parameters = {'login': {'username'}, 'send': {'recipient', 'text'}, 'inbox': set(), 'outbox': set(), 'status': set(), 'transport': {'mode'}, 'quit': set()}
    try:
        while True:
            line = sys.stdin.buffer.readline(65537)
            if not line:
                break
            correlation = None
            quitting = False
            try:
                if len(line) > 65536:
                    while not line.endswith(b'\n'):
                        line = sys.stdin.buffer.readline(65537)
                        if not line:
                            break
                    raise ValueError('Input exceeds 65536 bytes.')
                obj = json.loads(line.decode('utf-8'), object_pairs_hook=no_duplicates, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite number.')))
                if not isinstance(obj, dict):
                    raise ValueError('Command must be an object.')
                candidate = obj.get('id')
                if isinstance(candidate, str) and 1 <= len(candidate) <= 64 and candidate.isascii():
                    correlation = candidate
                else:
                    raise ValueError('ID must be a nonempty ASCII string of at most 64 characters.')
                command = obj.get('command')
                if not isinstance(command, str) or command not in parameters or set(obj) != parameters[command] | {'id', 'command'}:
                    raise ValueError('Unknown command or members.')
                if any(not isinstance(obj[k], str) for k in parameters[command]):
                    raise ValueError('Parameters must be strings.')
                if command == 'login':
                    data = client.login(obj['username'])
                elif command == 'send':
                    data = client.send(obj['recipient'], obj['text'])
                elif command == 'inbox':
                    data = {'messages': client.store.incoming()}
                elif command == 'outbox':
                    data = {'messages': client.store.outgoing()}
                elif command == 'status':
                    data = client.status()
                elif command == 'transport':
                    data = client.transport(obj['mode'])
                else:
                    data, quitting = {}, True
                emit({'type': 'result', 'id': correlation, 'ok': True, 'data': data})
            except (ValueError, UnicodeError) as e:
                emit({'type': 'result', 'id': correlation, 'ok': False, 'error': {'code': 'INVALID_COMMAND', 'message': str(e)}})
            except Exception as e:
                error = e.data() if isinstance(e, ClientError) else {'code': 'STORAGE_UNAVAILABLE', 'message': str(e)}
                emit({'type': 'result', 'id': correlation, 'ok': False, 'error': error})
            if quitting:
                break
    except KeyboardInterrupt:
        pass
    finally:
        client.shutdown()
        emit({'type': 'event', 'event': 'shutdown'})
    return 0


def main():
    parser = argparse.ArgumentParser(description='Local Messenger - Python desktop client')
    parser.add_argument('--server', default='http://127.0.0.1:8765')
    parser.add_argument('--state-dir', default='var/python-client')
    parser.add_argument('--machine', action='store_true')
    parser.add_argument('--transport', choices=('online', 'offline'), default='online')
    parser.add_argument('--reset-state', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()
    try:
        args.server = origin(args.server)
        if args.reset_state:
            if not args.yes:
                raise ClientError('INVALID_COMMAND', 'Stopped store reset requires --yes.')
            reset_files(args.state_dir)
            return 0
        if args.machine:
            return machine(args)
        try:
            import tkinter as tk
            from gui import DesktopApp
            root = tk.Tk()
        except (ImportError, RuntimeError) as e:
            raise ClientError('GUI_UNAVAILABLE', 'Install Python Tkinter/Tcl/Tk 8.6 and use an available display: ' + str(e))
        except Exception as e:
            raise ClientError('GUI_UNAVAILABLE', 'A graphical display and native Tcl/Tk are required: ' + str(e))
        app = DesktopApp(root, args.server, args.state_dir, args.transport)
        signal.signal(signal.SIGINT, lambda *_: app.close())
        root.mainloop()
        return 2 if app.startup_failed else 0
    except ClientError as e:
        print(e.code + ': ' + e.message, file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
