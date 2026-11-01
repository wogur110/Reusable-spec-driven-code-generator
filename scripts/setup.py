"""Install declared tools and present client dependencies, including from an empty generated tree."""
import argparse
import ctypes
import os
import shutil
import sys
from pathlib import Path
from common import ROOT, browser_env, execute, now, run_id, write_json
from gui_support import virtual_display


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-browser-install', action='store_true')
    args = parser.parse_args()
    report = {'status': 'IN_PROGRESS', 'started': now(), 'commands': []}
    path = ROOT/'artifacts/setup'/run_id()/'report.json'
    try:
        # Install native GUI packages through the OS package manager before setup.
        # Extracting Xvfb alone is insufficient: it invokes /usr/bin/xkbcomp.
        for binary in ('Xvfb', 'xkbcomp', 'xwininfo'):
            if not shutil.which(binary):
                raise RuntimeError(binary+' is missing. On Ubuntu/WSL run: sudo apt-get install -y python3-tk xvfb x11-xkb-utils x11-utils')
        with virtual_display() as display_env:
            record = execute([sys.executable, '-c', 'import tkinter as t; r=t.Tk(); print(r.tk.call("info", "patchlevel"), r.tk.call("package", "provide", "Tk")); r.destroy()'], env=display_env, timeout=15)
        report['commands'].append(record)
        if record['exit_code'] or record['timeout']:raise RuntimeError(record['stderr']+' Install python3-tk for this interpreter.')
    except Exception as exc:
        report.update(status='BLOCKED', reason='GUI prerequisites: '+str(exc));write_json(path,report);print(report['reason']);return 2
    env = browser_env()
    env.setdefault('npm_config_cache', str(ROOT/'artifacts/npm-cache'))
    env.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/tmp/reusable-spec-playwright')
    directories = [ROOT/'tests', ROOT/'generator/codex']
    directories += [p.parent for p in (ROOT/'generated').glob('*/package.json')]
    for directory in directories:
        action = 'ci' if (directory/'package-lock.json').is_file() else 'install'
        record = execute(['npm', action, '--no-audit', '--no-fund'], cwd=directory, timeout=600, env=env)
        report['commands'].append(record)
        if record['exit_code'] or record['timeout']:
            report['status'] = 'BLOCKED'; write_json(path, report)
            print(record['stderr'], file=sys.stderr); print(path); return 2
    if not args.skip_browser_install:
        record = execute(['node', 'node_modules/@playwright/test/cli.js', 'install', 'chromium'], cwd=ROOT/'tests', timeout=600, env=env)
        report['commands'].append(record)
        if record['exit_code'] or record['timeout']:
            report['status'] = 'BLOCKED'; write_json(path, report)
            print(record['stderr'], file=sys.stderr); print(path); return 2
        try:
            ctypes.CDLL('libnss3.so'); ctypes.CDLL('libnspr4.so')
        except OSError:
            # Ubuntu/WSL fallback: use distribution packages locally, without root.
            native = Path('/tmp/reusable-spec-native'); native.mkdir(exist_ok=True)
            if not (native/'usr/lib/x86_64-linux-gnu/libnss3.so').exists():
                record = execute(['apt-get', 'download', 'libnspr4', 'libnss3'], cwd=native, timeout=120)
                report['commands'].append(record)
                if record['exit_code']:
                    report.update(status='BLOCKED', reason='Install browser native dependencies for this operating system.'); write_json(path, report); print(record['stderr']); return 2
                for package in native.glob('*.deb'):
                    record=execute(['dpkg-deb','-x',str(package),str(native)],timeout=60)
                    report['commands'].append(record)
                    if record['exit_code']:report['status']='BLOCKED';write_json(path,report);return 2
            report['local_native_libraries']=str(native)
    report.update(status='PASS', finished=now(), browser_path=env['PLAYWRIGHT_BROWSERS_PATH'])
    write_json(path, report); print('Setup PASS:', path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
