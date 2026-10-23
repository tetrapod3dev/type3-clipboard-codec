import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run_case(case,trace=False,timeout=3,before_scan=False):
    # Use the real interpreter, not Windows venv launcher/shim: Popen owns the exact child.
    command=[sys._base_executable,str(HERE/'child_decoder.py'),'--case',case]
    if trace:command.append('--trace')
    if before_scan:command.append('--before-scan')
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    p=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    start=time.monotonic();timed_out=False
    try:stdout,stderr=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out=True;p.kill();stdout,stderr=p.communicate(timeout=5)
    rows=[json.loads(line) for line in stdout.decode('utf8').splitlines() if line.strip()]
    if rows:assert rows[0]['pid']==p.pid, 'Unexpected interpreter launcher; do not reuse this setup'
    return {'case':case,'parent_pid':os.getpid(),'child_pid':p.pid,'command':command,'timeout_limit_seconds':timeout,'timed_out':timed_out,'returncode':p.returncode,'elapsed_seconds':time.monotonic()-start,'events':rows,'stderr':stderr.decode('utf8',errors='replace'),'kill_scope':'Popen handle for this child only' if timed_out else 'none'}
if __name__=='__main__':
    result=run_case('count_stride_extent_truncated',trace=True,timeout=2)
    with (HERE/'reproduction-before.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
