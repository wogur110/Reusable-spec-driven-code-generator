"""Prove reconstruction in a retained-only workspace; preserve the original tree."""
import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from common import ROOT,PYTHON,execute,now,run_id,write_json
sys.path.insert(0,str(ROOT))
from generator.core import Blocked,check_inventory,copy_files,inventory,retained_inventory,valid_test_report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    folder=ROOT/'artifacts/regeneration'/run_id();folder.mkdir(parents=True)
    report={'status':'IN_PROGRESS','started':now(),'commands':[],'environment_reuse':'Installed interpreters, /tmp/reusable-spec-playwright browser binaries, and /tmp/reusable-spec-native Ubuntu NSS/NSPR libraries; no prior client source.'}
    path=folder/'report.json';write_json(path,report);deadline=time.monotonic()+7200
    try:
        original=inventory(ROOT);frozen=retained_inventory(ROOT);report['input_hashes']=frozen
        before=inventory(ROOT/'generated',excluded=set()) if (ROOT/'generated').exists() else {}
        work=Path(tempfile.mkdtemp(prefix='spec-clean-regeneration-',dir='/tmp'));report['workspace']=str(work)
        copy_files(ROOT,work,frozen);assert not (work/'generated').exists() and not (work/'.git').exists()
        verification=work/'artifacts/standalone.json'
        commands=[([PYTHON,'scripts/setup.py'],600),([PYTHON,'generator/run.py','--target','all'],5400),([PYTHON,'scripts/setup.py','--skip-browser-install'],600),([PYTHON,'scripts/build.py','--target','all'],120),([PYTHON,'scripts/verify.py','--suite','all','--report',str(verification)],600)]
        for cmd,timeout in commands:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise RuntimeError('Outer proof deadline exceeded')
            record=execute(cmd,cwd=work,timeout=min(timeout,remaining));report['commands'].append(record)
            check_inventory(ROOT,original);check_inventory(work,frozen)
            if before!=(inventory(ROOT/'generated',excluded=set()) if (ROOT/'generated').exists() else {}):raise RuntimeError('Original generated source changed')
            write_json(path,report);print(record['stdout'][-5000:]+record['stderr'][-2000:],flush=True)
            if record['exit_code']==2:raise Blocked('Clean command blocked: '+json.dumps(cmd))
            if record['exit_code'] or record['timeout']:raise RuntimeError('Clean command failed: '+json.dumps(cmd))
        if not valid_test_report(verification):raise RuntimeError('Missing valid standalone acceptance evidence')
        report.update(status='PASS',acceptance=json.loads(verification.read_text()),original_tree_preserved=True,finished=now())
    except Exception as exc:report.update(status='BLOCKED' if isinstance(exc,Blocked) else 'FAIL',reason=str(exc),finished=now())
    write_json(path,report);print(report['status'],path);return {'PASS':0,'FAIL':1,'BLOCKED':2}[report['status']]


if __name__=='__main__':sys.exit(main())
