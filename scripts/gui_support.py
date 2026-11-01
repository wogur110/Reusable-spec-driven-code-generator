"""Native desktop prerequisites and isolated displays for retained GUI checks."""
import contextlib
import os
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

def gui_env(base=None):
    return dict(os.environ if base is None else base)


@contextlib.contextmanager
def virtual_display(base=None):
    """Always use a private test display, never interact with the user's desktop."""
    env = gui_env(base)
    binary = shutil.which('Xvfb', path=env.get('PATH'))
    if not binary:
        raise RuntimeError('Xvfb is missing; run python3 scripts/setup.py or install native GUI prerequisites.')
    if not shutil.which('xdpyinfo', path=env.get('PATH')):
        raise RuntimeError('xdpyinfo is missing; install x11-utils.')
    for _ in range(20):
        display = str(random.SystemRandom().randrange(100, 60000))
        if not Path('/tmp/.X'+display+'-lock').exists():
            break
    else:
        raise RuntimeError('Could not allocate a private display number.')
    env['DISPLAY'] = ':' + display
    env.pop('WAYLAND_DISPLAY', None)
    process = None
    diagnostic = tempfile.TemporaryFile()
    try:
        # WSLg's shared .X11-unix directory may reject filesystem listeners.
        # Explicit numbering allows the normal Linux abstract socket listener.
        process = subprocess.Popen([binary, env['DISPLAY'], '-screen', '0', '1280x900x24', '-nolisten', 'tcp', '-ac'],
                                   stdout=subprocess.DEVNULL, stderr=diagnostic, env=env)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and process.poll() is None:
            probe = subprocess.run(['xdpyinfo'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            if probe.returncode == 0:
                break
            time.sleep(.05)
        else:
            diagnostic.seek(0)
            raise RuntimeError('Xvfb startup failed: '+diagnostic.read(4000).decode(errors='replace'))
        yield env
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
        diagnostic.close()
