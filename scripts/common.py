"""Shared process/report utilities; no messaging implementation."""
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def now():
    return datetime.now(timezone.utc).isoformat()


def run_id():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def browser_env():
    env = dict(os.environ)
    env.setdefault('PLAYWRIGHT_BROWSERS_PATH', '/tmp/reusable-spec-playwright')
    native = Path('/tmp/reusable-spec-native/usr/lib/x86_64-linux-gnu')
    if native.is_dir():
        env['LD_LIBRARY_PATH'] = str(native) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    return env


def redact(value):
    value = re.sub(r'(?i)(bearer\s+)[^\s"\']+', r'\1[REDACTED]', value)
    return re.sub(r'\bsk-[A-Za-z0-9_-]{12,}', '[REDACTED]', value)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n')
    tmp.replace(path)


def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def execute(argv, cwd=ROOT, timeout=120, stdin=None, env=None):
    start = time.monotonic()
    record = {'command': list(map(str, argv)), 'started': now(), 'timeout': False}
    try:
        process = subprocess.Popen(record['command'], cwd=cwd, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                                   start_new_session=True, env=env)
        try:
            out, err = process.communicate(stdin, timeout=max(.01, timeout))
        except subprocess.TimeoutExpired:
            record['timeout'] = True
            stop(process)
            out, err = process.communicate()
        record.update(exit_code=process.returncode, stdout=redact(out), stderr=redact(err))
    except OSError as exc:
        record.update(exit_code=127, stdout='', stderr=str(exc))
    record['duration_seconds'] = round(time.monotonic() - start, 3)
    return record


def require(record):
    if record['exit_code'] or record['timeout']:
        raise RuntimeError(json.dumps(record, ensure_ascii=True))
    return record


def fingerprint(paths, base=ROOT):
    return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file()}


def input_hashes():
    paths = [p for folder in ('specs', 'tests') for p in (ROOT / folder).rglob('*')
             if p.is_file() and not any(x in p.parts for x in ('node_modules', '__pycache__', 'test-results'))]
    return fingerprint(paths)
