"""Logging-only adapter around the byte-identical upstream argparse/main entrypoint."""
import json, pathlib, runpy, subprocess, sys, time
source=sys.argv.pop(1)
real_run=subprocess.run
calls=[]
def logged_run(*args,**kwargs):
    t=time.monotonic(); i=len(calls); item={'command':str(args[0]),'timeout_seconds':kwargs.get('timeout')}
    try:
        result=real_run(*args,**kwargs)
        item['returncode']=result.returncode
        pathlib.Path(f'yosys_{i}.stdout.log').write_text(result.stdout or '')
        pathlib.Path(f'yosys_{i}.stderr.log').write_text(result.stderr or '')
        return result
    except Exception as exc:
        item['exception_type']=type(exc).__name__
        raise
    finally:
        item['wall_seconds']=time.monotonic()-t; calls.append(item)
        pathlib.Path('subprocess_calls.json').write_text(json.dumps(calls,indent=2)+'\n')
subprocess.run=logged_run
sys.argv[0]=source
runpy.run_path(source,run_name='__main__')
