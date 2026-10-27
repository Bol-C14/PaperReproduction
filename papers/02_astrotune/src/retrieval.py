"""Paper Eq1-7 structural signatures; TF-IDF is explicitly NOT an LLM."""
import hashlib, re, collections
import numpy as np
from pyverilog.vparser.parser import VerilogParser
from sklearn.feature_extraction.text import TfidfVectorizer

B=128; K=64; D=1024

def digest(token, seed=0):
    return int.from_bytes(hashlib.blake2b((str(seed)+':'+token).encode(),digest_size=16).digest(),'little')

def tokens(code, clock_ns=2.0):
    # No macros/includes in selected sources; parser directly avoids external preprocessor.
    code=re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)
    def split_assign(m):
        chunks=[]; depth=0; start=0; s=m[1]
        for i,ch in enumerate(s):
            if ch in '({[': depth+=1
            elif ch in ')}]': depth-=1
            elif ch==',' and depth==0: chunks.append(s[start:i]); start=i+1
        chunks.append(s[start:]); return ''.join('assign '+x+';' for x in chunks)
    # Pyverilog 1.3 rejects legal comma-separated continuous assignments.
    code=re.sub(r'\bassign\s+([^;]+);',split_assign,code)
    tree=VerilogParser(outputdir='/tmp',debug=False).parse(code)
    c=collections.Counter()
    def visit(n):
        kind=type(n).__name__; c['node:'+kind]+=1
        if kind in ('Input','Output','Inout'): c['port:'+kind]+=2
        if kind=='Width':
            # Numeric widths are preserved; symbolic spelling is discarded.
            s=re.sub(r'[A-Za-z_]\w*','SYM',str(n.msb)+':'+str(n.lsb)); c['width:'+s]+=1
        for child in n.children():
            c['edge:'+kind+'>'+type(child).__name__]+=1; visit(child)
    visit(tree); c['spec:clock_ns='+str(clock_ns)]+=1
    return c

def signature(c):
    vote=np.zeros(B); emb=np.zeros(D)
    for t,f in c.items():
        h=digest(t); vote+=f*np.array([1 if (h>>i)&1 else -1 for i in range(B)])
        emb[h%D]+=f*(1 if digest(t,1)&1 else -1)
    norm=np.linalg.norm(emb)
    if norm: emb/=norm
    return {'sim':sum(int(x>=0)<<i for i,x in enumerate(vote)),
            'min':[min(digest(t,i+2)&0xffffffff for t in c) for i in range(K)],'haste':emb}

def similarities(a,b):
    return [1-(a['sim']^b['sim']).bit_count()/B,
            sum(x==y for x,y in zip(a['min'],b['min']))/K,
            float(a['haste']@b['haste'])]

def retrieve(query, donors, mode='ast'):
    """Only donor RTL/spec/config enter; no target results accepted by this interface."""
    qa=signature(tokens(query['code'])); rows=[]
    vec=TfidfVectorizer(ngram_range=(1,2)).fit_transform([query['spec']]+[d['spec'] for d in donors])
    text=(vec[1:]@vec[0].T).toarray().ravel()
    qcount=tokens(query['code'])
    for i,d in enumerate(donors):
        dc=tokens(d['code']); scores=similarities(qa,signature(dc))
        keys=sorted(set(qcount)|set(dc)); x=np.array([qcount[k] for k in keys]); y=np.array([dc[k] for k in keys])
        numeric=1-float(np.linalg.norm(x-y)/(np.linalg.norm(x)+np.linalg.norm(y)))
        rows.append({'id':d['id'],'simhash':scores[0],'minhash':scores[1],'haste':scores[2], 'text':float(text[i]),'numeric':numeric})
    if mode=='fusion_control':
        # Paper has LLM preselection + semantic score. This is a deterministic control only.
        rows=sorted(rows,key=lambda r:(-r['text'],r['id']))[:2]
    for r in rows:
        r['score']=r['text'] if mode=='text' else r['numeric'] if mode=='numeric' else (r['simhash']+r['minhash']+r['haste']+(r['text'] if mode=='fusion_control' else 0))/(4 if mode=='fusion_control' else 3)
    return sorted(rows,key=lambda r:(-r['score'],r['id']))
