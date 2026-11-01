"""Archive committed source and real Git history, then verify restoration."""
import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path
from common import ROOT,execute,require,run_id,write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    if require(execute(['git','status','--porcelain']))['stdout'].strip():
        print('BLOCKED: commit the intended source before packaging.');return 2
    folder=ROOT/'artifacts/release'/run_id();folder.mkdir(parents=True)
    revision=require(execute(['git','rev-parse','HEAD']))['stdout'].strip()
    require(execute(['git','archive','--format=tar','--output',str(folder/'source.tar'),revision]))
    require(execute(['git','bundle','create',str(folder/'history.bundle'),'--all']))
    require(execute(['git','bundle','verify',str(folder/'history.bundle')]))
    files=require(execute(['git','ls-files']))['stdout'].splitlines()
    forbidden={'node_modules','dist','artifacts','var','__pycache__','.codex'}
    if any(forbidden.intersection(Path(name).parts) for name in files):raise RuntimeError('Archive includes disposable/private state')
    work=Path(tempfile.mkdtemp(prefix='spec-archive-check-',dir='/tmp'))
    require(execute(['git','clone',str(folder/'history.bundle'),str(work/'restored')],timeout=120))
    require(execute(['git','checkout','--detach',revision],cwd=work/'restored'))
    require(execute(['git','fsck','--full'],cwd=work/'restored'))
    hashes={}
    for name in files:
        data=(ROOT/name).read_bytes();hashes[name]=hashlib.sha256(data).hexdigest()
        if (work/'restored'/name).read_bytes()!=data:raise RuntimeError('Restored source differs: '+name)
    with tarfile.open(folder/'source.tar') as archive:
        if set(archive.getnames())!={*files,*[m.name for m in archive.getmembers() if m.isdir()]}:raise RuntimeError('Archive inventory mismatch')
        for name in files:
            if archive.extractfile(name).read()!=(ROOT/name).read_bytes():raise RuntimeError('Archive source differs: '+name)
    (folder/'RESTORE.txt').write_text(f'git clone history.bundle restored\ncd restored\ngit checkout --detach {revision}\npython3 scripts/setup.py\npython3 scripts/verify.py --suite all\n\nSee docs/STATUS.md for automated evidence and pending human review.\n')
    write_json(folder/'manifest.json',{'status':'PASS','revision':revision,'files':hashes,'history_restoration':'PASS'})
    bundle=folder.parent/(folder.name+'.tar.gz')
    with tarfile.open(bundle,'w:gz') as archive:
        for name in ('source.tar','history.bundle','RESTORE.txt','manifest.json'):archive.add(folder/name,arcname=name)
    print('Archive verified:',bundle);return 0


if __name__=='__main__':sys.exit(main())
