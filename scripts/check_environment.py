"""Read-only prerequisite checks; never performs a model request or installation."""
import argparse
import json
import os
import shutil
import sqlite3
import sys
from common import ROOT, browser_env, execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation', action='store_true')
    args = parser.parse_args()
    result = {'python': sys.version.split()[0], 'sqlite': sqlite3.sqlite_version, 'missing': [], 'commands': [], 'model_access': 'UNVERIFIED'}
    if sys.version_info < (3, 10): result['missing'].append('Python >=3.10')
    for binary in ('node', 'npm', 'git'):
        record = execute([binary, '--version'], timeout=10)
        result['commands'].append(record)
        if record['exit_code']: result['missing'].append(binary)
        elif binary == 'node' and int(record['stdout'].strip().lstrip('v').split('.')[0]) < 22: result['missing'].append('Node >=22')
    if not (ROOT/'tests/node_modules/@playwright/test').is_dir(): result['missing'].append('Retained test dependencies: run scripts/setup.py')
    else:
        probe="const {chromium}=require('./tests/node_modules/@playwright/test');(async()=>{const b=await chromium.launch({headless:true});console.log(b.version());await b.close();})().catch(e=>{console.error(e.message);process.exitCode=1;});"
        record=execute(['node','-e',probe],timeout=30,env=browser_env());result['commands'].append(record)
        if record['exit_code'] or record['timeout']:result['missing'].append('Chromium/browser native prerequisites; run scripts/setup.py and inspect the launch diagnostic')
    if args.generation:
        binary = ROOT/'generator/codex/node_modules/.bin/codex'
        for suffix in (['--version'], ['exec', '--help'], ['login', 'status']):
            record = execute([str(binary), *suffix], timeout=20)
            result['commands'].append(record)
            if record['exit_code']: result['missing'].append('Codex ' + ' '.join(suffix))
    result['status'] = 'BLOCKED' if result['missing'] else 'PASS'
    print(json.dumps(result, indent=2)); return 2 if result['missing'] else 0


if __name__ == '__main__':
    sys.exit(main())
