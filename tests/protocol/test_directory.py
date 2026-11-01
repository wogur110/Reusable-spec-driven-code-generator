"""Independent HTTP contracts for directory and durable receipt observations."""
import concurrent.futures
import http.client
import json
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from server.main import Server


class DirectoryProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.clock=[100.0]
        self.server=Server(('127.0.0.1',0),Path(self.temp.name),clock=lambda:self.clock[0])
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.01},daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def api(self,method,path,data=None,raw=None,headers=None):
        body=raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        connection.request(method,path,body,headers or ({'Content-Type':'application/json'} if body is not None else {}))
        r=connection.getresponse();status=r.status;value=json.loads(r.read());connection.close();return status,value
    def error(self,result,status,code,field=None):
        self.assertEqual(result[0],status);self.assertEqual((result[1]['error']['code'],result[1]['error']['field']),(code,field))
    def message(self,sender='alice',recipient='bob',text='  한글 😀\nline  '):
        return {'message_id':str(uuid.uuid4()),'sender':sender,'recipient':recipient,'text':text}
    def test_DIR01_directory_membership_presence_and_side_effect_free_refresh(self):
        self.assertEqual(self.api('GET','/api/v1/users'),(200,{'users':[]}))
        for username in ['bob','alice','bob']:
            self.assertEqual(self.api('POST','/api/v1/users',{'username':username}),(200,{'username':username}))
        self.assertEqual(self.api('GET','/api/v1/users')[1],{'users':[{'username':'alice','online':True},{'username':'bob','online':True}]})
        self.clock[0]+=15
        self.assertTrue(all(not row['online'] for row in self.api('GET','/api/v1/users')[1]['users']))
        msg=self.message(recipient='carol');self.assertEqual(self.api('POST','/api/v1/messages',msg)[0],201)
        users=self.api('GET','/api/v1/users')[1]['users']
        self.assertEqual(users,[{'username':n,'online':False} for n in ['alice','bob','carol']])
        self.api('POST','/api/v1/receipts',{'recipient':'carol','through':0})
        self.assertEqual(self.api('GET','/api/v1/users')[1]['users'],users)
        self.api('POST','/api/v1/users',{'username':'carol'})
        self.assertTrue(self.api('GET','/api/v1/users')[1]['users'][-1]['online'])
    def test_DIR01_strict_new_routes_reject_invalid_inputs_without_users(self):
        for data in [{},[],{'username':'alice','extra':True}]:self.error(self.api('POST','/api/v1/users',data),400,'INVALID_FIELDS')
        for name in ['Alice',' alice','',True,None,'a'*33]:self.error(self.api('POST','/api/v1/users',{'username':name}),400,'INVALID_USERNAME','username')
        for route in ['/api/v1/users','/api/v1/receipts']:
            self.error(self.api('POST',route,raw=b'{"username":"alice","username":"bob"}'),400,'INVALID_JSON')
            self.error(self.api('POST',route,raw=b'{}',headers={'Content-Type':'text/plain'}),415,'UNSUPPORTED_MEDIA_TYPE')
            self.error(self.api('POST',route+'?x=1',{}),400,'INVALID_QUERY')
            self.error(self.api('DELETE',route),405,'METHOD_NOT_ALLOWED')
        self.error(self.api('GET','/api/v1/receipts'),405,'METHOD_NOT_ALLOWED')
        self.error(self.api('GET','/api/v1/users?x=1'),400,'INVALID_QUERY')
        self.error(self.api('GET','/api/v1/users',{}),400,'INVALID_REQUEST')
        self.assertEqual(self.api('GET','/api/v1/users')[1],{'users':[]})
    def test_DIR02_receipts_monotonic_concurrent_and_non_destructive(self):
        messages=[self.message(text=str(n)) for n in range(3)]
        receipts=[self.api('POST','/api/v1/messages',m)[1] for m in messages]
        page=self.api('GET','/api/v1/messages?recipient=bob&after=0')[1]
        self.assertEqual(self.api('POST','/api/v1/receipts',{'recipient':'bob','through':0}),(200,{'recipient':'bob','through':0}))
        def ack(n):return self.api('POST','/api/v1/receipts',{'recipient':'bob','through':n})
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(ack,[1,3,2,3]))
        self.assertTrue(all(result[0]==200 for result in results))
        self.assertEqual(ack(0),(200,{'recipient':'bob','through':3}))
        self.assertEqual(ack(3),(200,{'recipient':'bob','through':3}))
        self.assertEqual(self.api('GET','/api/v1/messages?recipient=bob&after=0')[1],page)
        for m,r in zip(messages,receipts):self.assertEqual(self.api('POST','/api/v1/messages',m),(200,r))
        self.assertEqual(self.api('POST','/api/v1/receipts',{'recipient':'carol','through':0.0}),(200,{'recipient':'carol','through':0}))
    def test_DIR02_invalid_ack_does_not_advance_or_register(self):
        for through in [True,False,-1,1.5,'1',None,9007199254740992]:
            self.error(self.api('POST','/api/v1/receipts',{'recipient':'bob','through':through}),400,'INVALID_RECEIPT','through')
        self.error(self.api('POST','/api/v1/receipts',{'recipient':'Bob','through':0}),400,'INVALID_USERNAME','recipient')
        self.error(self.api('POST','/api/v1/receipts',{'recipient':'bob','through':0,'extra':1}),400,'INVALID_FIELDS')
        self.error(self.api('POST','/api/v1/receipts',{'recipient':'bob','through':1}),409,'CURSOR_INVALID','through')
        self.assertEqual(self.api('GET','/api/v1/users')[1],{'users':[]})
        self.api('POST','/api/v1/messages',self.message())
        self.assertEqual(self.api('POST','/api/v1/receipts',{'recipient':'bob','through':0})[1]['through'],0)
