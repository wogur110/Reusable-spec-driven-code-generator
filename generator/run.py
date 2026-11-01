"""Generate selected targets from frozen specifications with bounded repair."""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from common import PYTHON,execute,now,run_id,write_json
from generator.core import (Blocked,IntegrityError,adapter_command,check_inventory,completed,copy_files,inventory,
                            load_config,output_inventory,publish,relative,retained_inventory,valid_test_report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec-root',default='specs');parser.add_argument('--config',default='generator/targets.json')
    parser.add_argument('--target',default='all');parser.add_argument('--model');parser.add_argument('--codex')
    args=parser.parse_args();folder=ROOT/'artifacts/generation'/run_id();folder.mkdir(parents=True)
    report={'status':'IN_PROGRESS','started':now(),'commands':[],'targets':{},'publication':'NOT_RUN','effective_model':'UNREPORTED'}
    report_path=folder/'report.json';write_json(report_path,report)
    deadline=time.monotonic()+5400
    def budget(limit):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise RuntimeError('Harness total deadline exceeded')
        return min(limit,remaining)
    try:
        config=load_config(ROOT,args.config,args.spec_root)
        selected=list(config['targets']) if args.target=='all' else [args.target]
        if any(name not in config['targets'] for name in selected):raise Blocked('Unknown target: '+args.target)
        deadline=time.monotonic()+config['total_timeout_seconds']
        model=args.model or config['agent'].get('model');binary=args.codex or config['agent']['binary']
        if '/' in binary:binary=str((ROOT/binary).resolve()) if not Path(binary).is_absolute() else binary
        elif not shutil.which(binary):raise Blocked('Coding tool is missing; run scripts/setup.py')
        if not model:raise Blocked('No model selected; verify account access and set agent.model or --model')
        frozen=inventory(ROOT)
        inputs=retained_inventory(ROOT,args.spec_root,config['context_files']+[args.config,config['agent']['template']])
        report.update(input_hashes=inputs,requested_model=model,scope=selected)
        revision=execute(['git','rev-parse','HEAD'],timeout=10);report['base_revision']=revision['stdout'].strip() if not revision['exit_code'] else None
        version=execute([binary,'--version'],timeout=budget(20));report['tool_version']=version['stdout'].strip();report['commands'].append(version)
        if version['exit_code']:raise Blocked('Coding tool unavailable: '+version['stderr'])
        workspace=Path(tempfile.mkdtemp(prefix='spec-generator-verify-',dir='/tmp'));report['verification_workspace']=str(workspace)
        copy_files(ROOT,workspace,inputs);verify_frozen=inventory(workspace)
        def integrity():
            check_inventory(ROOT,frozen);check_inventory(workspace,verify_frozen)
        def check(command,timeout,check_report=None):
            vector=[x.replace('{python}',PYTHON).replace('{report}',str(check_report or folder/'acceptance.json')) for x in command]
            record=execute(vector,cwd=workspace,timeout=budget(timeout));report['commands'].append(record)
            integrity();write_json(report_path,report)
            if record['exit_code']==2:raise Blocked(record['stdout'][-18000:]+record['stderr'][-10000:])
            if record['exit_code'] or record['timeout']:raise RuntimeError(record['stdout'][-18000:]+record['stderr'][-10000:])
            return record
        # Readiness is repeated in this invocation/account before freezing agent contexts.
        probe=Path(tempfile.mkdtemp(prefix='spec-generator-ready-',dir='/tmp'))
        preflight=execute(adapter_command(binary,model,probe),timeout=budget(120),stdin='Readiness check only: write readiness.txt containing READY in this workspace and reply READY. Do not read outside it, install anything, or delegate.\n')
        report['commands'].append(preflight);integrity()
        if not completed(preflight) or not (probe/'readiness.txt').is_file():raise Blocked('Authenticated writable preflight failed: '+preflight['stdout'][-4000:]+preflight['stderr'][-3000:])
        report['preflight']='PASS'
        candidates={};candidate_frozen={}
        for name in selected:
            target=config['targets'][name];candidate=Path(tempfile.mkdtemp(prefix='spec-generator-'+name+'-',dir='/tmp'))
            specs=[str(relative(args.spec_root)/relative(f)) for f in config['shared_specs']+config.get('extensions',[])+target['specs']]
            context=list(dict.fromkeys(config['context_files']))
            if not set(specs+context)<=set(inputs):raise Blocked('A declared context/spec is private or outside the retained input allowlist')
            copy_files(ROOT,candidate,dict.fromkeys(specs+context))
            candidate_frozen[name]=inventory(candidate,excluded=set(),disposable=False)
            candidates[name]=candidate
            report['targets'][name]={'workspace':str(candidate),'input_hashes':candidate_frozen[name],'rounds':[]}
        # Existing unselected source is visible only to trusted verification.
        for name,target in config['targets'].items():
            if name not in selected and (ROOT/target['output']).is_dir():copy_files(ROOT/target['output'],workspace/target['output'],output_inventory(ROOT/target['output']))
        diagnostics='';template=(ROOT/config['agent']['template']).read_text()
        for round_number in range(config['repair_rounds']+1):
            print(f'Generation round {round_number}',flush=True)
            round_failed=False
            for name in selected:
                target=config['targets'][name];candidate=candidates[name]
                specs=[str(relative(args.spec_root)/relative(f)) for f in config['shared_specs']+config.get('extensions',[])+target['specs']]
                prompt=template.format(target=name,output=target['output'],specs=json.dumps(specs),context=json.dumps(config['context_files']),
                    extensions=json.dumps(config.get('extensions',[])),required=json.dumps([f for f in target['required_files'] if f not in target.get('managed_lockfiles',[])]),
                    dependencies=json.dumps(config['dependency_policy']),checks=json.dumps(target['checks']),diagnostics=diagnostics[-22000:])
                record=execute(adapter_command(binary,model,candidate),timeout=budget(config['agent']['timeout_seconds']),stdin=prompt)
                report['targets'][name]['rounds'].append({'round':round_number,'command':record})
                actual=inventory(candidate,excluded=set(),disposable=False)
                prefix=target['output']+'/'
                retained={k:v for k,v in actual.items() if not k.startswith(prefix)}
                if retained!=candidate_frozen[name]:raise IntegrityError('Agent modified retained inputs or wrote outside target: '+name)
                integrity();write_json(report_path,report)
                if not completed(record):
                    text=record['stdout'][-6000:]+record['stderr'][-3000:]
                    if any(term in text.lower() for term in ('model_not_found','not supported when using codex','unauthorized','failed to initialize','read-only file system')):raise Blocked(text)
                    diagnostics=f'Target {name} did not complete successfully. {text}';round_failed=True;continue
                output=candidate/target['output']
                files=output_inventory(output)
                missing=[f for f in target['required_files'] if f not in target.get('managed_lockfiles',[]) and f not in files]
                if missing:diagnostics=f'Target {name} missing authored files: {missing}';round_failed=True;continue
                destination=workspace/target['output']
                if destination.exists():shutil.rmtree(destination)
                copy_files(output,destination,files)
                for lock in target.get('managed_lockfiles',[]):
                    (destination/lock).unlink(missing_ok=True)
                report['targets'][name]['source_hashes']=files
            if round_failed:continue
            try:
                check(config['setup_command'],600)
                for name in selected:
                    target=config['targets'][name]
                    for f in target['required_files']:
                        if not (workspace/target['output']/f).is_file():raise RuntimeError('Missing post-setup required output: '+f)
                    for command in target['checks']:check(command,120)
                all_present=all((workspace/t['output']).is_dir() for t in config['targets'].values())
                if all_present:
                    result_path=workspace/'artifacts/baseline.json'
                    check(config['verify_command'],config['verify_timeout_seconds'],result_path)
                    if not valid_test_report(result_path):raise RuntimeError('Missing, empty, skipped, flaky, or failing acceptance report')
                    report['acceptance']=json.loads(result_path.read_text());report['interoperability']='PASS'
                else:report['interoperability']='NOT_RUN'
                integrity()
                replacements={config['targets'][name]['output']:workspace/config['targets'][name]['output'] for name in selected}
                publish(ROOT,replacements,folder/'publication')
                check_inventory(ROOT,frozen)
                for name in selected:report['targets'][name]['published_hashes']=output_inventory(ROOT/config['targets'][name]['output'])
                report.update(status='PASS',publication='PASS',finished=now());write_json(report_path,report)
                print('Generation PASS:',report_path);return 0
            except (IntegrityError,Blocked):raise
            except RuntimeError as exc:
                diagnostics=str(exc);report['last_failure']=diagnostics[-22000:];write_json(report_path,report)
                print('Candidate validation failed; bounded repair will use the frozen contract.',flush=True)
        raise RuntimeError('Repair budget exhausted. '+diagnostics)
    except (Blocked,FileNotFoundError,json.JSONDecodeError,KeyError,TypeError) as exc:
        report.update(status='BLOCKED',reason=str(exc),finished=now());code=2
    except (RuntimeError,OSError,ValueError) as exc:
        report.update(status='FAIL',reason=str(exc),finished=now());code=1
    write_json(report_path,report);print(report['status']+': '+report['reason']);print(report_path);return code


if __name__=='__main__':sys.exit(main())
