"""Retained automation: real Tk widgets only; no calls into messaging operations."""
import argparse
import json
import queue
import sqlite3
import sys
import threading
import traceback
from pathlib import Path
import tkinter as tk

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'generated/python-client'))
from gui import DesktopApp

parser = argparse.ArgumentParser()
parser.add_argument('--server', required=True)
parser.add_argument('--state-dir', required=True)
parser.add_argument('--transport', default='online')
args = parser.parse_args()
root = tk.Tk()
app = DesktopApp(root, args.server, args.state_dir, args.transport)
requests = queue.Queue()


def emit(value):
    print(json.dumps(value, ensure_ascii=True), flush=True)


def text(widget):
    if isinstance(widget, tk.Text):
        return widget.get('1.0', 'end-1c')
    if widget.winfo_class() in ('Entry', 'TEntry', 'TCombobox'):
        return widget.get()
    return str(widget.cget('text'))


def snapshot():
    widgets = app.widgets
    inbox = []
    for iid in widgets['inbox'].get_children(''):
        sender, body, sequence = widgets['inbox'].item(iid, 'values')
        inbox.append(dict(message_id=iid.split(':', 1)[1], sender=sender, text=body, sequence=int(sequence)))
    outbox = []
    for iid in widgets['outbox'].get_children(''):
        recipient, body, state, error, order = widgets['outbox'].item(iid, 'values')
        outbox.append(dict(message_id=iid, recipient=recipient, text=body,
                           state='accepted' if state == 'accepted by server' else state,
                           visible_state=state, error=error or None, local_order=int(order)))
    users=[]
    if 'user-directory' in widgets:
        users=[dict(username=iid,presence=widgets['user-directory'].item(iid,'values')[1]) for iid in widgets['user-directory'].get_children('')]
    state = dict(ready=bool(app.ready), inbox=inbox, outbox=outbox, users=users, widgets={})
    for key, widget in widgets.items():
        if key in ('inbox', 'outbox', 'user-directory'):
            continue
        state['widgets'][key] = dict(text=text(widget), visible=bool(widget.winfo_ismapped()),
                                    enabled=str(widget.cget('state')) != 'disabled' if 'state' in widget.keys() else True)
    database = Path(args.state_dir)/'messages.sqlite3'
    if database.exists():
        with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True) as db:
            try:
                row = db.execute('SELECT receive_cursor FROM metadata WHERE id=1').fetchone()
            except sqlite3.OperationalError:
                row = None
            state['cursor'] = row[0] if row else None
    return state


def read_commands():
    for line in sys.stdin:
        try:
            requests.put(json.loads(line))
        except Exception:
            traceback.print_exc(file=sys.stderr)
    requests.put({'id': None, 'command': 'close'})


def poll():
    try:
        while True:
            request = requests.get_nowait()
            command = request['command']
            if command == 'close':
                emit({'type': 'result', 'id': request['id'], 'ok': True, 'data': {}})
                app.close()
                return
            try:
                if command == 'snapshot':
                    data = snapshot()
                else:
                    widget = app.widgets[request['widget']]
                    if command == 'fill':
                        if isinstance(widget, tk.Text):
                            widget.delete('1.0', 'end'); widget.insert('1.0', request['text'])
                        else:
                            widget.delete(0, 'end'); widget.insert(0, request['text'])
                            if request['widget']=='user-filter':widget.focus_force();widget.event_generate('<KeyRelease>')
                    elif command == 'click':
                        if not widget.winfo_ismapped() or str(widget.cget('state')) == 'disabled':
                            raise AssertionError('Cannot click a hidden or disabled widget')
                        widget.invoke()
                    elif command == 'select':
                        widget.set(request['value']); widget.event_generate('<<ComboboxSelected>>')
                    elif command == 'row':
                        widget.selection_set(request['iid']); widget.event_generate('<<TreeviewSelect>>')
                    else:
                        raise ValueError('Unknown GUI action')
                    data = {}
                emit({'type': 'result', 'id': request['id'], 'ok': True, 'data': data})
            except Exception as exc:
                emit({'type': 'result', 'id': request['id'], 'ok': False, 'error': str(exc)})
    except queue.Empty:
        pass
    root.after(20, poll)


threading.Thread(target=read_commands, daemon=True).start()
root.after(20, poll)
# Driver readiness means widgets exist; app.ready is asserted separately.
root.after(0, lambda: emit({'type': 'event', 'event': 'ready'}))
root.mainloop()
