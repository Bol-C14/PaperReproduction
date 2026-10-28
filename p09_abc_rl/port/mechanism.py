"""Small deterministic retrieval/control contract. No substitute learned policy."""
import math
ACTIONS=('refactor','refactor -z','rewrite','rewrite -z','resub','resub -z','balance')
def nearest_distance(query,bank):
 def distance(v):
  if len(query)!=len(v): raise ValueError('dimension mismatch')
  nq=math.sqrt(sum(x*x for x in query));nv=math.sqrt(sum(x*x for x in v))
  if not nq or not nv: raise ValueError('zero-norm graph embedding')
  return max(0.,min(2.,1-sum(a*b for a,b in zip(query,v))/(nq*nv)))
 if not bank: raise ValueError('empty training-only bank')
 return min(distance(v) for v in bank)
def guidance_exponent(distance,threshold=.007,scaling=100.):
 z=scaling*(distance-threshold)
 if z>=0:
  e=math.exp(-z);return e/(1+e)
 return 1/(1+math.exp(z))
def prior_weights(probabilities,beta):
 if len(probabilities)!=7 or not 0<=beta<=1: raise ValueError('invalid prior')
 if any(p<=0 for p in probabilities): raise ValueError('requires positive softmax probabilities')
 return [p**beta for p in probabilities]
