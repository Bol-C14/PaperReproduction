"""Controlled TRACE predictive closure. Execute from any cwd; PROTOCOL.md is authoritative."""
import ast
import copy
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import resource
import sys
import time
import traceback
from types import SimpleNamespace
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent
START = time.monotonic()
SEEDS = [2026, 2027, 2028]
TRAIN_FAMILIES = ['random_dag', 'chain', 'balanced']
TEST_FAMILIES = ['ripple_carry', 'comparator', 'priority_selector', 'reconvergent_mux']
ARITY = dict(INV=1, AND=2, OR=2, XOR=2, XNOR=2, MUX=3, MAJ=3)


def log(phase, **kwargs):
    row = dict(phase=phase, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               elapsed_s=time.monotonic()-START, **kwargs)
    with (ROOT/'RESULTS.jsonl').open('a') as f:
        f.write(json.dumps(row, allow_nan=False)+'\n')
    print(json.dumps(row), flush=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def deadline():
    if time.monotonic()-START > 1800:
        raise TimeoutError('Frozen 30-minute wall bound reached')


def load_official():
    source = (ROOT/'official_pm_source.py').read_text()
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in ['MLP', 'PlainMLP', 'TRACE']]
    ns = {'torch': torch, 'nn': nn, '__name__': 'official_pm_extracted'}
    exec(compile(ast.Module(body=classes, type_ignores=[]), 'official_pm_source.py', 'exec'), ns)
    trainer = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TRACETrainer')
    funcs = []
    for node in trainer.body:
        if isinstance(node, ast.FunctionDef) and node.name in ['_cop', '_cop_with_cov']:
            funcs.append(node)
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'official_pm_source.py', 'exec'), ns)
    return ns


def scalar(op, inputs):
    if op == 'INV': return 1-inputs[0]
    if op == 'AND': return inputs[0] & inputs[1]
    if op == 'OR': return inputs[0] | inputs[1]
    if op == 'XOR': return inputs[0] ^ inputs[1]
    if op == 'XNOR': return 1-(inputs[0] ^ inputs[1])
    if op == 'MUX': return inputs[2] if inputs[0] else inputs[1]
    if op == 'MAJ': return int(sum(inputs) >= 2)
    raise ValueError(op)


def truth_bits(nodes):
    # First label implementation: parallel Boolean algebra over 64-bit truth vectors.
    full = (1 << 64)-1
    values = []
    for i, node in enumerate(nodes):
        op, fanins = node['op'], node['inputs']
        if op == 'PI':
            value = sum(((j >> (5-i)) & 1) << j for j in range(64))
        else:
            a = [values[j] for j in fanins]
            if op == 'INV': value = full ^ a[0]
            elif op == 'AND': value = a[0] & a[1]
            elif op == 'OR': value = a[0] | a[1]
            elif op == 'XOR': value = a[0] ^ a[1]
            elif op == 'XNOR': value = full ^ (a[0] ^ a[1])
            elif op == 'MUX': value = ((full ^ a[0]) & a[1]) | (a[0] & a[2])
            elif op == 'MAJ': value = (a[0]&a[1]) | (a[0]&a[2]) | (a[1]&a[2])
            else: raise ValueError(op)
        values.append(value)
    return np.array([[(v >> j)&1 for v in values] for j in range(64)], dtype=np.float64)


def weights(probs):
    return np.array([np.prod([p if ((idx >> (5-j))&1) else 1-p for j,p in enumerate(probs)])
                     for idx in range(64)])


def exact_independent(nodes, probs):
    # Independent scalar recursion and rational arithmetic. Never calls truth_bits/scalar.
    means = [Fraction(0) for _ in nodes]
    pf = [Fraction(str(p)) for p in probs]
    for assignment in itertools.product([0, 1], repeat=6):
        memo = {}
        def evaluate(i):
            if i in memo: return memo[i]
            node = nodes[i]
            op = node['op']
            if op == 'PI': result = assignment[i]
            else:
                inputs = [evaluate(j) for j in node['inputs']]
                if op == 'INV': result = int(not inputs[0])
                elif op == 'AND': result = int(all(inputs))
                elif op == 'OR': result = int(any(inputs))
                elif op == 'XOR': result = int(inputs[0] != inputs[1])
                elif op == 'XNOR': result = int(inputs[0] == inputs[1])
                elif op == 'MUX': result = inputs[1] if inputs[0] == 0 else inputs[2]
                elif op == 'MAJ': result = int(inputs.count(1) > 1)
                else: raise ValueError(op)
            memo[i] = result
            return result
        w = Fraction(1)
        for p,b in zip(pf, assignment): w *= p if b else 1-p
        for i in range(len(nodes)): means[i] += w * evaluate(i)
    return np.array([float(v) for v in means])


def build_parent(family, index):
    rng = random.Random(70000 + (TRAIN_FAMILIES+TEST_FAMILIES).index(family)*100 + index)
    nodes = [dict(op='PI', inputs=[]) for _ in range(6)]
    def add(op, *fanins):
        nodes.append(dict(op=op, inputs=list(fanins)))
        return len(nodes)-1
    # Distinct masks per family; no renamed derivative crosses a parent split.
    mask = (index*7+3)%64
    x = [add('INV', i) if mask & (1 << i) else i for i in range(6)]
    if family == 'random_dag':
        pool = x[:]
        for _ in range(7 + index%4):
            op = rng.choice(list(ARITY))
            pool.append(add(op, *rng.choices(pool, k=ARITY[op])))
        add('MUX', x[index%6], pool[-1], pool[-2])
    elif family == 'chain':
        cur = x[0]
        for i in range(1, 7+index%4):
            op = rng.choice(['AND','OR','XOR','MUX'])
            cur = add(op, cur, x[i%6], *([x[(i+2)%6]] if op=='MUX' else []))
    elif family == 'balanced':
        low = [add(rng.choice(['AND','OR','XOR']), x[2*i], x[2*i+1]) for i in range(3)]
        mid = add(rng.choice(['AND','OR','XOR']),low[0],low[1])
        add('MUX',low[2],mid,x[index%6])
    elif family == 'ripple_carry':
        c0=add('MAJ',x[0],x[1],x[4]); s0=add('XOR',add('XOR',x[0],x[1]),x[4])
        c1=add('MAJ',x[2],x[3],c0); s1=add('XOR',add('XOR',x[2],x[3]),c0)
        add('MUX',x[5],c1,add('XOR',s0,s1))
    elif family == 'comparator':
        gt=add('AND',x[0],add('INV',x[3]))
        for a,b in [(x[1],x[4]),(x[2],x[5])]:
            gt=add('OR',add('AND',a,add('INV',b)),add('AND',add('XNOR',a,b),gt))
    elif family == 'priority_selector':
        zero=add('XOR',x[3],x[3]); tail=add('MUX',x[2],x[5],zero)
        mid=add('MUX',x[1],x[4],tail); add('MUX',x[0],x[3],mid)
    elif family == 'reconvergent_mux':
        s=add('XOR',x[0],x[1]); a=add('AND',x[1],x[2]); b=add('XOR',x[2],x[3])
        t=add('MUX',s,a,b); u=add('MUX',x[4],t,x[5])
        add('AND',u,add('OR',t,add('INV',x[0])))
    else: raise ValueError(family)
    return nodes


def make_data():
    rows, parents = [], []
    grid = [.1,.3,.5,.7,.9]
    max_disagreement = 0.
    for family in TRAIN_FAMILIES+TEST_FAMILIES:
        count = 16 if family in TRAIN_FAMILIES else 8
        for idx in range(count):
            nodes=build_parent(family,idx)
            parent=family+'_'+str(idx)
            split='train' if family in TRAIN_FAMILIES else ('support' if idx<2 else 'query')
            identity=hashlib.sha256(json.dumps(nodes,sort_keys=True).encode()).hexdigest()
            parents.append(dict(parent=parent,family=family,split=split,nodes=nodes,identity_sha256=identity))
            truth=truth_bits(nodes)
            rng=random.Random(81000+(TRAIN_FAMILIES+TEST_FAMILIES).index(family)*100+idx)
            draws=set()
            while len(draws)<8: draws.add(tuple(rng.choice(grid) for _ in range(6)))
            for assignment,p in enumerate(sorted(draws)):
                target=weights(p)@truth
                checked=exact_independent(nodes,p)
                max_disagreement=max(max_disagreement,float(np.abs(target-checked).max()))
                assert np.abs(target-checked).max()<1e-10
                rows.append(dict(id=parent+'_'+str(assignment),parent=parent,family=family,split=split,
                                 nodes=nodes,pi_probs=list(p),target=target.tolist()))
            deadline()
    hashes={s:{p['identity_sha256'] for p in parents if p['split']==s} for s in ['train','support','query']}
    assert hashes['train'].isdisjoint(hashes['support']|hashes['query'])
    assert hashes['support'].isdisjoint(hashes['query'])
    path=ROOT/'frozen_families.json'
    body=json.dumps(dict(protocol_sha256=sha(ROOT/'PROTOCOL.md'),parents=parents,rows=rows),sort_keys=True,indent=2)+'\n'
    if path.exists(): assert path.read_text()==body, 'Refusing to modify frozen data'
    else: path.write_text(body)
    log('data_and_independent_labels',status='pass',parents=len(parents),samples=len(rows),
        max_label_disagreement=max_disagreement,sha256=sha(path),counts={s:sum(r['split']==s for r in rows) for s in ['train','support','query']})
    return rows


def phi(op, p):
    if op=='INV': return 1-p[:,0]
    if op=='AND': return p[:,0]*p[:,1]
    if op=='OR': return p[:,0]+p[:,1]-p[:,0]*p[:,1]
    if op=='XOR': return p[:,0]+p[:,1]-2*p[:,0]*p[:,1]
    if op=='XNOR': return 1-p[:,0]-p[:,1]+2*p[:,0]*p[:,1]
    if op=='MUX': return (1-p[:,0])*p[:,1]+p[:,0]*p[:,2]
    if op=='MAJ': return p[:,0]*p[:,1]+p[:,0]*p[:,2]+p[:,1]*p[:,2]-2*p[:,0]*p[:,1]*p[:,2]
    raise ValueError(op)


def truth_feature(op):
    if op=='PI': return [0]*64
    # source _cop flips the feature vector: index 63-pattern encodes pattern output.
    return [scalar(op,[((63-index) >> j)&1 for j in reversed(range(ARITY[op]))]) for index in range(64)]


def batch(rows):
    xs=[];edges=[];ports=[];levels=[];targets=[];pi=[];ops=[];families=[];parents=[];outputs=[];slices=[]
    offset=0
    for row in rows:
        local_levels=[]
        for i,node in enumerate(row['nodes']):
            op=node['op'];fanins=node['inputs']
            xs.append(truth_feature(op));ops.append(op)
            local_levels.append(0 if op=='PI' else 1+max(local_levels[j] for j in fanins))
            for port,j in enumerate(fanins):edges.append([offset+j,offset+i]);ports.append(port)
            pi.append(row['pi_probs'][i] if op=='PI' else 0.)
            families.append(row['family']);parents.append(row['parent'])
        levels.extend(local_levels);targets.extend(row['target']);outputs.append(offset+len(local_levels)-1)
        slices.append([offset,offset+len(local_levels)]);offset+=len(local_levels)
    g=SimpleNamespace(x=torch.tensor(xs,dtype=torch.float32),edge_index=torch.tensor(edges,dtype=torch.long).t().contiguous(),
        edge_pos=torch.tensor(ports),forward_level=torch.tensor(levels),forward_index=torch.arange(offset),
        prob=torch.tensor(pi),target=torch.tensor(targets),outputs=torch.tensor(outputs),ops=ops,
        families=families,parents=parents,slices=slices,rows=rows)
    g.mask=g.forward_level>0
    g.plan=[]
    for level in range(1,max(levels)+1):
        for op in ARITY:
            indices=[i for i,(lev,name) in enumerate(zip(levels,ops)) if lev==level and name==op]
            if not indices:continue
            fanins=[]
            for i in indices:
                e=(g.edge_index[1]==i).nonzero().view(-1)
                e=e[torch.argsort(g.edge_pos[e])]
                fanins.append(g.edge_index[0,e].tolist())
            g.plan.append((level,op,torch.tensor(indices),torch.tensor(fanins)))
    g.local_teacher=torch.zeros_like(g.target)
    for _,op,idx,src in g.plan:g.local_teacher[idx]=phi(op,g.target[src])
    g.residual=g.target-g.local_teacher;g.residual[~g.mask]=0
    return g


def reconstruct(g,residual):
    p=g.prob.clone()
    for _,op,idx,src in g.plan:p[idx]=phi(op,p[src])+residual[idx]
    return p


def make_model(ns,seed):
    torch.manual_seed(seed)
    return ns['TRACE'](num_rounds=1,dim_hidden=128,num_heads=8,num_layers=2)


def raw_model(model,g):
    return model.readout_prob(model(g)).squeeze(-1)


def predict(model,g,arm):
    raw=raw_model(model,g)
    if arm=='direct':return torch.sigmoid(raw),raw
    raw=raw.clamp(-1,1)
    return reconstruct(g,raw),raw


def summary(g,p):
    err=(p-g.target).abs()
    return dict(node_mae=float(err[g.mask].mean()),output_mae=float(err[g.outputs].mean()),
        outside_unit=int(((p[g.mask]<0)|(p[g.mask]>1)).sum()),nodes=int(g.mask.sum()),
        min=float(p[g.mask].min()),max=float(p[g.mask].max()))


def evaluate(model,g,arm,tag):
    model.eval()
    with torch.no_grad():
        t=time.perf_counter();p,raw=predict(model,g,arm);inference=time.perf_counter()-t
        # Oracle teacher-predecessor diagnostic isolates one-step residual error.
        teacher=g.local_teacher+raw if arm=='fsl' else p
        stats=summary(g,p)
        stats['inference_s']=inference
        stats['teacher_node_mae']=float((teacher[g.mask]-g.target[g.mask]).abs().mean())
        stats['teacher_output_mae']=float((teacher[g.outputs]-g.target[g.outputs]).abs().mean())
        stats['recursive_teacher_gap_output']=float((p[g.outputs]-teacher[g.outputs]).abs().mean())
        stats['depth']={str(level):dict(n=int((g.forward_level==level).sum()),
             mae=float((p[g.forward_level==level]-g.target[g.forward_level==level]).abs().mean()),
             teacher_mae=float((teacher[g.forward_level==level]-g.target[g.forward_level==level]).abs().mean()))
             for level in sorted(set(g.forward_level.tolist())) if level>0}
        records=[]
        for row,(lo,hi) in zip(g.rows,g.slices):
            records.append(dict(id=row['id'],parent=row['parent'],family=row['family'],
                target=g.target[lo:hi].tolist(),prediction=p[lo:hi].tolist(),raw=raw[lo:hi].tolist(),
                teacher=teacher[lo:hi].tolist(),levels=g.forward_level[lo:hi].tolist()))
        (ROOT/'predictions'/f'{tag}.json').write_text(json.dumps(records)+'\n')
    return stats


def train(model,rows,arm,steps,lr,seed,tag,resource_pilot=False):
    torch.manual_seed(seed)
    model.train();optimizer=torch.optim.Adam(model.parameters(),lr=lr)
    rng=random.Random(seed);history=[];t=time.perf_counter()
    for step in range(steps):
        deadline()
        chosen=rows if len(rows)==16 else rng.sample(rows,16)
        g=batch(chosen)
        optimizer.zero_grad();raw=raw_model(model,g)
        pred=torch.sigmoid(raw) if arm=='direct' else raw.clamp(-1,1)
        target=g.target if arm=='direct' else g.residual
        loss=nn.functional.l1_loss(pred[g.mask],target[g.mask]);assert torch.isfinite(loss)
        loss.backward();optimizer.step()
        history.append(float(loss.detach()))
        with (ROOT/'training_steps.jsonl').open('a') as journal:
            journal.write(json.dumps(dict(tag=tag,step=step+1,loss=history[-1],elapsed_s=time.monotonic()-START))+'\n')
        if resource_pilot and step==19:
            used=time.perf_counter()-t;projected=used/20*(6*240+48*20)
            rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            log('resource_pilot',steps_retained=20,seconds=used,projected_compute_s=projected,peak_rss_kib=rss)
            assert projected<1800 and rss<4*1024*1024,'Resource gate exceeded'
    seconds=time.perf_counter()-t
    (ROOT/'losses'/f'{tag}.json').write_text(json.dumps(history)+'\n')
    return dict(seconds=seconds,steps=steps,first_loss=history[0],last_loss=history[-1],lr=lr)


def checks(ns,rows):
    g=batch(rows[:8]);oracle=reconstruct(g,g.residual)
    error=float((oracle-g.target).abs().max());assert error<1e-6
    proxy=SimpleNamespace();proxy._cop=lambda *a:ns['_cop'](proxy,*a)
    original_targets,original_residual,original_local=proxy._cop(g.edge_index,g.target,g.x)
    local_error=float((original_local-g.local_teacher[original_targets]).abs().max());assert local_error<1e-5
    original=ns['_cop_with_cov'](proxy,g,g.residual.unsqueeze(-1))
    original_error=float((original[g.outputs]-g.target[g.outputs]).abs().max())
    log('recurrence_checks',status='pass_port_original_failed' if original_error>1e-6 else 'pass',
        port_oracle_max_abs=error,source_local_max_abs=local_error,
        original_deepest_output_max_abs=original_error,
        original_deepest_output_values=original[g.outputs].tolist(),
        note='Original range(1,max_level) excludes deepest level; port includes it')


def model_controls(model,ns,g,arm,tag):
    model.eval()
    with torch.no_grad():
        p,raw=predict(model,g,arm)
        raw=raw_model(model,g)
        poisoned=copy.copy(g);poisoned.prob=g.prob.clone();poisoned.prob[g.mask]=.98765
        hidden_error=float((raw_model(model,poisoned)-raw).abs().max());assert hidden_error<=1e-6
        rng=torch.Generator().manual_seed(3901);new_to_old=torch.randperm(len(g.ops),generator=rng)
        old_to_new=torch.argsort(new_to_old);h=copy.copy(g)
        for key in ['x','prob','target','forward_level','residual','local_teacher']:
            setattr(h,key,getattr(g,key)[new_to_old])
        # Canonical order is (renamed target, semantic input port), never input node ID.
        e=old_to_new[g.edge_index];order=torch.argsort(e[1]*8+g.edge_pos)
        h.edge_index=e[:,order];h.edge_pos=g.edge_pos[order];h.forward_index=torch.arange(len(g.ops))
        renamed_raw=raw_model(model,h)[old_to_new]
        rename_error=float((raw-renamed_raw).abs().max());assert rename_error<1e-5
        # Edge order normalization is the explicit-port adapter's contract.
        reverse=torch.arange(g.edge_index.shape[1]-1,-1,-1);shuffled=copy.copy(g)
        e=g.edge_index[:,reverse];port=g.edge_pos[reverse];order=torch.argsort(e[1]*8+port)
        shuffled.edge_index=e[:,order]
        reorder_error=float((raw_model(model,shuffled)-raw).abs().max());assert reorder_error<1e-6
    return dict(hidden_label_poisoning_max_abs=hidden_error,rename_raw_max_abs=rename_error,
                edge_reorder_normalized_max_abs=reorder_error)


def role_rows():
    base=[dict(op='PI',inputs=[]) for _ in range(6)]
    result=[]
    for name,op,fanins in [('mux','MUX',[0,1,2]),('mux_roles_changed','MUX',[1,0,2]),
                            ('and','AND',[0,1]),('and_swapped','AND',[1,0])]:
        nodes=base+[dict(op=op,inputs=fanins)]
        probs=[.2,.8,.1,.3,.5,.7]
        result.append(dict(id=name,parent=name,family='role_control',split='control',nodes=nodes,
                           pi_probs=probs,target=(weights(probs)@truth_bits(nodes)).tolist()))
    return result


def role_check(model,arm):
    g=batch(role_rows());model.eval()
    with torch.no_grad():p,_=predict(model,g,arm)
    outputs=p[g.outputs].tolist();target=g.target[g.outputs].tolist()
    return dict(target=target,prediction=outputs,mux_target_delta=target[0]-target[1],
        mux_prediction_delta=outputs[0]-outputs[1],and_prediction_swap_abs=abs(outputs[2]-outputs[3]))


def alias_check(ns):
    # Isomorphic local computation but shared PI versus distinct equal-marginal PIs.
    inputs=[dict(op='PI',inputs=[]) for _ in range(6)]
    shared=inputs+[dict(op='AND',inputs=[0,1]),dict(op='AND',inputs=[0,2]),dict(op='AND',inputs=[6,7])]
    independent=inputs+[dict(op='AND',inputs=[0,1]),dict(op='AND',inputs=[2,3]),dict(op='AND',inputs=[6,7])]
    rows=[]
    for name,nodes in [('shared',shared),('independent',independent)]:
        rows.append(dict(id=name,parent=name,family='alias_control',nodes=nodes,pi_probs=[.5]*6,
                         target=(weights([.5]*6)@truth_bits(nodes)).tolist()))
    g=batch(rows);model=make_model(ns,9901).eval()
    with torch.no_grad():h=model(g);output=h[g.outputs]
    delta=float((output[0]-output[1]).abs().max())
    log('equal_marginal_alias_diagnostic',status='observed',embedding_max_abs=delta,
        different_exact_targets=g.target[g.outputs].tolist(),
        implication='Equal PI marginals without identity can erase reconvergence distinctions; no theorem beyond this example')


def main():
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    for d in ['predictions','losses','weights']: (ROOT/d).mkdir(exist_ok=True)
    log('start',python=sys.version,torch=torch.__version__,source_sha256=sha(ROOT/'official_pm_source.py'),
        protocol_sha256=sha(ROOT/'PROTOCOL.md'),cpu_threads=1,cuda_initialized=torch.cuda.is_initialized())
    ns=load_official();rows=make_data();checks(ns,rows);alias_check(ns)
    official=make_model(ns,0);checkpoint=torch.load(ROOT/'official_pm_probability.pth',map_location='cpu',weights_only=True)
    official.load_state_dict(checkpoint['state_dict'],strict=True)
    log('official_weights',status='strict_loaded',sha256=sha(ROOT/'official_pm_probability.pth'),
        epoch=checkpoint.get('epoch'),params=sum(p.numel() for p in official.parameters()),
        synthetic_truth_table_encoding='source _cop cross-check; original industrial preprocessing unverified')
    train_rows=[r for r in rows if r['split']=='train']
    results=[]
    # Diagnostic baseline costs have no learning steps.
    for family in TEST_FAMILIES:
        query=batch([r for r in rows if r['family']==family and r['split']=='query'])
        t=time.perf_counter();p=reconstruct(query,torch.zeros_like(query.prob));duration=time.perf_counter()-t
        score=summary(query,p);score['inference_s']=duration
        log('local_only',family=family,metrics=score)
    for seed in SEEDS:
        for arm in ['direct','fsl']:
            model=make_model(ns,seed)
            pre=train(model,train_rows,arm,240,.001,seed,f'{seed}_{arm}_pretrain',resource_pilot=seed==2026 and arm=='direct')
            torch.save(model.state_dict(),ROOT/'weights'/f'{seed}_{arm}_pretrain.pt')
            log('pretrain',seed=seed,arm=arm,**pre)
            for family in TEST_FAMILIES:
                support=[r for r in rows if r['family']==family and r['split']=='support']
                query=batch([r for r in rows if r['family']==family and r['split']=='query'])
                tag=f'{seed}_{arm}_{family}'
                before=evaluate(model,query,arm,tag+'_no_adapt')
                adapted=copy.deepcopy(model)
                adaptation=train(adapted,support,arm,20,.0001,seed+100,tag+'_adapt')
                after=evaluate(adapted,query,arm,tag+'_adapt')
                control=model_controls(adapted,ns,query,arm,tag)
                role=role_check(adapted,arm)
                torch.save(adapted.state_dict(),ROOT/'weights'/f'{tag}_adapt.pt')
                row=dict(track='scratch_pretrain',seed=seed,arm=arm,family=family,pretraining=pre,
                    no_adapt=before,adapt=after,adaptation=adaptation,controls=control,role_control=role)
                results.append(row);log('family_result',**row)
        # Independent transfer comparison uses source checkpoint versus random same-shape.
        for init in ['official','random']:
            model=copy.deepcopy(official) if init=='official' else make_model(ns,seed)
            for family in TEST_FAMILIES:
                support=[r for r in rows if r['family']==family and r['split']=='support']
                query=batch([r for r in rows if r['family']==family and r['split']=='query'])
                tag=f'{seed}_transfer_{init}_{family}'
                before=evaluate(model,query,'fsl',tag+'_no_adapt')
                adapted=copy.deepcopy(model)
                adaptation=train(adapted,support,'fsl',20,.0001,seed+100,tag+'_adapt')
                after=evaluate(adapted,query,'fsl',tag+'_adapt')
                control=model_controls(adapted,ns,query,'fsl',tag)
                row=dict(track='transfer_'+init,seed=seed,arm='fsl',family=family,
                    no_adapt=before,adapt=after,adaptation=adaptation,controls=control,
                    role_control=role_check(adapted,'fsl'))
                results.append(row);log('family_result',**row)
    (ROOT/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    log('complete',wall_s=time.monotonic()-START,cpu_s=time.process_time(),
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,cuda_initialized=torch.cuda.is_initialized(),
        result_rows=len(results),optimizer_steps=6*240+48*20)


if __name__=='__main__':
    try: main()
    except Exception as exc:
        log('failure',error=repr(exc),traceback=traceback.format_exc())
        raise
