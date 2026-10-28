"""One independent routed OpenRCX measurement; not optimization or signoff."""
import os,pathlib,subprocess,json,time,hashlib,re
r=pathlib.Path(os.environ['E4_WORK_ROOT']);o=r/'results/fluxbench/route1200-v1';data=r/'assets/pdagent/dataset/PlaceReasoner-Bench/bp_fe';a=r/'assets/fluxbench/official-nangate'
assert hashlib.sha256((o/'route.odb').read_bytes()).hexdigest()==json.load(open(o/'result.json'))['artifacts']['route.odb']['sha256']
s='''read_liberty /data/lib/NangateOpenCellLibrary_typical.lib
read_db /out/route.odb
read_sdc /out/port.sdc
set_thread_count 4
set_propagated_clock [all_clocks]
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file /assets/rcx_patterns.rules
write_spef /out/extracted.spef
report_worst_slack -max
report_worst_slack -min
report_tns
report_checks -path_delay max -group_count 1
'''
(o/'extract.tcl').write_text(s);cpus=','.join(str(x) for x in sorted(os.sched_getaffinity(0))[:4]);name='e4-fluxbench-extraction-v1'
cmd=['taskset','-c',cpus,'podman','run','--name',name,'--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--pids-limit=128','--memory=8g','--tmpfs=/tmp:rw,nosuid,size=128m','-e','OMP_NUM_THREADS=4','-e','QT_QPA_PLATFORM=minimal','-v',str(data)+':/data:ro','-v',str(a)+':/assets:ro','-v',str(o)+':/out:rw','080c40706b37fb2fece6a61412d17c0e025ee87af82af28e79aa90f5d02a78ac','-no_init','-exit','/out/extract.tcl']
t=time.monotonic();p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(o/'extract.log').write_bytes(p.stdout)
sp=o/'extracted.spef';d=dict(command=cmd,seconds=time.monotonic()-t,returncode=p.returncode,measurement='OpenRCX research-model extracted timing, not foundry signoff',spef_bytes=sp.stat().st_size if sp.exists() else 0,spef_sha256=hashlib.sha256(sp.read_bytes()).hexdigest() if sp.exists() else None,d_net_count=len(re.findall(rb'^\*D_NET ',sp.read_bytes(),re.M)) if sp.exists() else 0)
(o/'extract.json').write_text(json.dumps(d,indent=2)+'\n');assert p.returncode==0
