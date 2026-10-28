"""Self-authored 3-bit RTL-expression cones and exact synthetic gate lowering.
Not a Verilog parser, production synthesis flow, or physical-label generator.
"""
import hashlib,itertools,json
from pathlib import Path
BITS=3; MASK=7
OPS=['xor','and','or','add']

def evaluate(t,a,b):
    if isinstance(t,str):return a if t=='a' else b
    if isinstance(t,int):return t
    op,*xs=t;vs=[evaluate(x,a,b) for x in xs]
    if op=='not':return (~vs[0])&MASK
    if op=='rol':return ((vs[0]<<1)|(vs[0]>>2))&MASK
    x,y=vs
    return {'xor':lambda:x^y,'and':lambda:x&y,'or':lambda:x|y,'add':lambda:(x+y)&MASK}[op]()

def template(f,k):
    # Distinct expression skeletons define parent families; constants define cones.
    a,b='a','b';r=('rol',a);s=('rol',b)
    patterns=[('xor',('add',a,k),b),('add',('xor',a,k),b),('or',('add',a,b),k),('and',('xor',a,b),k),('xor',('and',a,k),s),('add',('or',a,k),s),('xor',('add',r,b),k),('or',('xor',r,k),b),('add',('and',a,b),k),('and',('add',r,k),b),('xor',('or',a,b),k),('add',('xor',a,b),('and',r,k))]
    return patterns[f]

def equivalent(t):
    if not isinstance(t,tuple):return t
    op,*xs=t;xs=[equivalent(x) for x in xs]
    if len(xs)==2:xs=xs[::-1] # all available binary ops are commutative
    return ('not',('not',(op,*xs)))

def text(t,summary=False):
    if isinstance(t,str):return ['input',t] if summary else [t]
    if isinstance(t,int):return ['constant',str(t)] if summary else [str(t)]
    op,*xs=t
    name={'xor':'exclusive_or','and':'bitwise_and','or':'bitwise_or','add':'modular_sum','not':'bitwise_inversion','rol':'rotate_left_one'}[op] if summary else op
    out=[name,'(']
    for x in xs:out+=text(x,summary)+[',']
    return out+[')']

def verilog(t):
    if isinstance(t,str):return t
    if isinstance(t,int):return "3'd"+str(t)
    op,*xs=t;v=[verilog(x) for x in xs]
    if op=='not':return '(~'+v[0]+')'
    if op=='rol':return '{'+v[0]+'[1:0],'+v[0]+'[2]}'
    return '('+v[0]+{'xor':' ^ ','and':' & ','or':' | ','add':' + '}[op]+v[1]+')'

class Gates:
    def __init__(self):self.nodes=[];self.edges=[]
    def node(self,kind,children=(),lane=-1):
        idx=len(self.nodes);self.nodes.append([kind,lane]);self.edges += [[c,idx] for c in children];return idx
    def lower(self,t):
        if isinstance(t,str):return [self.node('input_'+t,lane=i) for i in range(3)]
        if isinstance(t,int):return [self.node('const_'+str((t>>i)&1),lane=i) for i in range(3)]
        op,*xs=t;vs=[self.lower(x) for x in xs]
        if op=='rol':return [vs[0][2],vs[0][0],vs[0][1]]
        if op=='not':return [self.node('NOT',[v],i) for i,v in enumerate(vs[0])]
        x,y=vs
        if op!='add':return [self.node(op.upper(),[u,v],i) for i,(u,v) in enumerate(zip(x,y))]
        carry=self.node('const_0');out=[]
        for i,(u,v) in enumerate(zip(x,y)):
            xy=self.node('XOR',[u,v],i);out.append(self.node('XOR',[xy,carry],i))
            carry=self.node('OR',[self.node('AND',[u,v],i),self.node('AND',[xy,carry],i)],i)
        return out
    def eval(self,a,b,outputs):
        vals=[];parents={i:[] for i in range(len(self.nodes))}
        for x,y in self.edges:parents[y].append(x)
        for i,(kind,lane) in enumerate(self.nodes):
            vs=[vals[x] for x in parents[i]]
            if kind.startswith('input_'):v=((a if kind=='input_a' else b)>>lane)&1
            elif kind.startswith('const_'):v=int(kind[-1])
            elif kind=='NOT':v=1-vs[0]
            else:v={'XOR':lambda:vs[0]^vs[1],'AND':lambda:vs[0]&vs[1],'OR':lambda:vs[0]|vs[1]}[kind]()
            vals.append(v)
        return sum(vals[x]<<i for i,x in enumerate(outputs))

def rtl_graph(t):
    nodes=[];edges=[]
    def visit(x):
        children=[] if not isinstance(x,(tuple,list)) else [visit(y) for y in x[1:]]
        kind=str(x) if not isinstance(x,(tuple,list)) else x[0]
        i=len(nodes);nodes.append([kind,-1]);edges.extend([[j,i] for j in children]);return i
    output=visit(t);return {'nodes':nodes,'edges':edges,'outputs':[output]}

def check(records):
    ids=[r['sample_id'] for r in records];assert len(ids)==len(set(ids)),'duplicate sample IDs'
    train={r['family'] for r in records if r['split']=='train'};test={r['family'] for r in records if r['split']=='test'}
    assert not train&test,'family overlap'
    fingerprints={};semantic_checks=0
    for r in records:
        expected=f"family{r['family']:02d}_cone{r['constant']}";assert r['sample_id']==expected
        assert set(r['modality_ids'])=={'code','graph','summary','netlist'},'missing modality'
        assert set(r['modality_ids'].values())=={expected},'modality ID mismatch'
        assert r['code']==text(r['expression']) and r['equivalent_code']==text(r['equivalent_expression']),'code mismatch'
        assert r['summary']==text(r['expression'],True),'summary mismatch'
        assert r['graph']==rtl_graph(r['expression']) and r['equivalent_graph']==rtl_graph(r['equivalent_expression']),'RTL graph mismatch'
        assert r['split']==('train' if r['family']<8 else 'test'),'split reassignment'
        tt=[];g=Gates();g.nodes=r['netlist']['nodes'];g.edges=r['netlist']['edges']
        for a,b in itertools.product(range(8),repeat=2):
            truth=evaluate(r['expression'],a,b)
            assert truth==evaluate(r['equivalent_expression'],a,b)==g.eval(a,b,r['netlist']['outputs']),'semantic mismatch'
            tt.append(truth);semantic_checks+=1
        fp=hashlib.sha256(bytes(tt)).hexdigest();assert fp==r['semantic_sha256']
        assert fp not in fingerprints,'duplicate truth table';fingerprints[fp]=r['split']
        assert all(len(r[x]['nodes'])<=128 for x in ['graph','equivalent_graph','netlist'])
        assert max(len(r['code']),len(r['equivalent_code']),len(r['summary']))<=128
    return {'records':len(records),'train_records':sum(r['split']=='train' for r in records),'test_records':sum(r['split']=='test' for r in records),'train_families':sorted(train),'test_families':sorted(test),'exhaustive_input_assignments_checked':semantic_checks,'cross_split_semantic_duplicates':0,'modality_id_mismatches':0}

def build(dest):
    records=[];seen=set();duplicates=[]
    for f,k in itertools.product(range(12),range(1,8)):
        t=template(f,k);e=equivalent(t);tt=bytes(evaluate(t,a,b) for a,b in itertools.product(range(8),repeat=2));fp=hashlib.sha256(tt).hexdigest()
        if fp in seen:duplicates.append([f,k]);continue
        seen.add(fp);g=Gates();out=g.lower(t);sid=f'family{f:02d}_cone{k}'
        records.append({'sample_id':sid,'family':f,'constant':k,'split':'train' if f<8 else 'test','modality_ids':{m:sid for m in ['code','graph','summary','netlist']},'expression':t,'equivalent_expression':e,'code':text(t),'equivalent_code':text(e),'summary':text(t,True),'graph':rtl_graph(t),'equivalent_graph':rtl_graph(e),'netlist':{'nodes':g.nodes,'edges':g.edges,'outputs':out},'semantic_sha256':fp,'verilog':"module cone(input [2:0] a,b, output [2:0] y); assign y = "+verilog(t)+"; endmodule"})
    audit=check(records);audit['excluded_semantic_duplicates']=duplicates
    assert len(audit['train_families'])==8 and len(audit['test_families'])==4
    dest.mkdir(parents=True,exist_ok=True);(dest/'manifest.json').write_text(json.dumps(records,indent=2)+'\n');(dest/'integrity.json').write_text(json.dumps(audit,indent=2)+'\n')
    return records,audit
if __name__=='__main__':
    records,audit=build(Path(__file__).resolve().parents[1]/'results/data');print(json.dumps(audit,indent=2))
