"""Independent scalar BLIF replay, importing neither model nor solver/parser."""
import hashlib,itertools,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def load(path):
    lines=[s.split('#')[0].strip() for s in path.read_text().replace('\\\n',' ').splitlines()];lines=[s for s in lines if s]
    inputs=[];outputs=[];gates={};i=0
    while i<len(lines):
        w=lines[i].split();i+=1
        if w[0]=='.inputs':inputs=w[1:]
        elif w[0]=='.outputs':outputs=w[1:]
        elif w[0]=='.names':
            cubes=[]
            while i<len(lines) and not lines[i].startswith('.'):
                cubes.append(lines[i].split());i+=1
            gates[w[-1]]=(w[1:-1],cubes)
        elif w[0] not in ['.model','.end']:raise ValueError(w[0])
    return inputs,outputs,gates
def evaluate(net,bits):
    inputs,outputs,gates=net;cache=dict(zip(inputs,bits))
    def get(n):
        if n in cache:return cache[n]
        pins,cubes=gates[n];values=[get(p) for p in pins];v=int(bool(cubes) and all(c[-1]=='0' for c in cubes))
        for c in cubes:
            pattern=c[0] if pins else ''
            if all(a=='-' or int(a)==b for a,b in zip(pattern,values)):v=int(c[-1])
        cache[n]=v;return v
    return tuple(get(n) for n in outputs)
def main():
    raw=ROOT/'assets/int2float.blif';original=load(raw);patterns=list(itertools.product([0,1],repeat=11));truth=[evaluate(original,x) for x in patterns]
    report=json.loads((ROOT/'results/results.json').read_text());rows=[]
    for rec in report['records']:
        if not rec['success']:continue
        p=ROOT/rec['patch_blif'];net=load(p);assert net[:2]==original[:2]
        assert all(evaluate(net,x)==gold for x,gold in zip(patterns,truth))
        rows.append(dict(path=rec['patch_blif'],sha256=hashlib.sha256(p.read_bytes()).hexdigest(),assignments_checked=2048,passed=True))
    negative=load(ROOT/'results/negative.blif');bad=next((x for x,gold in zip(patterns,truth) if evaluate(negative,x)!=gold),None);assert bad is not None
    output=dict(status='passed',original_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),patches_checked=len(rows),assignments_checked=len(rows)*2048,records=rows,negative_counterexample=list(bad))
    assert len(rows)==6
    (ROOT/'results/independent_verification.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
