"""AT-18: controlled failures cannot become successful publications."""
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from generator.core import (Blocked,IntegrityError,check_inventory,completed,copy_files,inventory,load_config,output_inventory,publish,relative,retained_inventory,valid_test_report)
from scripts.common import execute

ROOT=Path(__file__).resolve().parents[2]


class Guards(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def test_AT18_paths(self):
        for value in ('../escape','/absolute','generated/../escape','generated\\escape',''):
            with self.subTest(value=value),self.assertRaises(Blocked):relative(value)

    def test_AT18_added_removed_changed_retained_files(self):
        path=self.root/'input.md';path.write_text('frozen');frozen=inventory(self.root)
        path.write_text('changed')
        with self.assertRaises(IntegrityError):check_inventory(self.root,frozen)
        path.unlink()
        with self.assertRaises(IntegrityError):check_inventory(self.root,frozen)
        path.write_text('frozen');(self.root/'new.md').write_text('unexpected')
        with self.assertRaises(IntegrityError):check_inventory(self.root,frozen)

    def test_AT18_source_symlinks_and_missing_output(self):
        (self.root/'link').symlink_to('/etc/passwd')
        with self.assertRaises(IntegrityError):inventory(self.root)
        with self.assertRaises(IntegrityError):output_inventory(self.root/'missing')

    def test_AT18_completion_requires_event_and_success(self):
        def record(out,code=0,timeout=False):return {'stdout':out,'exit_code':code,'timeout':timeout}
        for item in [record(''),record('not-json'),record('null\n'),record('[]\n'),record('{"type":"turn.started"}\n'),record('{"type":"turn.completed"}\n',1),record('{"type":"turn.completed"}\n',0,True),record('{"type":"turn.completed"}\n{"type":"turn.failed"}\n')]:self.assertFalse(completed(item))
        self.assertTrue(completed(record('{"type":"turn.started"}\n{"type":"turn.completed"}\n')))

    def test_AT18_reports_reject_zero_skips_and_flaky(self):
        path=self.root/'report.json'
        self.assertFalse(valid_test_report(path))
        for changes in ({'collected':0},{'passed':0},{'skipped':1},{'failed':1},{'flaky':1},{'status':'IN_PROGRESS'}):
            path.write_text(json.dumps({'status':'PASS','collected':1,'passed':1,'failed':0,'skipped':0,'flaky':0,**changes}));self.assertFalse(valid_test_report(path))
        path.write_text(json.dumps({'status':'PASS','collected':1,'passed':1,'failed':0,'skipped':0,'flaky':0}));self.assertTrue(valid_test_report(path))

    def test_AT18_snapshot_excludes_private_and_unregistered_inputs(self):
        (self.root/'README.md').write_text('public')
        (self.root/'.env').write_text('not a generation input')
        (self.root/'notes.txt').write_text('unregistered')
        (self.root/'tests').mkdir();(self.root/'tests/oracle.py').write_text('assert True')
        (self.root/'tests/auth.json').write_text('private')
        snapshot=retained_inventory(self.root)
        self.assertEqual(set(snapshot),{'README.md','tests/oracle.py'})

    def test_AT18_config_boundaries(self):
        inputs=inventory(ROOT);copy_files(ROOT,self.root,inputs)
        baseline=json.loads((self.root/'generator/targets.json').read_text())
        for output in ('../escape','generated/a/b',baseline['targets']['python']['output']):
            data=copy.deepcopy(baseline);data['targets']['typescript']['output']=output
            (self.root/'generator/targets.json').write_text(json.dumps(data))
            with self.assertRaises(Blocked):load_config(self.root,'generator/targets.json','specs')
        data=copy.deepcopy(baseline);data['repair_rounds']=4;(self.root/'generator/targets.json').write_text(json.dumps(data))
        with self.assertRaises(Blocked):load_config(self.root,'generator/targets.json','specs')

    def test_AT18_publication_rolls_back_both_targets(self):
        sources={}
        for name in ('one','two'):
            old=self.root/'generated'/name;old.mkdir(parents=True);(old/'source.txt').write_text('old '+name)
            new=self.root/'candidates'/name;new.mkdir(parents=True);(new/'source.txt').write_text('new '+name)
            sources['generated/'+name]=new
        calls=[]
        def faulty(src,dest):
            calls.append((src,dest))
            if Path(src).name=='stage-two':raise OSError('Injected second publication failure')
            os.replace(src,dest)
        with self.assertRaises(OSError):publish(self.root,sources,self.root/'backups',replace=faulty)
        for name in ('one','two'):self.assertEqual((self.root/'generated'/name/'source.txt').read_text(),'old '+name)

    def test_AT18_process_timeout(self):
        result=execute([sys.executable,'-c','import time; time.sleep(30)'],cwd=self.root,timeout=.1)
        self.assertTrue(result['timeout']);self.assertNotEqual(result['exit_code'],0);self.assertLess(result['duration_seconds'],6)
