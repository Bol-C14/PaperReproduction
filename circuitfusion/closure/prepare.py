"""Actual Verilog -> DFF boundary -> Yosys/ABC netlist; independent semantic checks."""
import collections,copy,hashlib,json,os,random,re,subprocess,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];TOOL=REPO/'circuitfusion/.venv/bin/yowasp-yosys';PROTOCOL=json.loads((ROOT/'PROTOCOL.json').read_text())

def yosys(script,name):
    (ROOT/(name+'.ys')).write_text(script);env=os.environ.copy();env['YOWASP_CACHE_DIR']=str(ROOT/'.yowasp-cache')
    with (ROOT/'logs'/f'{name}.log').open('w') as log:
        subprocess.run([str(TOOL),'-T','-s',str(ROOT/(name+'.ys'))],cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)

def expr(f,k):
    rng=random.Random(1314+f);ops=['xor','and','or','add','sub','mul'];o=[rng.choice(ops) for _ in range(4)];leaves=['q','a','b'];rng.shuffle(leaves);x,y,z=leaves
    shapes=[(o[0],(o[1],x,y),(o[2],z,k)),(o[0],(o[1],(o[2],x,k),y),z),(o[0],(o[1],x,(o[2],y,z)),k),(o[0],(o[1],x,k),(o[2],y,('not',z)))]
    return shapes[f%4]

def alternate(t):
    if not isinstance(t,(tuple,list)):return t
    op,*args=t;args=[alternate(x) for x in args]
    if op in ["xor","and","or","add","mul"]:args=args[::-1]
    return (op,*args)

def render(t,w=4):
    if isinstance(t,str):return t
    if isinstance(t,int):return f"{w}'d{t}"
    op,*args=t;v=[render(x,w) for x in args]
    if op=='not':return '(~'+v[0]+')'
    return '('+v[0]+{'xor':' ^ ','and':' & ','or':' | ','add':' + ','sub':' - ','mul':' * '}[op]+v[1]+')'

def reference(t,env,mask):
    if isinstance(t,str):return env[t]
    if isinstance(t,int):return np.full_like(env['q'],t)
    op,*args=t;v=[reference(x,env,mask) for x in args]
    if op=='not':return (~v[0])&mask
    a,b=v
    return {'xor':lambda:a^b,'and':lambda:a&b,'or':lambda:a|b,'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b}[op]()&mask

def assignments(w,external=False):
    names=['state'] if external else ['state','a','b'];ranges=[range(1<<w)]*len(names)+[range(2),range(2)];names+=['en','rst']
    grid=np.indices(tuple(map(len,ranges)),dtype=np.int64).reshape(len(names),-1)
    return dict(zip(names,grid))

def evaluate(module,env):
    size=len(next(iter(env.values())));bits={'0':np.zeros(size,dtype=np.int64),'1':np.ones(size,dtype=np.int64)};depth={'0':0,'1':0}
    for port,p in module['ports'].items():
        if p['direction']=='input':
            for lane,b in enumerate(p['bits']):bits[b]=(env[port]>>lane)&1;depth[b]=0
    def val(connection):return sum(bits[b]<<i for i,b in enumerate(connection))
    pending=dict(module['cells']);levels=[]
    while pending:
        progress=False
        for name,c in list(pending.items()):
            ins={k:v for k,v in c['connections'].items() if c['port_directions'][k]=='input'}
            if not all(b in bits for conn in ins.values() for b in conn):continue
            v={k:val(conn) for k,conn in ins.items()};typ=c['type'];a=v.get('A');b=v.get('B');s=v.get('S')
            funcs={'$add':lambda:a+b,'$sub':lambda:a-b,'$mul':lambda:a*b,'$xor':lambda:a^b,'$xnor':lambda:~(a^b),'$and':lambda:a&b,'$or':lambda:a|b,'$not':lambda:~a,'$mux':lambda:np.where(s,b,a),'$logic_not':lambda:(a==0).astype(np.int64),'$reduce_or':lambda:(a!=0).astype(np.int64),
            '$_AND_':lambda:a&b,'$_OR_':lambda:a|b,'$_XOR_':lambda:a^b,'$_XNOR_':lambda:~(a^b),'$_NOT_':lambda:~a,'$_MUX_':lambda:np.where(s,b,a),'$_NAND_':lambda:~(a&b),'$_NOR_':lambda:~(a|b),'$_ANDNOT_':lambda:a&~b,'$_ORNOT_':lambda:a|~b}
            if typ not in funcs:raise ValueError(('unsupported evaluator cell',typ))
            out=funcs[typ]();level=1+max((depth[b] for conn in ins.values() for b in conn),default=0)
            for port,conn in c['connections'].items():
                if c['port_directions'][port]=='output':
                    for i,bit in enumerate(conn):bits[bit]=(out>>i)&1;depth[bit]=level
            levels.append(level);del pending[name];progress=True
        assert progress,('cycle/unresolved',list(pending)[:3])
    outputs=module['ports']['next_state']['bits'];return val(outputs),max(depth[b] for b in outputs)

def graph(module):
    # Explicit bit-position nodes prevent equal-popcount constants from aliasing.
    nodes=[];edges=[];driver={};cellids={}
    for port,pr in sorted(module['ports'].items()):
        if pr['direction']=='input':
            for lane,bit in enumerate(pr['bits']):driver[bit]=len(nodes);nodes.append(['PI_'+port,lane,len(pr['bits'])])
    for bit in ['0','1']:driver[bit]=len(nodes);nodes.append(['CONST_'+bit,0,1])
    wordlevel=any(c['type'].startswith('$') and not c['type'].startswith('$_') for c in module['cells'].values())
    for name,c in sorted(module['cells'].items()):
        width=max((len(v) for k,v in c['connections'].items() if c['port_directions'][k]=='output'),default=1)
        cellids[name]=len(nodes);nodes.append([c['type'],0,width])
        for port,conn in c['connections'].items():
            if c['port_directions'][port]=='output':
                for lane,bit in enumerate(conn):
                    if wordlevel:
                        idx=len(nodes);nodes.append(['OUTPUT_BIT',lane,len(conn)]);edges.append([cellids[name],idx,0]);driver[bit]=idx
                    else:driver[bit]=cellids[name]
    for name,c in sorted(module['cells'].items()):
        for port,conn in c['connections'].items():
            if c['port_directions'][port]=='input':
                role=0 if port=='A' else 1 if port=='B' else 2
                for lane,bit in enumerate(conn):
                    if wordlevel:
                        idx=len(nodes);nodes.append(['PIN_'+port,lane,len(conn)]);edges.extend([[driver[bit],idx,role],[idx,cellids[name],role]])
                    else:edges.append([driver[bit],cellids[name],role])
    for lane,bit in enumerate(module['ports']['next_state']['bits']):
        idx=len(nodes);nodes.append(['OUTPUT',lane,1]);edges.append([driver[bit],idx,0])
    return {'nodes':nodes,'edges':edges}

def behavioral_summary(base,w):
    # Only I/O behavior: no expression, names, constants, IDs or implementation statistics.
    if base.ndim==1:base=base.reshape(1<<w,-1)
    bits=np.unpackbits(base.astype(np.uint8)[...,None],axis=-1)[...,-w:]
    activity=float(bits.mean());activity_word=['sparse','moderate','dense'][min(2,int(activity*3))]
    varying=bool(np.any(base!=base.flat[0]));state=bool(np.any(base[1:]!=base[:-1]))
    symmetry=base.ndim==3 and np.array_equal(base,base.swapaxes(1,2))
    return f"An unsigned state update has {'varying' if varying else 'constant'} outputs and {activity_word} bit activity. Prior state {'affects' if state else 'does not affect'} the result. Data operand exchange is {'symmetric' if symmetry else 'asymmetric'}. Reset clears state. Disabled updates hold state."

def main():
    start=time.monotonic();assert hashlib.sha256((ROOT/'PROTOCOL.json').read_bytes()).hexdigest()==(ROOT/'PROTOCOL.sha256').read_text().split()[0]
    out=ROOT/'data';out.mkdir(exist_ok=True);records=[];seen=set();excluded=[]
    for f in range(25):
        for k in (range(1,7) if f<24 else [0]):
            external=f==24;w=3 if external else 4;env=assignments(w,external);state=env['state'];e=None if external else expr(f,k)
            base=(state+1)&((1<<w)-1) if external else reference(e,{**env,'q':state},(1<<w)-1)
            truth=np.where(env['rst'],0,np.where(env['en'],base,state));fp=hashlib.sha256(truth.astype(np.uint8).tobytes()).hexdigest()
            if fp in seen:excluded.append([f,k]);continue
            seen.add(fp);sid=f'p{f:02d}_c{k}';d=out/sid;d.mkdir(exist_ok=True)
            code=(ROOT/'assets/counter.v').read_text() if external else f"module dut(input clk,rst,en,input [3:0] a,b,output reg [3:0] q);\nalways @(posedge clk) if(rst) q<=4'd0; else if(en) q<={render(e)};\nendmodule\n"
            (d/'parent.v').write_text(code)
            altcode=code if external else code.replace(render(e),render(('not',('not',alternate(e)))))
            (d/'parent_alt.v').write_text(altcode)
            r_alt=None if external else ('not',('not',alternate(e)))
            if r_alt is not None:assert np.array_equal(reference(r_alt,{**env,'q':state},(1<<w)-1),base)
            np.save(d/'reference.npy',truth.astype(np.uint8))
            base_shape=(1<<w,)*(1 if external else 3)+(2,2);base_values=base.reshape(base_shape)[...,0,0]
            summary=behavioral_summary(base_values,w)
            records.append({'sample_id':sid,'family':f,'constant':k,'split':'train' if f<16 else 'test','external':external,'bits':w,'expression':e,'summary':summary,'semantic_sha256':fp,'parent_sha256':hashlib.sha256(code.encode()).hexdigest(),'assignments':len(truth),'modality_ids':{x:sid for x in ['code','summary','graph','netlist']}})
    script=[]
    for r in records:
        d=out/r['sample_id'];top='counter' if r['external'] else 'dut'
        for suffix in ['', '_alt']:
            script += ['design -reset',f'read_verilog {d}/parent{suffix}.v',f'hierarchy -top {top}','proc','opt_clean',f'write_json {d}/sequential{suffix}.json']
    yosys('\n'.join(script)+'\n','extract_registers')
    for r in records:
        d=out/r['sample_id'];top='counter' if r['external'] else 'dut'
        for suffix in ['', '_alt']:
            obj=json.loads((d/f'sequential{suffix}.json').read_text());m=obj['modules'][top];ffs=[(n,c) for n,c in m['cells'].items() if c['type']=='$dff'];assert len(ffs)==1
            name,ff=ffs[0];q=ff['connections']['Q'];d_bits=ff['connections']['D'];del m['cells'][name]
            ports={n:pr for n,pr in m['ports'].items() if pr['direction']=='input' and n!='clk'};ports['state']={'direction':'input','bits':q};ports['next_state']={'direction':'output','bits':d_bits};m['ports']=ports;m['attributes']={'top':'1'}
            (d/f'cone{suffix}.json').write_text(json.dumps({'modules':{'gold':m}}))
    script=[]
    for r in records:
        d=out/r['sample_id'];script+=['design -reset',f'read_json {d}/cone.json','hierarchy -top gold','check -assert',f'write_verilog -noattr {d}/cone.v',f'write_json {d}/rtl.json','design -save rtl','design -reset',f'read_json {d}/cone_alt.json','hierarchy -top gold','opt',f'write_json {d}/equivalent.json','techmap','opt','abc -g AND,OR,XOR,XNOR,MUX','clean','rename gold gate',f'write_json {d}/gate.json',f'write_verilog -noattr {d}/gate.v','design -copy-from rtl gold','equiv_make gold gate equiv','hierarchy -top equiv','equiv_simple',f'tee -o {d}/formal_status.txt equiv_status -assert']
    yosys('\n'.join(script)+'\n','synthesize_and_prove')
    total=0;semantic_fp={};allcells=collections.Counter();maxnodes=0
    for r in records:
        d=out/r['sample_id'];env=assignments(r['bits'],r['external']);truth=np.load(d/'reference.npy');views={}
        for kind,file in [('graph','rtl.json'),('equivalent_graph','equivalent.json'),('netlist','gate.json')]:
            modules=json.loads((d/file).read_text())['modules'];m=next(iter(modules.values()));got,depth=evaluate(m,env)
            assert np.array_equal(got,truth),(r['sample_id'],kind,'reference mismatch');views[kind]=graph(m);maxnodes=max(maxnodes,len(views[kind]['nodes']));total+=len(truth);allcells.update(c['type'] for c in m['cells'].values())
            if kind=='netlist':r['targets']={'gate_count':len(m['cells']),'gate_depth':depth}
        assert max(len(v['nodes']) for v in views.values())<=PROTOCOL['data']['graph_node_limit'],(r['sample_id'],'node cap')
        r.update(views)
        # Features use anonymous HDL identifier roles and full expressions, never module names/paths/IDs.
        cone=(d/'parent.v').read_text();cone=re.sub(r'//[^\n]*','',cone);cone=re.sub(r'\b(?:dut|counter|count)\b',lambda m:'q' if m[0]=='count' else 'module_name',cone)
        r['code']=re.findall(r"\d+'[bdh][0-9a-fA-F]+|[A-Za-z_][A-Za-z_0-9]*|\d+|<=|==|!=|<<|>>|[^\s]",cone)
        assert len(r['code'])<=PROTOCOL['data']['code_token_limit']
        alt=(d/'parent_alt.v').read_text();alt=re.sub(r'//[^\n]*','',alt);alt=re.sub(r'\b(?:dut|counter|count)\b',lambda m:'q' if m[0]=='count' else 'module_name',alt)
        r['equivalent_code']=re.findall(r"\d+'[bdh][0-9a-fA-F]+|[A-Za-z_][A-Za-z_0-9]*|\d+|<=|==|!=|<<|>>|[^\s]",alt)
        assert len(r['equivalent_code'])<=PROTOCOL['data']['code_token_limit']
        r['summary_tokens']=re.findall(r'[a-z]+',r['summary'].lower())
        r['reference_sha256']=hashlib.sha256((d/'reference.npy').read_bytes()).hexdigest()
        semantic_fp.setdefault(r['semantic_sha256'],[]).append(r['split'])
    assert all(len(x)==1 for x in semantic_fp.values())
    summary_groups=collections.defaultdict(list)
    for r in records:summary_groups[r['summary']].append(r['sample_id'])
    # Tamper an observable gate output and ensure the independent evaluator rejects behavior.
    tampered=False
    for r in records:
        m=next(iter(json.loads((out/r['sample_id']/'gate.json').read_text())['modules'].values()));cp=copy.deepcopy(m);outs=cp['ports']['next_state']['bits'];cp['ports']['next_state']['bits']=['0']*len(outs)
        got,_=evaluate(cp,assignments(r['bits'],r['external']));tampered=not np.array_equal(got,np.load(out/r['sample_id']/'reference.npy'))
        if tampered:break
    assert tampered
    stats={'samples':len(records),'train_samples':sum(r['split']=='train' for r in records),'test_samples':sum(r['split']=='test' for r in records),'families':sorted({r['family'] for r in records}),'excluded_duplicate_candidates':excluded,'unique_summaries':len(summary_groups),'summary_group_sizes':sorted(map(len,summary_groups.values())),'all_input_comparisons_across_three_views':total,'formal_proofs':len(records),'max_graph_nodes':maxnodes,'tampered_output_rejected':tampered,'cell_types':dict(allcells),'wall_seconds':time.monotonic()-start,'summary_is_LLM':False,'external_asset':'Yosys examples/cmos/counter.v; family24 test only','equivalent_code_note':'commutative operand swaps and double inversion in actual alternate sequential Verilog; independently checked reference and formal RTL-to-alternate-gate equality'}
    (ROOT/'manifest.json').write_text(json.dumps(records,indent=2)+'\n');(ROOT/'integrity.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats,indent=2))
if __name__=='__main__':main()
