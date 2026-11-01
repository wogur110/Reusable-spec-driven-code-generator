"""Contract-first tests of production server controls and real HTTP sockets."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import tkinter as tk
import unittest
import urllib.error
import urllib.request
import uuid
from unittest.mock import patch

from scripts.gui_support import virtual_display
from server.gui import ServerApp

ROOT = Path(__file__).resolve().parents[2]


class ServerGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.display = virtual_display()
        cls.env = cls.display.__enter__()
        cls.old_display = os.environ.get('DISPLAY')
        os.environ['DISPLAY'] = cls.env['DISPLAY']

    @classmethod
    def tearDownClass(cls):
        if cls.old_display is None:
            os.environ.pop('DISPLAY', None)
        else:
            os.environ['DISPLAY'] = cls.old_display
        cls.display.__exit__(None, None, None)

    def setUp(self):
        self.assets = tempfile.TemporaryDirectory()
        Path(self.assets.name, 'index.html').write_text('<html>server GUI fixture</html>')
        self.root = tk.Tk()
        self.app = ServerApp(self.root, port=0, static_dir=self.assets.name)
        self.w = self.app.widgets
        self.root.update()

    def tearDown(self):
        try:
            self.close_window()
        except tk.TclError:
            pass
        self.assets.cleanup()

    def wait(self, predicate, timeout=6):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return
            time.sleep(.01)
        self.fail('Timed out awaiting observable GUI state')

    def text(self, name):
        return str(self.w[name].cget('text'))

    def fill(self, name, value):
        self.w[name].delete(0, 'end')
        self.w[name].insert(0, value)

    def start(self):
        self.w['start-button'].invoke()
        self.wait(lambda: self.text('server-status') == 'Running')
        return self.text('server-url')

    def close_window(self):
        callback = self.root.protocol('WM_DELETE_WINDOW')
        self.root.tk.call(callback)
        deadline = time.monotonic()+6
        while time.monotonic() < deadline:
            try:
                self.root.update()
                if not self.root.winfo_exists():
                    return
            except tk.TclError:
                return
            time.sleep(.01)
        self.fail('Window did not close within six seconds')

    def http(self, origin, path='/health', data=None):
        request = urllib.request.Request(origin+path, data=json.dumps(data).encode() if data else None,
                                         headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def message(self, text='  한글 😀\nsecond line  '):
        return dict(message_id=str(uuid.uuid4()), sender='alice', recipient='bob', text=text)

    def test_SG01_validation_start_and_browser_control(self):
        self.assertEqual(self.text('server-status'), 'Stopped')
        self.assertTrue(self.w['stop-button'].instate(['disabled']))
        for invalid in ['abc', '-1', '65536', '1.5']:
            self.fill('port-input', invalid)
            self.w['start-button'].invoke()
            self.assertTrue(self.text('error-message'))
            self.assertNotEqual(self.text('server-status'), 'Running')
        self.fill('port-input', '0')
        self.fill('static-input', self.assets.name+'/missing')
        self.w['start-button'].invoke()
        self.wait(lambda: bool(self.text('error-message')))
        self.assertNotEqual(self.text('server-status'), 'Running')
        self.fill('static-input', self.assets.name)
        origin = self.start()
        self.assertRegex(origin, r'^http://127\.0\.0\.1:\d+$')
        self.assertEqual(json.loads(self.http(origin)[1])['status'], 'ok')
        self.assertIn(b'server GUI fixture', self.http(origin, '/')[1])
        for name in ['start-button', 'port-input', 'static-input']:
            self.assertTrue(self.w[name].instate(['disabled']))
        with patch('server.gui.webbrowser.open', return_value=True) as open_browser:
            self.w['open-browser'].invoke()
            open_browser.assert_called_once_with(origin)
        with patch('server.gui.webbrowser.open', return_value=False):
            self.w['open-browser'].invoke()
            self.assertTrue(self.text('error-message'))

    def test_SG02_monitoring_replay_error_and_exact_details(self):
        origin = self.start()
        message = self.message()
        self.assertEqual(self.http(origin, '/api/v1/messages', message)[0], 201)
        self.assertEqual(self.http(origin, '/api/v1/messages', message)[0], 200)
        self.assertEqual(self.http(origin, '/api/v1/messages', dict(message,text='conflict'))[0], 409)
        self.assertEqual(self.http(origin, '/api/unknown')[0], 404)
        self.wait(lambda: self.text('response-count') == '4')
        self.assertEqual(self.text('message-count'), '1')
        self.assertEqual(self.text('error-count'), '2')
        rows = self.w['messages'].get_children()
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.w['messages'].item(rows[0], 'values'), ('alice','bob',message['message_id'],'1',message['text']))
        self.w['messages'].selection_set(rows[0])
        self.w['messages'].event_generate('<<TreeviewSelect>>')
        self.root.update()
        self.assertEqual(self.w['message-detail'].get('1.0','end-1c'), message['text'])
        first = json.loads(self.http(origin, '/api/v1/messages?recipient=bob&after=0')[1])
        second = json.loads(self.http(origin, '/api/v1/messages?recipient=bob&after=0')[1])
        self.assertEqual(first,second)
        self.assertEqual(len(first['messages']),1)
        statuses=[self.w['requests'].item(i,'values')[2] for i in self.w['requests'].get_children()]
        self.assertIn('409',statuses)

    def test_SG02_bounded_monitor_windows_keep_full_counts(self):
        origin = self.start()
        for i in range(205):
            self.assertEqual(self.http(origin,'/api/v1/messages',self.message(str(i)))[0],201)
        self.wait(lambda:self.text('message-count')=='205')
        self.assertEqual(self.text('response-count'),'205')
        self.assertEqual(len(self.w['requests'].get_children()),200)
        rows=self.w['messages'].get_children()
        self.assertEqual(len(rows),200)
        self.assertEqual(self.w['messages'].item(rows[0],'values')[4],'5')
        self.assertEqual(self.w['messages'].item(rows[-1],'values')[4],'204')

    def test_SG03_stop_restart_empty_session_releases_port(self):
        origin=self.start();session=self.text('session-id')
        self.http(origin,'/api/v1/messages',self.message())
        self.wait(lambda:self.text('message-count')=='1')
        self.w['stop-button'].invoke()
        self.wait(lambda:self.text('server-status')=='Stopped')
        self.assertEqual(self.text('server-url'),'')
        self.assertEqual(self.text('message-count'),'0')
        self.assertFalse(self.w['messages'].get_children())
        self.assertFalse(self.w['requests'].get_children())
        with self.assertRaises(urllib.error.URLError):self.http(origin)
        self.fill('port-input',origin.rsplit(':',1)[1])
        self.assertEqual(self.start(),origin)
        self.assertNotEqual(self.text('session-id'),session)
        self.assertEqual(self.text('response-count'),'0')
        self.assertEqual(json.loads(self.http(origin,'/api/v1/messages?recipient=bob&after=0')[1])['messages'],[])
        self.assertIn('fresh',self.text('session-notice').lower())

    def test_SG04_bind_conflict_does_not_stop_existing_server(self):
        child=subprocess.Popen([sys.executable,'server/main.py','--port','0','--static-dir',self.assets.name],cwd=ROOT,stdout=subprocess.PIPE,text=True)
        try:
            origin=json.loads(child.stdout.readline())['origin']
            self.fill('port-input',origin.rsplit(':',1)[1]);self.w['start-button'].invoke()
            self.wait(lambda:self.text('server-status')=='Error')
            self.assertTrue(self.text('error-message'))
            self.assertEqual(self.http(origin)[0],200)
            self.fill('port-input','0');self.start()
            self.assertEqual(self.http(origin)[0],200)
        finally:
            child.terminate();child.wait(timeout=5);child.stdout.close()

    def test_SG04_close_during_startup(self):
        self.w['start-button'].invoke()
        self.close_window()

    def test_SG04_close_with_incomplete_request_releases_listener(self):
        origin=self.start();port=int(origin.rsplit(':',1)[1])
        with socket.create_connection(('127.0.0.1',port),timeout=2) as peer:
            peer.sendall(b'POST /api/v1/messages HTTP/1.1\r\nHost: localhost\r\nContent-Length: 100\r\nContent-Type: application/json\r\n\r\n{')
            self.root.update()
            self.close_window()
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            probe.bind(('127.0.0.1',port))

    def test_SG04_production_launch_closed_stdin(self):
        # Give the fixture a distinct name so discovery inspects the production window.
        self.root.title('Server test fixture');self.root.update()
        child=subprocess.Popen([sys.executable,'server/gui.py','--port','0','--static-dir',self.assets.name],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=self.env)
        try:
            def visible():
                self.assertIsNone(child.poll())
                result=subprocess.run(['xwininfo','-name','Local Messenger - Server'],capture_output=True,text=True,env=self.env)
                return 'Map State: IsViewable' in result.stdout
            self.wait(visible)
            child.send_signal(signal.SIGINT)
            self.assertEqual(child.wait(timeout=6),0)
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=3)
            child.stdout.close();child.stderr.close()

    def test_DIR03_select_filter_refresh_and_receipt_categories(self):
        origin=self.start();w=self.w
        # Tests operate actual tabs, entries, tree selection and buttons.
        tabs=w['server-tabs'];tabs.select(next(t for t in tabs.tabs() if tabs.tab(t,'text')=='Users'));self.root.update()
        for name in ['alice','bob']:
            self.assertEqual(self.http(origin,'/api/v1/users',{'username':name})[0],200)
        message=self.message();self.http(origin,'/api/v1/messages',message)
        self.wait(lambda:'bob' in w['users'].get_children())
        w['users'].selection_set('bob');w['users'].event_generate('<<TreeviewSelect>>')
        self.wait(lambda:self.text('user-queued-count')=='1')
        self.assertEqual(self.text('user-received-count'),'0');self.assertEqual(self.text('user-sent-count'),'0')
        w['user-refresh'].invoke();self.root.update()
        self.assertEqual(self.text('user-queued-count'),'1')
        self.http(origin,'/api/v1/messages?recipient=bob&after=0')
        w['user-refresh'].invoke();self.root.update()
        self.assertEqual(self.text('user-queued-count'),'1')
        self.assertIn('Offline client queues: unknown',self.text('queue-notice'))
        activity=w['activity-tabs'];activity.select(next(t for t in activity.tabs() if activity.tab(t,'text')=='Queued'));self.root.update()
        iid='alice:'+message['message_id'];w['user-queued'].selection_set(iid);w['user-queued'].event_generate('<<TreeviewSelect>>');self.root.update()
        self.assertEqual(w['user-message-detail'].get('1.0','end-1c'),message['text'])
        self.http(origin,'/api/v1/receipts',{'recipient':'bob','through':1})
        self.wait(lambda:self.text('user-received-count')=='1')
        self.assertEqual(self.text('user-queued-count'),'0')
        w['users'].selection_set('alice');w['users'].event_generate('<<TreeviewSelect>>')
        self.wait(lambda:self.text('user-sent-count')=='1')
        self.assertEqual(w['user-sent'].item(iid,'values')[3],'received')
        self.fill('user-filter','BO');w['user-filter'].focus_force();w['user-filter'].event_generate('<KeyRelease>');self.root.update()
        self.assertEqual(w['users'].get_children(),('bob',));self.assertEqual(self.text('selected-user'),'')
        self.assertEqual(self.text('user-sent-count'),'0')

    def test_DIR03_per_user_history_exceeds_global_window(self):
        origin=self.start();w=self.w
        for n in range(205):self.http(origin,'/api/v1/messages',self.message(str(n)))
        self.wait(lambda:'bob' in w['users'].get_children())
        w['users'].selection_set('bob');w['users'].event_generate('<<TreeviewSelect>>')
        self.wait(lambda:self.text('user-queued-count')=='205')
        self.assertEqual(len(w['user-queued'].get_children()),205)
        self.http(origin,'/api/v1/receipts',{'recipient':'bob','through':200})
        self.wait(lambda:self.text('user-received-count')=='200')
        self.assertEqual(self.text('user-queued-count'),'5')
        self.assertEqual(len(w['messages'].get_children()),200)

    def test_DIR08_restart_clears_directory_acknowledgments_and_selection(self):
        origin=self.start();w=self.w
        self.http(origin,'/api/v1/messages',self.message())
        self.http(origin,'/api/v1/receipts',{'recipient':'bob','through':1})
        self.wait(lambda:'bob' in w['users'].get_children())
        w['users'].selection_set('bob');w['users'].event_generate('<<TreeviewSelect>>')
        self.wait(lambda:self.text('user-received-count')=='1')
        w['stop-button'].invoke();self.wait(lambda:self.text('server-status')=='Stopped')
        self.assertEqual(w['users'].get_children(),());self.assertEqual(self.text('selected-user'),'')
        self.assertEqual(self.text('user-received-count'),'0')
        origin=self.start();self.assertEqual(json.loads(self.http(origin,'/api/v1/users')[1]),{'users':[]})
        self.http(origin,'/api/v1/messages',self.message())
        self.wait(lambda:'bob' in w['users'].get_children())
        w['users'].selection_set('bob');w['users'].event_generate('<<TreeviewSelect>>')
        self.wait(lambda:self.text('user-queued-count')=='1')
        self.assertEqual(self.text('user-received-count'),'0')


    def test_DIR_online_offline_status_expires_and_recovers_without_refresh(self):
        origin = self.start()
        now = [100.0]
        self.app.server.store.clock = lambda: now[0]
        self.http(origin, '/api/v1/messages', self.message())
        self.wait(lambda: 'alice' in self.w['users'].get_children())
        self.assertEqual(self.w['users'].heading('presence', 'text'), 'Status')
        self.assertIn('15 seconds', self.text('presence-notice'))
        self.assertEqual(self.w['users'].item('alice', 'values')[1], 'Offline')
        self.http(origin, '/api/v1/users', {'username': 'alice'})
        self.wait(lambda: self.w['users'].item('alice', 'values')[1] == 'Online')
        self.w['users'].selection_set('alice')
        self.w['users'].event_generate('<<TreeviewSelect>>')
        now[0] = 114.999
        self.w['user-refresh'].invoke()
        self.assertEqual(self.w['users'].item('alice', 'values')[1], 'Online')
        now[0] = 115.0
        self.wait(lambda: self.w['users'].item('alice', 'values')[1] == 'Offline')
        self.assertEqual(self.w['users'].selection(), ('alice',))
        self.assertEqual(self.text('user-sent-count'), '1')
        self.assertEqual(self.w['users'].item('bob', 'values')[1], 'Offline')
        self.http(origin, '/api/v1/users', {'username': 'alice'})
        self.wait(lambda: self.w['users'].item('alice', 'values')[1] == 'Online')
        self.assertEqual(self.app.server.store.acknowledged, {})

    def test_PRES02_status_changes_by_client_presence_without_messages(self):
        origin=self.start();route='/api/v1/presence'
        for online,label in [(True,'Online'),(False,'Offline'),(True,'Online')]:
            self.assertEqual(self.http(origin,route,{'username':'alice','online':online})[0],200)
            self.wait(lambda:'alice' in self.w['users'].get_children() and self.w['users'].item('alice','values')[1]==label)
            self.assertEqual(self.text('message-count'),'0')
        self.http(origin,route,{'username':'alice','online':False})
        self.http(origin,'/api/v1/users',{'username':'alice'})
        self.http(origin,'/api/v1/messages',self.message())
        self.wait(lambda:self.text('message-count')=='1')
        self.assertEqual(self.w['users'].item('alice','values')[1],'Offline')
        self.assertIn('Offline choice',self.text('presence-notice'))
