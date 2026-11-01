"""Launch a fresh local server and print the exact second-terminal command."""
import argparse
import json
import shlex
import subprocess
import sys
from common import ROOT,PYTHON,run_id


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    if not (ROOT/'generated/typescript-web/dist/index.html').is_file() or not (ROOT/'generated/python-client/main.py').is_file():
        print('Generate both clients, then run python3 scripts/setup.py and python3 scripts/build.py --target all.',file=sys.stderr);return 2
    child=subprocess.Popen([PYTHON,'server/main.py','--port',str(args.port),'--static-dir','generated/typescript-web/dist'],cwd=ROOT,stdout=subprocess.PIPE,text=True)
    try:
        line=child.stdout.readline()
        if not line:return child.wait() or 1
        ready=json.loads(line);origin=ready['origin'];state='var/demo/'+run_id()+'/alice'
        print('Browser URL:',origin,flush=True)
        print('Use a fresh private browser window; log in as bob.',flush=True)
        print('In another terminal: '+shlex.join(['python3','generated/python-client/main.py','--server',origin,'--state-dir',state]),flush=True)
        print('At the Python Username prompt enter alice. Keep this server running during the walkthrough.',flush=True)
        return child.wait()
    except KeyboardInterrupt:return 0
    finally:
        if child.poll() is None:child.terminate();child.wait(timeout=5)


if __name__=='__main__':sys.exit(main())
