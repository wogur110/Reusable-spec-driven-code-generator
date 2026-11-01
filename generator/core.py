"""Generic retained-input, tool-adapter, and atomic-publication primitives."""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import execute

DISPOSABLE={'node_modules','dist','__pycache__'}
TOP_EXCLUDED={'.git','artifacts','var','generated'}
RETAINED_DIRS={'generator','server','tests','scripts','specs','docs'}


class Blocked(RuntimeError): pass
class IntegrityError(RuntimeError): pass


def relative(value):
    if not isinstance(value,str) or not value or '\\' in value:
        raise Blocked('Expected a safe relative path')
    p=Path(value)
    if p.is_absolute() or any(x in ('..','.') for x in p.parts) or str(p)!=value:
        raise Blocked('Unsafe relative path: '+value)
    return p


def inventory(root, excluded=TOP_EXCLUDED, disposable=True):
    root=Path(root);result={}
    for current,dirs,files in os.walk(root,followlinks=False):
        current=Path(current)
        for name in list(dirs):
            path=current/name;rel=path.relative_to(root)
            if path.is_symlink(): raise IntegrityError('Source symlink: '+str(rel))
            if (len(rel.parts)==1 and name in excluded) or (disposable and name in DISPOSABLE):dirs.remove(name)
        for name in files:
            path=current/name;rel=path.relative_to(root)
            if path.is_symlink():raise IntegrityError('Source symlink: '+str(rel))
            if len(rel.parts)==1 and name in excluded:continue
            result[str(rel)]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def check_inventory(root,expected,**kwargs):
    actual=inventory(root,**kwargs)
    if actual!=expected:
        changes=sorted(k for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k))
        raise IntegrityError('Retained inventory changed: '+', '.join(changes))


def retained_inventory(root,spec_root='specs',extra_files=()):
    """Copy only declared source families; private/unregistered files are not inputs."""
    result={};spec_parts=relative(spec_root).parts
    for name,digest in inventory(root).items():
        p=Path(name);parts=p.parts
        private=any(part in ('.codex','.aws','.ssh','auth.json','.npmrc','.netrc') or part.startswith('.env') for part in parts)
        if private or p.suffix in ('.pem','.key'):continue
        allowed=(parts[0] in RETAINED_DIRS or parts[:len(spec_parts)]==spec_parts or name in extra_files or (len(parts)==1 and (p.suffix=='.md' or name=='.gitignore')))
        if allowed:result[name]=digest
    return result


def copy_files(source,destination,files):
    for name in files:
        p=relative(name);src=source/p
        if src.is_symlink() or not src.is_file():raise IntegrityError('Missing or symlink input: '+name)
        dst=destination/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def load_config(root,config_path,spec_root):
    config=json.loads((root/relative(config_path)).read_text())
    if config.get('version')!=1 or not isinstance(config.get('targets'),dict) or not config['targets']:raise Blocked('Invalid target configuration')
    for key in ('repair_rounds','total_timeout_seconds','verify_timeout_seconds'):
        value=config.get(key)
        if type(value)!=int or value<0 or (key!='repair_rounds' and value==0):raise Blocked('Invalid bound: '+key)
    if config['repair_rounds']>3 or config['total_timeout_seconds']>5400 or config['verify_timeout_seconds']>600:raise Blocked('Configured bounds exceed the documented limits')
    agent=config.get('agent',{})
    if agent.get('tool')!='codex' or type(agent.get('timeout_seconds'))!=int or not 1<=agent['timeout_seconds']<=600:raise Blocked('Unsupported adapter or agent timeout')
    relative(agent['template']);outputs=set()
    for name,target in config['targets'].items():
        out=relative(target['output'])
        if len(out.parts)!=2 or out.parts[0]!='generated' or out in outputs:raise Blocked('Output boundaries must be unique direct children of generated/')
        outputs.add(out)
        if not target.get('required_files'):raise Blocked('Required output inventory is empty')
        for f in target['required_files']+target.get('managed_lockfiles',[]):relative(f)
        if not set(target.get('managed_lockfiles',[]))<=set(target['required_files']):raise Blocked('Managed locks must be declared outputs')
        for command in target.get('checks',[]):validate_command(command)
        if not target.get('checks'):raise Blocked('Target checks are required')
        for f in config['shared_specs']+config.get('extensions',[])+target['specs']:
            p=root/relative(spec_root)/relative(f)
            if not p.is_file() or p.is_symlink():raise Blocked('Missing registered spec: '+str(f))
    for f in config['context_files']+[agent['template']]:
        if not (root/relative(f)).is_file():raise Blocked('Missing context: '+f)
    validate_command(config['setup_command']);validate_command(config['verify_command'])
    return config


def validate_command(command):
    if not isinstance(command,list) or not command or any(not isinstance(x,str) or not x for x in command):raise Blocked('Commands must be nonempty argument vectors')


def adapter_command(binary,model,workspace):
    if not model:raise Blocked('Select a verified model with --model or agent.model; no model entitlement is assumed')
    return [str(binary),'exec','--sandbox','workspace-write','--ephemeral','--skip-git-repo-check','--json','--color','never','-C',str(workspace),'--model',model,'-']


def completed(record):
    if record['exit_code'] or record['timeout']:return False
    try:events=[json.loads(line) for line in record['stdout'].splitlines() if line.strip()]
    except ValueError:return False
    return bool(events) and all(isinstance(e,dict) for e in events) and any(e.get('type')=='turn.completed' for e in events) and not any(e.get('type') in ('turn.failed','error') for e in events)


def valid_test_report(path):
    try:
        d=json.loads(path.read_text())
        return isinstance(d,dict) and d.get('status')=='PASS' and type(d.get('collected'))==int and d['collected']>0 and type(d.get('passed'))==int and d['passed']==d['collected'] and all(d.get(k,0)==0 for k in ('failed','skipped','flaky'))
    except (OSError,ValueError):return False


def output_inventory(path):
    if path.is_symlink() or not path.is_dir():raise IntegrityError('Missing output or symlink: '+str(path))
    return inventory(path,excluded=set(),disposable=True)


def publish(root,candidates,backup_root,replace=os.replace):
    """Copy source-only candidates, then replace selected outputs with rollback."""
    backup_root.mkdir(parents=True,exist_ok=True);stages={};backups={};installed=[]
    for output,source in candidates.items():
        relative(output);files=output_inventory(source);stage=backup_root/('stage-'+Path(output).name)
        copy_files(source,stage,files);stages[output]=stage
    try:
        for output,stage in stages.items():
            dest=root/relative(output);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.is_symlink():raise IntegrityError('Published output is a symlink')
            if dest.exists():
                backup=backup_root/('old-'+dest.name);replace(dest,backup);backups[output]=backup
            replace(stage,dest);installed.append(output)
    except BaseException:
        for output in reversed(installed):shutil.rmtree(root/output)
        for output,backup in backups.items():
            if backup.exists():os.replace(backup,root/output)
        raise
