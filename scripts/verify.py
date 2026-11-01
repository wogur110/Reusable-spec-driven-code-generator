"""Run retained suites and reject missing, skipped, flaky, or zero-test results."""
import argparse
import json
import os
import sys
from pathlib import Path
from common import ROOT, PYTHON, browser_env, execute, input_hashes, now, run_id, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['all', 'protocol', 'python-interface', 'harness'], default='all')
    parser.add_argument('--report', type=str)
    args = parser.parse_args()
    directory = ROOT/'artifacts/verification'/run_id(); directory.mkdir(parents=True)
    destination = Path(args.report).resolve() if args.report else directory/'report.json'
    report = {'status': 'IN_PROGRESS', 'suite': args.suite, 'started': now(), 'input_hashes': input_hashes(), 'commands': [], 'collected': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'flaky': 0}
    write_json(destination, report)
    if args.suite == 'all':
        readiness=execute([PYTHON,'scripts/check_environment.py'],timeout=60)
        report['commands'].append(readiness)
        if readiness['exit_code'] or readiness['timeout']:
            report.update(status='BLOCKED',finished=now());write_json(destination,report);print(readiness['stdout']+readiness['stderr']);return 2
    if args.suite in ('all', 'python-interface'):
        record = execute([PYTHON, 'scripts/build.py', '--target', 'all' if args.suite == 'all' else 'python'], timeout=120)
        report['commands'].append(record)
        if record['exit_code'] or record['timeout']:
            report.update(status='BLOCKED' if record['exit_code']==2 else 'FAIL', finished=now());write_json(destination,report);print(record['stdout']+record['stderr']);return 2 if record['exit_code']==2 else 1
    suites = ['protocol', 'python_interface'] if args.suite == 'all' else [args.suite.replace('-', '_')]
    for name in suites:
        subreport = directory/(name+'.json')
        record = execute([PYTHON, 'tests/run_unittest.py', 'tests/'+name, '--report', str(subreport)], timeout=120)
        report['commands'].append(record)
        print(record['stdout']+record['stderr'], end='')
        if subreport.exists():
            data=json.loads(subreport.read_text())
            for key in ('collected','passed','failed','skipped'):report[key]+=data[key]
        if record['exit_code'] or record['timeout']:
            report.update(status='FAIL',finished=now());write_json(destination,report);print(destination);return 1
    if args.suite == 'all':
        browser_report=directory/'browser.json';env=browser_env()
        env.update(TEST_JSON_REPORT=str(browser_report), TEST_ARTIFACTS=str(directory/'browser'), TEST_PYTHON=PYTHON)
        env.setdefault('PLAYWRIGHT_BROWSERS_PATH','/tmp/reusable-spec-playwright')
        record=execute(['node','node_modules/@playwright/test/cli.js','test','--config','playwright.config.js'],cwd=ROOT/'tests',timeout=600,env=env)
        report['commands'].append(record);print(record['stdout']+record['stderr'],end='')
        if browser_report.exists():
            stats=json.loads(browser_report.read_text()).get('stats',{})
            report['passed']+=stats.get('expected',0);report['failed']+=stats.get('unexpected',0)
            report['skipped']+=stats.get('skipped',0);report['flaky']+=stats.get('flaky',0)
            report['collected']+=sum(stats.get(k,0) for k in ('expected','unexpected','skipped','flaky'))
        else:report['failed']+=1
        if record['exit_code'] or record['timeout']:report['failed']=max(1,report['failed'])
    unchanged = report['input_hashes'] == input_hashes()
    good=unchanged and report['collected']>0 and not any(report[k] for k in ('failed','skipped','flaky'))
    report.update(status='PASS' if good else 'FAIL',retained_tests_unchanged=unchanged,finished=now())
    write_json(destination,report);print(report['status'],report['collected'],'tests:',destination)
    return 0 if good else 1


if __name__ == '__main__':
    sys.exit(main())
