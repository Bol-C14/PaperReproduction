"""Interpret metadata from a tiny allowlisted pickle language; execute no globals.

No pickle.load, Unpickler, torch.load, eval, dynamic import, or callable dispatch.
Torch storage/tensor references become ordinary symbolic dictionaries.
"""
from pathlib import Path
import collections, hashlib, json, math, pickletools, zipfile

class StaticMap(dict):
    pass

ALLOWED_GLOBALS = {'collections OrderedDict', 'torch FloatStorage', 'torch LongStorage', 'torch._utils _rebuild_tensor_v2'}
MARK = object()

def inspect_pickle(data):
    if len(data) > 1_000_000:
        raise ValueError('pickle metadata size gate')
    stack, memo, globals_seen = [], {}, set()
    def marked():
        index = next(i for i in range(len(stack)-1,-1,-1) if stack[i] is MARK)
        values=stack[index+1:]
        del stack[index:]
        return values
    for count,(op,arg,pos) in enumerate(pickletools.genops(data)):
        if count > 100_000:
            raise ValueError('opcode count gate')
        name=op.name
        if name=='PROTO':
            if arg != 2: raise ValueError('Only audited protocol 2 accepted')
        elif name=='MARK': stack.append(MARK)
        elif name=='EMPTY_DICT': stack.append(StaticMap())
        elif name=='EMPTY_LIST': stack.append([])
        elif name=='EMPTY_TUPLE': stack.append(())
        elif name in {'BININT','BININT1','BININT2','BINFLOAT','BINUNICODE'}: stack.append(arg)
        elif name=='NEWFALSE': stack.append(False)
        elif name in {'BINPUT','LONG_BINPUT'}: memo[arg]=stack[-1]
        elif name in {'BINGET','LONG_BINGET'}: stack.append(memo[arg])
        elif name=='TUPLE': stack.append(tuple(marked()))
        elif name in {'TUPLE1','TUPLE2','TUPLE3'}:
            n=int(name[-1]); vals=stack[-n:]; del stack[-n:]; stack.append(tuple(vals))
        elif name=='GLOBAL':
            if arg not in ALLOWED_GLOBALS: raise ValueError(f'Unsupported GLOBAL {arg}')
            globals_seen.add(arg); stack.append(('symbolic_global',arg))
        elif name=='BINPERSID':
            storage=stack.pop()
            if not (isinstance(storage,tuple) and len(storage)==5 and storage[0]=='storage' and storage[1] in [('symbolic_global','torch FloatStorage'),('symbolic_global','torch LongStorage')]):
                raise ValueError('Unsupported persistent storage metadata')
            stack.append(dict(storage_type=storage[1][1],storage_key=storage[2],original_device=storage[3],storage_numel=storage[4]))
        elif name=='REDUCE':
            args=stack.pop(); symbol=stack.pop()
            if symbol==('symbolic_global','collections OrderedDict') and args==(): stack.append(StaticMap())
            elif symbol==('symbolic_global','torch._utils _rebuild_tensor_v2'):
                storage,offset,shape,stride,requires_grad,hooks=args
                if not all(type(i) is int and i>=0 for i in shape):raise ValueError('Invalid tensor shape')
                stack.append(dict(__tensor__=True,**storage,offset=offset,shape=list(shape),stride=list(stride),requires_grad=requires_grad))
            else: raise ValueError('Unsupported symbolic REDUCE')
        elif name in {'SETITEM','SETITEMS'}:
            vals=marked() if name=='SETITEMS' else [stack.pop(-2),stack.pop()]
            if len(vals)%2:raise ValueError('Odd mapping values')
            target=stack[-1]
            for i in range(0,len(vals),2):target[vals[i]]=vals[i+1]
        elif name=='APPEND':
            value=stack.pop();stack[-1].append(value)
        elif name=='APPENDS':
            values=marked(); stack[-1].extend(values)
        elif name=='BUILD':
            state=stack.pop();target=stack[-1]
            if type(target) is not StaticMap or not isinstance(state,dict):raise ValueError('Unsupported BUILD')
            target.symbolic_attributes=state
        elif name=='STOP':
            if len(stack)!=1:raise ValueError('Unexpected final stack')
            return stack[0],sorted(globals_seen),count+1
        else:raise ValueError(f'Unsupported opcode {name} at {pos}')
    raise ValueError('Missing STOP')

def inspect_checkpoint(path):
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        if len(entries)>1000 or sum(i.file_size for i in entries)>20_000_000:
            raise ValueError('ZIP metadata size gate')
        names=[i.filename for i in entries if i.filename.endswith('/data.pkl')]
        if len(names)!=1:raise ValueError('Ambiguous metadata')
        raw=archive.read(names[0]);root,globals_seen,nops=inspect_pickle(raw)
    tensors=root['state_dict']
    assert all(isinstance(v,dict) and v.get('__tensor__') for v in tensors.values())
    return dict(file=path.name,inspection='non-executing symbolic metadata only',epoch=root.get('epoch'),top_keys=list(root),globals=globals_seen,opcodes=nops,tensor_count=len(tensors),tensor_elements=sum(math.prod(v['shape']) for v in tensors.values()),state_dict=tensors)

if __name__=='__main__':
    root=Path(__file__).resolve().parent
    rows=[inspect_checkpoint(p) for p in sorted((root.parent/'.checkpoint-cache').glob('*.pth'))]
    (root/'checkpoint_metadata.json').write_text(json.dumps(rows,indent=2)+'\n')
    for row in rows:
        print(row['file'],'epoch',row['epoch'],'tensors',row['tensor_count'],'elements',row['tensor_elements'],'roots',sorted({k.split('.')[0] for k in row['state_dict']}))
