"""Build selected published/candidate sources without generating them."""
import argparse
import os
import sys
from common import ROOT, PYTHON, execute, now, run_id, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=['all', 'python', 'typescript'], default='all')
    args = parser.parse_args()
    report = {'status': 'IN_PROGRESS', 'started': now(), 'commands': []}
    path = ROOT/'artifacts/build'/run_id()/'report.json'
    commands = []
    if args.target in ('all', 'python'):
        entry = ROOT/'generated/python-client/main.py'
        if not entry.is_file():
            report.update(status='BLOCKED', reason='Python client has not been generated.'); write_json(path, report); print(report['reason']); return 2
        commands += [[PYTHON, '-m', 'compileall', '-q', 'generated/python-client'], [PYTHON, str(entry), '--help']]
    if args.target in ('all', 'typescript'):
        if not (ROOT/'generated/typescript-web/package.json').is_file():
            report.update(status='BLOCKED', reason='TypeScript client has not been generated.'); write_json(path, report); print(report['reason']); return 2
        commands += [['npm', '--prefix', 'generated/typescript-web', 'run', name] for name in ('typecheck', 'build')]
    for cmd in commands:
        record = execute(cmd, timeout=120)
        report['commands'].append(record)
        if record['exit_code'] or record['timeout']:
            report['status'] = 'FAIL'; write_json(path, report); print(record['stdout']+record['stderr']); return 1
    if args.target in ('all', 'typescript') and not (ROOT/'generated/typescript-web/dist/index.html').is_file():
        report.update(status='FAIL', reason='Build did not create dist/index.html'); write_json(path, report); return 1
    report.update(status='PASS', finished=now()); write_json(path, report)
    print('Build PASS:', args.target); return 0


if __name__ == '__main__':
    sys.exit(main())
