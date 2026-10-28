#!/usr/bin/env python3
"""CPU-only non-LLM retrieval/search baseline, with real Yosys/ABC measurements."""
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
YOSYS = ROOT / 'native/root/usr/bin/yosys'
ABC = ROOT / 'native/root/usr/bin/yosys-abc'


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def design_definitions():
    # Every input is unsigned, and every output width and truncation is explicit.
    # Separate independently written Python arithmetic is used for verification.
    return [
        ('sumtree', 'prior', 32, 10,
         "wire [9:0] a={2'b0,x[7:0]}, b={2'b0,x[15:8]}, c={2'b0,x[23:16]}, d={2'b0,x[31:24]}; assign y=a+b+c+d;"),
        ('multiply', 'prior', 16, 16, 'assign y=x[7:0]*x[15:8];'),
        ('alu', 'prior', 18, 8,
         "wire [7:0] a=x[7:0], b=x[15:8]; assign y=x[17:16]==0 ? a+b : x[17:16]==1 ? a-b : x[17:16]==2 ? a&b : a^b;"),
        ('barrel', 'prior', 21, 16, 'assign y=x[20] ? (x[15:0] >> x[19:16]) : (x[15:0] << x[19:16]);'),
        ('minmax', 'prior', 32, 16,
         'wire [7:0] a=x[7:0],b=x[15:8],c=x[23:16],d=x[31:24]; wire [7:0] lo=a<b?a:b,hi=c>d?c:d; assign y={hi,lo};'),
        ('popcount', 'prior', 32, 6,
         'integer i; reg [5:0] n; always @* begin n=0; for(i=0;i<32;i=i+1) n=n+x[i]; end assign y=n;'),
        ('fir3', 'target', 36, 14,
         "wire [11:0] p0=x[5:0]*x[23:18],p1=x[11:6]*x[29:24],p2=x[17:12]*x[35:30]; assign y={2'b0,p0}+{2'b0,p1}+{2'b0,p2};"),
        ('crc8', 'target', 24, 8,
         "integer i; reg [7:0] c; always @* begin c=x[7:0]; for(i=23;i>=8;i=i-1) begin if(c[7]^x[i]) c=(c<<1)^8'h07; else c=c<<1; end end assign y=c;"),
        ('priority', 'target', 32, 6,
         'integer i; reg [4:0] index; always @* begin index=0; for(i=0;i<32;i=i+1) if(x[i]) index=i; end assign y={|x,index};'),
        ('manhattan', 'target', 32, 10,
         "wire [7:0] a=x[7:0],b=x[15:8],c=x[23:16],d=x[31:24]; wire [7:0] dx=a>b?a-b:b-a,dy=c>d?c-d:d-c; assign y={2'b0,dx}+{2'b0,dy};"),
    ]


def reference(name, x):
    b = [(x >> (8*i)) & 255 for i in range(4)]
    if name == 'sumtree': return sum(b)
    if name == 'multiply': return b[0]*b[1]
    if name == 'alu':
        op = (x >> 16) & 3
        return [b[0]+b[1], b[0]-b[1], b[0]&b[1], b[0]^b[1]][op] & 255
    if name == 'barrel':
        word, shift = x & 65535, (x >> 16) & 15
        return (word >> shift if (x >> 20) & 1 else word << shift) & 65535
    if name == 'minmax': return (max(b[2], b[3]) << 8) | min(b[0], b[1])
    if name == 'popcount': return x.bit_count()
    if name == 'fir3':
        a = [(x >> (6*i)) & 63 for i in range(6)]
        return sum(a[i]*a[i+3] for i in range(3))
    if name == 'crc8':
        c = x & 255
        for i in range(23, 7, -1):
            feedback = ((c >> 7) ^ (x >> i)) & 1
            c = ((c << 1) & 255) ^ (7 if feedback else 0)
        return c
    if name == 'priority': return (32 | (x.bit_length()-1)) if x else 0
    if name == 'manhattan': return abs(b[0]-b[1])+abs(b[2]-b[3])
    raise ValueError(name)


def freeze():
    if (ROOT/'manifest.json').exists():
        raise SystemExit('Already frozen; do not replace the manifest.')
    designs = []
    for name, role, ib, ob, body in design_definitions():
        path = ROOT/'circuits'/f'{name}.v'
        path.parent.mkdir(exist_ok=True)
        path.write_text('// Independently authored educational workload, not a paper benchmark.\n'
                        f'module dut(input [{ib-1}:0] x, output [{ob-1}:0] y);\n{body}\nendmodule\n')
        designs.append(dict(id=name, family=name, role=role, input_bits=ib, output_bits=ob,
                            rtl=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    scripts = {'area':'strash; dch; if -K 4 -a; mfs2',
               'depth':'strash; balance; if -K 4 -F 0 -A 0'}
    for mode, text in scripts.items():
        path=ROOT/'abc_scripts'/f'{mode}.abc';path.parent.mkdir(exist_ok=True);path.write_text(text+'\n')
    configs=[]
    for noalumacc in [False,True]:
        for mode in ['fast','quality','area','depth']:
            configs.append(dict(id=f'c{len(configs)}',noalumacc=noalumacc,mode=mode))
    dump(ROOT/'manifest.json',dict(designs=designs,configs=configs,seeds=[11,23,37],
        arms=['structural','random_retrieval','no_retrieval','random_search'],
        online_budget_per_arm_target_seed=4,top_k_guidance=3,baseline_config='c0',
        score='LUT4 count * maximum unit LUT depth; lower is better',
        source_evaluations=48,online_evaluations=192,posthoc_oracle_evaluations=32,
        max_measurement_calls=272,max_seconds_per_synthesis=60,max_seconds_per_cec=30,
        correctness_vectors=256,correctness_seed=701,
        proposal='New categorical kernel LCB policy; NOT an LLM or the CROP proposal implementation',
        semantic_component='NOT RUN', archive_policy='Fixed prior retrieval DB; isolated per-query target histories',
        split='Six primitive-operation prior families; four distinct held-out application families; shared operators permitted, no width-scaled target copies',
        fixture_origin='All ten circuits independently authored; neither EPFL nor RTLRewriter was imported',
        frozen_before='First expanded-study synthesis measurement'))


def command(argv, logfile, timeout):
    started=time.monotonic()
    with logfile.open('w') as out:
        try:
            cp=subprocess.Popen([str(s) for s in argv],cwd=ROOT,stdout=out,
                                stderr=subprocess.STDOUT,start_new_session=True)
            return cp.wait(timeout=timeout),time.monotonic()-started
        except subprocess.TimeoutExpired:
            # Yosys may have launched ABC. Kill the owned process group so a
            # timed-out synthesis does not leave an unaccounted CPU worker.
            try:
                os.killpg(cp.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            cp.wait()
            out.write('\nOwned tool process group terminated after timeout.\n')
            return 124,time.monotonic()-started
        except OSError as exc:
            out.write('Tool launch failed: '+str(exc)+'\n')
            return 127,time.monotonic()-started


def structural_features(module):
    counts=[0.0]*8
    for cell in module.get('cells',{}).values():
        t=cell['type']
        i=(0 if t in ('$add','$sub','$neg') else 1 if t=='$mul' else 2 if t in ('$lt','$gt','$le','$ge','$eq','$ne')
           else 3 if t in ('$mux','$pmux') else 4 if t in ('$shl','$shr','$sshl','$sshr','$shift','$shiftx')
           else 5 if t.startswith('$reduce') else 6)
        outputs=sum(len(bits) for port,bits in cell['connections'].items() if cell['port_directions'][port]=='output')
        counts[i]+=outputs
    counts[7]=sum(len(p['bits']) for p in module['ports'].values())/8
    vec=[math.log1p(c) for c in counts]
    norm=math.sqrt(sum(v*v for v in vec))
    return dict(raw_output_bit_counts=counts, vector=[v/norm for v in vec],
                dimensions=['add_sub','multiply','compare','mux','shift','reduce','other','io_scaled'])


def verify_luts(path, design, vectors=256):
    mod=json.loads(path.read_text())['modules']['dut']
    rng=random.Random(701+design['input_bits'])
    width=design['input_bits'];limit=(1<<width)-1
    xs=[0,limit,1,1<<(width-1),limit//3,2*(limit//3)]
    xs += [1<<i for i in range(width)]
    xs += [rng.getrandbits(width) for _ in range(vectors-len(xs))]
    mask=(1<<len(xs))-1
    values={'0':0,'1':mask};depth={'0':0,'1':0}
    for i,bit in enumerate(mod['ports']['x']['bits']):
        values[bit]=sum(((x>>i)&1)<<j for j,x in enumerate(xs));depth[bit]=0
    pending=dict(mod['cells'])
    while pending:
        progress=False
        for name,cell in list(pending.items()):
            if cell['type']!='$lut': raise ValueError('Non-LUT cell '+cell['type'])
            bits=cell['connections']['A']
            if not all(b in values for b in bits): continue
            table=int(cell['parameters']['LUT'],2);out=0
            for pattern in range(1<<len(bits)):
                if not (table>>pattern)&1: continue
                term=mask
                for i,b in enumerate(bits): term &= values[b] if (pattern>>i)&1 else mask^values[b]
                out |= term
            output=cell['connections']['Y'][0]
            values[output]=out;depth[output]=1+max([depth[b] for b in bits] or [0])
            del pending[name];progress=True
        if not progress: raise ValueError('Cycle/unresolved signal')
    outputs=mod['ports']['y']['bits']
    for j,x in enumerate(xs):
        got=sum(((values[b]>>j)&1)<<i for i,b in enumerate(outputs))
        expected=reference(design['id'],x)
        if got!=expected: raise ValueError(f'Independent mismatch x={x} got={got} expected={expected}')
    return dict(lut_count=len(mod['cells']),lut_depth=max(depth[b] for b in outputs),
                vectors_checked=len(xs),vectors_sha256=digest(xs))


def score(row): return row['lut_count']*row['lut_depth']


def config_distance(a,b):
    return int(a['mode']!=b['mode'])+int(a['noalumacc']!=b['noalumacc'])


def propose(context):
    """Executable non-model policy; the JSON context is also the model interface."""
    configs=context['legal_configs']; byid={c['id']:c for c in configs}
    observed=context['target_history']; tried={r['config'] for r in observed}
    rng=random.Random(context['seed']+context['iteration']*1009)
    candidates=[c for c in configs if c['id'] not in tried];rng.shuffle(candidates)
    if not observed: return dict(config='c0',reason='common initialization',candidate_scores=[])
    if context['arm']=='random_search':
        return dict(config=candidates[0]['id'],reason='uniform untried configuration',candidate_scores=[])
    observations=[]
    baseline=observed[0]['objective']
    for r in observed:
        if r['status']=='ok': observations.append((byid[r['config']],r['objective']/baseline,1.0))
    for r in context['retrieved_guidance']:
        observations.append((byid[r['config']],r['normalized_objective'],0.5))
    ranked=[]
    for c in candidates:
        weights=[w*math.exp(-1.2*config_distance(c,old)) for old,val,w in observations]
        mean=sum(w*val for w,(_,val,_) in zip(weights,observations))/sum(weights)
        uncertainty=0.12/math.sqrt(sum(weights))
        ranked.append(dict(config=c['id'],predicted_mean=mean,exploration=uncertainty,lcb=mean-uncertainty))
    ranked.sort(key=lambda r:r['lcb'])
    return dict(config=ranked[0]['config'],reason='categorical kernel LCB using current target history and optional fixed prior guidance',candidate_scores=ranked)


class Study:
    def __init__(self):
        self.manifest=json.loads((ROOT/'manifest.json').read_text())
        self.rows=[];self.total_started=time.monotonic()
        self.features={};self.designs={d['id']:d for d in self.manifest['designs']}

    def measure(self,design,config,phase,**labels):
        m=self.manifest
        assert len(self.rows)<m['max_measurement_calls']
        name=f'{len(self.rows)+1:03d}_{phase}_{design["id"]}_{config["id"]}'
        folder=ROOT/'runs'/name;folder.mkdir(parents=True)
        rel=folder.relative_to(ROOT)
        abcargs=('-fast -lut 4' if config['mode']=='fast' else '-lut 4' if config['mode']=='quality'
                 else f'-lut 4 -script abc_scripts/{config["mode"]}.abc')
        opts='-noalumacc' if config['noalumacc'] else ''
        script=(f'read_verilog {design["rtl"]}\nhierarchy -check -top dut\nproc\nflatten\nopt\n'
                f'write_json {rel}/highlevel.json\nsynth -top dut -noabc {opts}\ncheck -assert\n'
                f'write_blif {rel}/reference.blif\nabc -exe {ABC} {abcargs}\nclean\ncheck -assert\n'
                f'write_json {rel}/mapped.json\nwrite_blif {rel}/mapped.blif\nstat\nltp -noff\n')
        (folder/'flow.ys').write_text(script)
        row=dict(invocation=len(self.rows)+1,phase=phase,design=design['id'],config=config['id'],status='started',folder=str(rel),**labels)
        self.rows.append(row)
        with (ROOT/'ledger.jsonl').open('a') as out: out.write(json.dumps(row)+'\n')
        started=time.monotonic()
        argv=[str(YOSYS),'-Q','-T','-s',str(rel/'flow.ys')]
        row['commands']=[argv];row['synthesis_returncode'],row['synthesis_seconds']=command(argv,folder/'yosys.log',m['max_seconds_per_synthesis'])
        try:
            if row['synthesis_returncode']!=0: raise ValueError('Yosys failed or timed out')
            if not (folder/'mapped.json').exists(): raise ValueError('Tool returned without producing mapped netlist')
            argv=[str(ABC),'-c',f'cec {rel}/reference.blif {rel}/mapped.blif']
            row['commands'].append(argv)
            row['cec_returncode'],row['cec_seconds']=command(argv,folder/'cec.log',m['max_seconds_per_cec'])
            if row['cec_returncode']!=0 or 'Networks are equivalent' not in (folder/'cec.log').read_text():
                raise ValueError('ABC combinational equivalence not established')
            row.update(verify_luts(folder/'mapped.json',design))
            yosyslog=(folder/'yosys.log').read_text()
            depth=int(re.findall(r'Longest topological path.*\(length=(\d+)\)',yosyslog)[-1])
            if depth!=row['lut_depth']: raise ValueError('Independent depth versus Yosys ltp mismatch')
            self.features[design['id']]=structural_features(json.loads((folder/'highlevel.json').read_text())['modules']['dut'])
            row.update(status='ok',objective=score(row),formal='ABC CEC: equivalent',independent='Python arithmetic versus LUT truth tables: pass')
        except Exception as exc:
            row.update(status='failed',error=str(exc),objective=None)
        row['elapsed_seconds']=time.monotonic()-started
        dump(folder/'result.json',row)
        with (ROOT/'ledger.jsonl').open('a') as out: out.write(json.dumps(dict(row,event='finished'))+'\n')
        dump(ROOT/'results.json',self.rows)
        print(name,row['status'],row.get('objective'),flush=True)
        return row

    def run(self):
        if (ROOT/'ledger.jsonl').exists(): raise SystemExit('Ledger exists; refusing to overwrite completed or partial study.')
        m=self.manifest;configs=m['configs'];byconfig={c['id']:c for c in configs}
        priors=[d for d in m['designs'] if d['role']=='prior'];targets=[d for d in m['designs'] if d['role']=='target']
        for design in m['designs']:
            assert hashlib.sha256((ROOT/design['rtl']).read_bytes()).hexdigest()==design['sha256']
        for design in priors:
            for config in configs: self.measure(design,config,'history')
            # First eight calls constitute the pilot. Stop on any correctness/tool issue.
            if any(r['status']!='ok' for r in self.rows): raise SystemExit('Pilot/history failure; preserved logs; stop scaling.')
        history={d['id']:sorted([r for r in self.rows if r['design']==d['id']],key=lambda r:(r['objective'],r['config'])) for d in priors}
        dump(ROOT/'history.json',history)
        history_hash=digest(history)
        # Freeze features for targets before search, with no objective or label exposed.
        for design in targets:
            folder=ROOT/'features'/design['id'];folder.mkdir(parents=True)
            script=f'read_verilog {design["rtl"]}; hierarchy -check -top dut; proc; flatten; opt; write_json features/{design["id"]}/highlevel.json'
            argv=[str(YOSYS),'-Q','-T','-p',script]
            rc,elapsed=command(argv,folder/'extract.log',60)
            if rc: raise SystemExit('Feature extraction failed; see preserved log')
            self.features[design['id']]=structural_features(json.loads((folder/'highlevel.json').read_text())['modules']['dut'])
            dump(folder/'extraction.json',dict(command=argv,seconds=elapsed,status='ok'))
        dump(ROOT/'features.json',self.features)
        for design in targets:
            vec=self.features[design['id']]['vector']
            similarities=[(sum(a*b for a,b in zip(vec,self.features[d['id']]['vector'])),d['id']) for d in priors]
            nearest=sorted(similarities,key=lambda x:(-x[0],x[1]))[0][1]
            for seed in m['seeds']:
                selected_random=random.Random(seed).choice(priors)['id']
                for arm in m['arms']:
                    selected=nearest if arm=='structural' else selected_random if arm=='random_retrieval' else None
                    guidance=[]
                    if selected:
                        baseline=next(r['objective'] for r in history[selected] if r['config']=='c0')
                        guidance=[dict(config=r['config'],objective=r['objective'],normalized_objective=r['objective']/baseline)
                                  for r in history[selected][:m['top_k_guidance']]]
                    archive=[]
                    archivepath=ROOT/'archives'/f'{design["id"]}_{seed}_{arm}.json'
                    for iteration in range(m['online_budget_per_arm_target_seed']):
                        context=dict(arm=arm,seed=seed,iteration=iteration,legal_configs=configs,
                                     retrieved_prior=selected,retrieved_guidance=guidance,target_history=archive,
                                     objective=m['score'],similarities=similarities,prior_db_hash=history_hash,
                                     target_history_hash=digest(archive),semantic_component='NOT RUN')
                        response=propose(context)
                        assert response['config'] in byconfig
                        assert response['config'] not in {r['config'] for r in archive}
                        path=ROOT/'contexts'/f'{design["id"]}_{seed}_{arm}_{iteration}.json'
                        dump(path,dict(request=context,response=response,proposal_origin='new non-LLM baseline'))
                        row=self.measure(design,byconfig[response['config']],'online',arm=arm,seed=seed,iteration=iteration,retrieved=selected,context=str(path.relative_to(ROOT)))
                        if row['status']!='ok': raise SystemExit('Online measurement failure; preserve and stop.')
                        archive=archive+[dict(config=row['config'],objective=row['objective'],status=row['status'],invocation=row['invocation'])]
                        dump(archivepath,dict(prior_db_hash=history_hash,target_history=archive,target_history_hash=digest(archive)))
        # Exhaustive eight-configuration reference is measured only after ALL online
        # proposals are complete; it is never an input to either search or retrieval.
        for design in targets:
            for config in configs: self.measure(design,config,'posthoc_oracle')
        assert digest(history)==history_hash
        dump(ROOT/'summary.json',dict(measurement_calls=len(self.rows),successful=sum(r['status']=='ok' for r in self.rows),
              seconds=time.monotonic()-self.total_started,semantic_component='NOT RUN',prior_db_hash=history_hash))
        fields=['invocation','phase','design','config','arm','seed','iteration','retrieved','lut_count','lut_depth','objective','status','elapsed_seconds','folder']
        with (ROOT/'measurements.csv').open('w') as out:
            writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(self.rows)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='freeze': freeze()
    else: Study().run()
