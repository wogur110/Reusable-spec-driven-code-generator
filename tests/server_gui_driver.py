"""Operate the production server window via actual widgets, not lifecycle calls."""
import json
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.gui import ServerApp
root=tk.Tk()
app=ServerApp(root,port=0)
requests=queue.Queue()

def emit(value):print(json.dumps(value),flush=True)
def reader():
    for line in sys.stdin:requests.put(json.loads(line))
    requests.put({'id':None,'command':'close'})
def poll():
    try:
        while True:
            request=requests.get_nowait();command=request['command']
            try:
                data={}
                if command=='snapshot':
                    data={'widgets':{},'messages':[]}
                    for name,w in app.widgets.items():
                        if name=='messages':data['messages']=[list(w.item(i,'values')) for i in w.get_children()]
                        elif name in ('requests','message-detail'):continue
                        else:data['widgets'][name]={'text':w.get() if hasattr(w,'get') else str(w.cget('text'))}
                elif command=='click':
                    w=app.widgets[request['widget']]
                    if w.instate(['disabled']):raise ValueError('Disabled widget')
                    w.invoke()
                elif command=='fill':
                    w=app.widgets[request['widget']];w.delete(0,'end');w.insert(0,request['text'])
                elif command=='close':
                    root.tk.call(root.protocol('WM_DELETE_WINDOW'))
                    emit({'type':'result','id':request['id'],'ok':True,'data':{}})
                    return
                else:raise ValueError('Unknown action')
                emit({'type':'result','id':request['id'],'ok':True,'data':data})
            except Exception as exc:emit({'type':'result','id':request['id'],'ok':False,'error':str(exc)})
    except queue.Empty:pass
    root.after(20,poll)
threading.Thread(target=reader,daemon=True).start()
root.after(20,poll)
root.after(0,lambda:emit({'event':'ready'}))
root.mainloop()
