"""Read-only audit of frozen RQ1 outputs; writes a small evidence summary."""
from pathlib import Path
import hashlib,json,re
P=Path(__file__).resolve().parents[1];L=P/'logs'
rows=[]
for name in ['noop_1','default_1','noop_confirmation']:
 d=L/name;s=(d/'stdout.log').read_text();cmd=json.loads((d/'command.json').read_text())
 # Tool-issued commands only; the preceding help text mentions many unexecuted options.
 issued=re.findall(r'^Command: (.*)$',s,re.M)
 phases=re.findall(r'^Phase (\d+) ([^|\n]+?)(?: \| Checksum: ([0-9a-f]+))?$',s,re.M)
 route_s=s[s.index('Command: route_design\n'):]
 row={'arm':name,'argv':cmd,'executed_route_commands':[x for x in issued if x.startswith('route_design')],'executed_physopt_commands':[x for x in issued if x.startswith('phys_opt_design')],'fresh_process_start':re.search(r'Start of session at: (.*)',s)[1],'max_route_cpus':re.findall(r'Multithreading enabled for route_design using a maximum of (\d+) CPUs',s),'physopt_ms':int(re.search(r'RQ1_PHYSOPT_MS=(\d+)',s)[1]),'route_ms':int(re.search(r'RQ1_ROUTE_MS=(\d+)',s)[1]),'route_phase_names':[m[1].strip() for m in re.findall(r'^Phase (\d+) ([^|\n]+)$',route_s,re.M)],'restored_netlist_device_cache':all(x in s for x in ['Read Netlist Cache:','Read Device Cache:']),'implicit_physical_synthesis_in_router':'Phase 14 Physical Synthesis in Router' in route_s,'route_phase_checksums':re.findall(r'^Phase (\d+) [^\n|]+ \| Checksum: ([0-9a-f]+)$',route_s,re.M)}
 rows.append(row)
assert all(r['executed_route_commands']==['route_design'] for r in rows)
assert all(r['max_route_cpus']==['2'] for r in rows)
assert rows[0]['route_phase_names']==rows[1]['route_phase_names']==rows[2]['route_phase_names']
assert rows[0]['route_phase_checksums']==rows[2]['route_phase_checksums']
result={'arms':rows,'shared_route_command':True,'shared_routing_phase_names':True,'noedit_repeats_all_recorded_route_phase_checksums_match':True,'shared_input_sha256':json.loads((L/'panel_ledger.json').read_text())[0]['input_sha256'],'seeds':'not_explicitly_set; no_seed_snapshot_or_determinism_claim','cache_control':'fresh_processes_with_same_checkpoint_embedded_caches; OS_cache_and_inprocess_warmth_not_matched','ratio_definition':{'numerator_ns':0.769,'denominator_ns':0.792,'ratio':0.769/0.792,'meaning':'descriptive_ratio_for_this_state_and_observed_runs_only; not_causal_attribution_or_population_estimate'}}
(P/'ROUND2_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='arms'},indent=2))
