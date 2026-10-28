"""Inspect immutable image history and patch applicability, without exposing patches."""
import argparse,json,pathlib,subprocess,re,os
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--datasets',type=pathlib.Path,required=True);p.add_argument('--selection',type=pathlib.Path,required=True);p.add_argument('--images',type=pathlib.Path,required=True);a=p.parse_args()
records={f"{r['org']}/{r['repo']}:pr-{r['number']}":r for f in a.datasets.glob('*.jsonl') if not f.name.startswith('._') for r in map(json.loads,f.read_text().splitlines())}
images={r['id']:r for r in json.loads(a.images.read_text())};out=a.root.parent/'history';out.mkdir(exist_ok=True)
pod=['podman','--root',str(a.root/'containers'),'--runroot',str(a.root/'runroot'),'--storage-driver','overlay'];cpus=','.join(map(str,sorted(os.sched_getaffinity(0))[:4]));rows=[]
for t in json.loads(a.selection.read_text())['tasks']:
 r=records[t['id']];commits=[r.get('merge_commit_sha','')]+[c.get('sha','') for c in r.get('commits',[]) if isinstance(c,dict)];commits=sorted(set(c for c in commits if re.fullmatch('[a-f0-9]{40}',c)))
 key=t['repo']+'-'+str(t['number']);fix=a.root/key/'private-runtime/fix.patch';image=t['image'].split(':')[0]+'@'+images[t['id']]['platform_digest']
 script='cd /home/'+t['repo']+'; printf "APPLY_CHECK\\n"; git apply --check /audit/ref.patch; echo "APPLY_RC=$?"; printf "CANDIDATE_FIX_OBJECTS\\n"; '
 for c in commits:script+='git cat-file -e '+c+'^{commit} 2>/dev/null; echo "'+c+' PRESENT_RC=$?"; '
 script+='printf "TOOLCHAIN\\n"; uname -m; gcc --version | head -1; if test -x /home/cva6/.hwe_tools/verilator/bin/verilator; then /home/cva6/.hwe_tools/verilator/bin/verilator --version; fi; printf "IMAGE_LICENSE_PATHS\\n"; find /home/'+t['repo']+' -maxdepth 1 -iname "*licen*" -print'
 cmd=['taskset','-c',cpus]+pod+['run','--rm','--network','none','--http-proxy=false','-v',str(fix)+':/audit/ref.patch:ro',image,'bash','-lc',script]
 try:
  proc=subprocess.run(cmd,text=True,capture_output=True,timeout=60);log=proc.stdout+proc.stderr;(out/(key+'.log')).write_text(log);row={'id':t['id'],'returncode':proc.returncode,'patch_applies':'APPLY_RC=0' in log,'candidate_fix_commits':len(commits),'present_candidate_fix_commits':len(re.findall(r'PRESENT_RC=0',log)),'command':cmd}
 except Exception as e:row={'id':t['id'],'error':str(e)}
 rows.append(row);(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(row),flush=True)
