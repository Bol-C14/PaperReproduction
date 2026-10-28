"""New paper-inspired datapath workloads, explicit finite bit widths."""
from engine import width


def workload(name,w):
    a,b,c,y=(('V',n,w) for n in ('a','b','c','y'))
    k=lambda n:('K',w,n)
    add=lambda x,z:('Add',w,x,z)
    mul=lambda x,z:('Mul',w,x,z)
    if name=='guarded_shift':return ('Mux',w,('Ult',y,2),add(('Shr',w,a,y),c),b)
    if name=='bounded_fma':return ('Mux',w,('Ult',a,8),add(mul(a,b),c),c)
    if name=='signed_abs':return ('Mux',w,('Sge0',a),add(('Abs',w,a),b),c)
    if name=='interpolation_clamp':
        # Four-bit samples: conservative bound sum <= 15*3+15*5=120.
        u=('Cut',4,a); v=('Cut',4,b)
        total=add(mul(u,k(3)),mul(v,k(5)))
        return ('Mux',w,('Ult',total,128),total,k(127))
    if name=='repeated_bounded_mul':
        product=mul(a,('Cut',3,b))
        return ('Mux',w,('Ult',a,4),add(product,product),c)
    if name=='unconstrained':return add(mul(a,b),c)
    raise ValueError(name)


def inputs(term):
    out={}
    def walk(t):
        if t[0]=='V':out[t[1]]=t[2]
        for a in t[1:]:
            if isinstance(a,tuple):walk(a)
    walk(term);return out


def emit(term,module):
    """Lower explicit AST to wires so Verilog contextual sizing is controlled."""
    lines=[]; memo={}
    def go(t):
        if t in memo:return memo[t]
        op,w=t[0],width(t)
        if op=='V':return t[1]
        if op=='K':return f"{w}'d{t[2]}"
        kids=[go(a) for a in t[1:] if isinstance(a,tuple)]
        def resize(v,source,target):
            if source==target:return v
            if source<target:return '{'+f"{target-source}'d0, {v}"+'}'
            # Never slice a literal/expression: each nonleaf is already a wire.
            key=f'z{len(lines)}';lines.append(f'wire [{target-1}:0] {key} = {v};');return key
        if op in ('Add','Mul','Shr'):
            a=resize(kids[0],width(t[2]),w)
            b=kids[1] if op=='Shr' else resize(kids[1],width(t[3]),w)
            expr=f'{a} '+{'Add':'+','Mul':'*','Shr':'>>'}[op]+f' {b}'
        elif op=='Abs':expr=f'$signed({kids[0]}) < 0 ? -{kids[0]} : {kids[0]}'
        elif op=='Mux':expr=f'{kids[0]} ? {kids[1]} : {kids[2]}'
        elif op=='Ult':expr=f'{kids[0]} < {width(t[1])}\'d{t[2]}'
        elif op=='Slt':expr=f'$signed({kids[0]}) < {width(t[1])}\'sd{t[2]}' if t[2]>=0 else f'$signed({kids[0]}) < -{width(t[1])}\'sd{-t[2]}'
        elif op=='And':expr=f'{kids[0]} && {kids[1]}'
        elif op=='Neg':expr=f'-{kids[0]}'
        elif op=='Sge0':expr=f'$signed({kids[0]}) >= 0'
        elif op=='Not':expr=f'!{kids[0]}'
        elif op in ('Cut','Ext','Assume'):expr=resize(kids[0],width(t[2]),w)
        else:raise ValueError(op)
        n=f'n{len(lines)}';lines.append(f'wire [{w-1}:0] {n} = {expr};');memo[t]=n;return n
    root=go(term)
    ports=', '.join([f'input [{w-1}:0] {n}' for n,w in sorted(inputs(term).items())]+[f'output [{width(term)-1}:0] out'])
    return f'module {module}({ports});\n'+'\n'.join(lines)+f'\nassign out = {root};\nendmodule\n'


def symbolic(term,env):
    import z3
    op,w=term[0],width(term)
    if op=='V':return env[term[1]]
    if op=='K':return z3.BitVecVal(term[2],w)
    values=[symbolic(a,env) for a in term[1:] if isinstance(a,tuple)]
    def resize(v):
        return z3.ZeroExt(w-v.size(),v) if v.size()<w else z3.Extract(w-1,0,v)
    if op=='Add':return resize(values[0])+resize(values[1])
    if op=='Mul':return resize(values[0])*resize(values[1])
    if op=='Shr':
        # A wide amount cannot be truncated; explicitly compare to data width.
        y=values[1]; x=resize(values[0])
        if y.size()>w:return z3.If(z3.UGE(y,w),z3.BitVecVal(0,w),z3.LShR(x,z3.Extract(w-1,0,y)))
        return z3.LShR(x,z3.ZeroExt(w-y.size(),y))
    if op=='Abs':return z3.If(values[0]<0,-values[0],values[0])
    if op=='Mux':return z3.If(values[0]!=0,values[1],values[2])
    if op=='Ult':return z3.If(z3.ULT(values[0],term[2]),z3.BitVecVal(1,1),z3.BitVecVal(0,1))
    if op=='Slt':return z3.If(values[0]<z3.BitVecVal(term[2],values[0].size()),z3.BitVecVal(1,1),z3.BitVecVal(0,1))
    if op=='And':return z3.If(z3.And(values[0]!=0,values[1]!=0),z3.BitVecVal(1,1),z3.BitVecVal(0,1))
    if op=='Neg':return -resize(values[0])
    if op=='Sge0':return z3.If(values[0]>=0,z3.BitVecVal(1,1),z3.BitVecVal(0,1))
    if op=='Not':return z3.If(values[0]==0,z3.BitVecVal(1,1),z3.BitVecVal(0,1))
    if op in ('Ext','Cut','Assume'):return resize(values[0])
    raise ValueError(op)
