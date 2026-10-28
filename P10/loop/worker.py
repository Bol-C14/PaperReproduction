import json,resource,sys,time
from circuits import workload
from engine import optimize
t=time.process_time()
try:
    r=optimize(workload(sys.argv[1],int(sys.argv[2])),sys.argv[3])
    if len(sys.argv)>4 and sys.argv[4]=='dag':
        from dag_extract import select
        r['tree_variants']=r['variants'];r['variants'],r['dag_reports']=select(r['egraph'])
    r['cpu_seconds']=time.process_time()-t
    r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(r))
except Exception as exc:
    print(json.dumps({'error':repr(exc),'cpu_seconds':time.process_time()-t}));raise
