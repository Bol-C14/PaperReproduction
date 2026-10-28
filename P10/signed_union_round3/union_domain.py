"""Sound finite bit-vector interval unions; signed comparisons refine bit patterns.

All intervals are inclusive unsigned encodings. Signed ranges crossing zero
retain two intervals. Transfer functions overapproximate, never enumerate inputs.
"""
from engine import width
LAST=[]

def norm(xs):
 out=[]
 for lo,hi in sorted((a,b) for a,b in xs if a<=b):
  if out and lo<=out[-1][1]+1:out[-1]=(out[-1][0],max(hi,out[-1][1]))
  else:out.append((lo,hi))
 return tuple(out) if len(out)<=64 else ((out[0][0],out[-1][1]),)

def meet(a,b):return norm((max(x,u),min(y,v)) for x,y in a for u,v in b)
def join(a,b):return norm((*a,*b))
def wrap(lo,hi,w):
 m=1<<w
 if hi-lo>=m-1:return ((0,m-1),)
 q,r=lo//m,hi//m
 if q==r:return ((lo%m,hi%m),)
 return norm(((0,hi%m),(lo%m,m-1)))

def signed_range(lo,hi,w):
 h=1<<(w-1);lo=max(lo,-h);hi=min(hi,h-1)
 if lo>hi:return ()
 if hi<0:return ((lo+(1<<w),hi+(1<<w)),)
 if lo>=0:return ((lo,hi),)
 return ((0,hi),(lo+(1<<w),(1<<w)-1))

def unary(xs,w,op):
 out=()
 for lo,hi in xs:
  if op=='Neg':out=join(out,wrap(-hi,-lo,w))
  else:
   h=1<<(w-1)
   if lo<h:out=join(out,((lo,min(hi,h-1)),))
   if hi>=h:out=join(out,wrap(-hi,-max(lo,h),w))
 return out

def ranges_union(nodes,groups,best):
 widths={c:width(b[2]) for c,b in best.items() if isinstance(b[2],tuple)}
 bounds={c:((0,(1<<w)-1),) for c,w in widths.items()}
 def restrict(c,value,guard,truth=True,seen=frozenset()):
  if (guard,truth) in seen:return value
  seen=seen|{(guard,truth)}
  for _,g in groups[guard]:
   cs=[nodes[x]['eclass'] for x in g['children']];op=g['op'];w=widths[c];m=1<<w
   if op=='Not':value=meet(value,restrict(c,value,cs[0],not truth,seen))
   elif op=='And':
    if truth:
     value=restrict(c,value,cs[0],True,seen);value=restrict(c,value,cs[1],True,seen)
    else:value=meet(value,join(restrict(c,value,cs[0],False,seen),restrict(c,value,cs[1],False,seen)))
   elif op=='Ult' and cs[0]==c:
    k=best[cs[1]][2]
    value=meet(value,((0,k-1),) if truth else ((k,m-1),))
   elif op in ('Slt','Sge0') and cs[0]==c:
    h=1<<(w-1);k=0 if op=='Sge0' else best[cs[1]][2]
    less=not truth if op=='Sge0' else truth
    value=meet(value,signed_range(-h,k-1,w) if less else signed_range(k,h-1,w))
  return value
 for _ in range(40):
  changed=False
  for c,items in groups.items():
   if c not in bounds:continue
   w=widths[c];full=((0,(1<<w)-1),)
   for _,n in items:
    cs=[nodes[x]['eclass'] for x in n['children']];op=n['op'];new=full
    if op=='K':new=((best[cs[1]][2],best[cs[1]][2]),)
    elif op in ('Add','Mul'):
     new=()
     for a,b in bounds[cs[1]]:
      for d,e in bounds[cs[2]]:
       new=join(new,wrap(a+d,b+e,w) if op=='Add' else wrap(a*d,b*e,w))
    elif op=='Ext':new=bounds[cs[1]]
    elif op=='Cut':
     new=()
     for a,b in bounds[cs[1]]:new=join(new,wrap(a,b,w))
    elif op in ('Abs','Neg'):new=unary(bounds[cs[1]],w,op)
    elif op=='Shr':
     new=()
     for a,b in bounds[cs[1]]:
      for d,e in bounds[cs[2]]:new=join(new,((a>>min(e,w),b>>min(d,w)),))
    elif op=='Assume':new=restrict(cs[1],bounds[cs[1]],cs[2])
    elif op=='Mux':new=join(bounds[cs[2]],bounds[cs[3]])
    narrowed=meet(bounds[c],new)
    if narrowed!=bounds[c]:bounds[c]=narrowed;changed=True
  if not changed:break
 LAST.append({'classes':len(bounds),'disjoint_classes':sum(len(v)>1 for v in bounds.values()),'bottom_classes':sum(not v for v in bounds.values())})
 # Old rule interface expects a hull. Empty care must never imply a rewrite.
 return {c:(v[0][0],v[-1][1]) if v else (0,(1<<widths[c])-1) for c,v in bounds.items()}
