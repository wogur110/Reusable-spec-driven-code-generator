"""Desktop entry point and display-free JSON-lines adapter."""
import argparse
import json
import signal
import sys
import threading
from core import Client
from protocol import ClientError, loads, origin
from storage import reset_files

class Machine:
    def __init__(self):
        self.output_lock = threading.RLock()
        self.revision = 0
        self.ready = False

    def emit(self, value):
        with self.output_lock:
            print(json.dumps(value,ensure_ascii=True,allow_nan=False),flush=True)

    def changed(self):
        with self.output_lock:
            self.revision += 1
            if self.ready:
                self.emit({'type':'event','event':'state_changed','revision':self.revision})

    def run(self, args):
        client = Client(args.server,args.state_dir,args.transport,self.changed)
        try:
            with self.output_lock:
                s = client.snapshot()['status']
                self.emit({'type':'event','event':'ready','username':s['username'],'transport':s['transport'],'cursor':s['cursor']})
                self.ready = True
            while True:
                line = sys.stdin.buffer.readline(65537)
                if not line:
                    break
                cid = None
                quit_requested = False
                try:
                    if len(line) > 65536:
                        while not line.endswith(b'\n'):
                            line = sys.stdin.buffer.readline(65537)
                            if not line:
                                break
                        raise ClientError('INVALID_COMMAND','Input line exceeds 65536 bytes.')
                    try:
                        obj = loads(line,duplicates=True)
                    except (ValueError,UnicodeError,RecursionError):
                        raise ClientError('INVALID_COMMAND','Expected a UTF-8 JSON object with unique members and finite numbers.')
                    if isinstance(obj,dict):
                        value = obj.get('id')
                        if isinstance(value,str) and 1 <= len(value) <= 64 and value.isascii():
                            cid = value
                    if cid is None or not isinstance(obj,dict):
                        raise ClientError('INVALID_COMMAND','Command id must be a nonempty ASCII string of at most 64 characters.')
                    command = obj.get('command')
                    fields = {'login':('username',),'send':('recipient','text'),'inbox':(),'outbox':(),'status':(),'transport':('mode',),'quit':()}
                    if not isinstance(command,str) or command not in fields or set(obj) != {'id','command',*fields[command]} or any(not isinstance(obj[k],str) for k in fields[command]):
                        raise ClientError('INVALID_COMMAND','Unknown command, fields, or parameter types.')
                    if command=='login':
                        data = client.login(obj['username'])
                    elif command=='send':
                        data = client.send(obj['recipient'],obj['text'])
                    elif command in ('inbox','outbox'):
                        data = {'messages':client.snapshot()[command]}
                    elif command=='status':
                        data = client.snapshot()['status']
                    elif command=='transport':
                        data = client.transport(obj['mode'])
                    else:
                        data = {}
                        quit_requested = True
                    self.emit({'type':'result','id':cid,'ok':True,'data':data})
                except ClientError as exc:
                    self.emit({'type':'result','id':cid,'ok':False,'error':exc.object()})
                if quit_requested:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            client.shutdown()
            self.emit({'type':'event','event':'shutdown'})
        return 0

def main():
    parser = argparse.ArgumentParser(description='Local Messenger: durable local queues and a desktop interface.')
    parser.add_argument('--server',default='http://127.0.0.1:8765')
    parser.add_argument('--state-dir',default='var/python-client')
    parser.add_argument('--machine',action='store_true',help='Display-free JSON-lines interface')
    parser.add_argument('--transport',choices=('online','offline'),default='online')
    parser.add_argument('--reset-state',action='store_true')
    parser.add_argument('--yes',action='store_true')
    args = parser.parse_args()
    try:
        args.server = origin(args.server)
        if args.reset_state:
            if not args.yes:
                raise ClientError('INVALID_COMMAND','Stopped reset requires --yes confirmation.')
            reset_files(args.state_dir)
            return 0
        if args.machine:
            return Machine().run(args)
        try:
            import tkinter as tk
            from gui import DesktopApp
            root = tk.Tk()
        except Exception as exc:
            print('GUI unavailable: install Python tkinter and Tcl/Tk 8.6 and provide a desktop display (or use --machine). ' + str(exc),file=sys.stderr)
            return 2
        app = DesktopApp(root,args.server,args.state_dir,args.transport)
        startup_ok = app.ready
        signal.signal(signal.SIGINT,lambda signum,frame:app.close())
        # A recurring Tk callback also lets Python process signals with idle stdin.
        root.mainloop()
        return 0 if startup_ok else 2
    except ClientError as exc:
        print(exc.code+': '+exc.message,file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0

if __name__=='__main__':
    sys.exit(main())
