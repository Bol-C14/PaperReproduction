"""Independent count/likelihood diagnosis of cached star-graph BT fits."""
import sys,json,pathlib,math,warnings
import numpy as np,pandas as pd
from scipy.optimize import brentq, minimize
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
root=pathlib.Path(sys.argv[1]); out=root/'results/arena-hard'; up=root/'checkouts/arena-hard/upstream';sys.path.insert(0,str(up))
from show_result import get_battles_from_row
from utils_math import compute_mle_elo
plan=json.loads((root/'assets/arena-hard/selection-plan.json').read_text()); base=plan['baseline']; rows=[]; independent={}
for m in plan['models']:
 if m==base: continue
 counts={'candidate':0,'baseline':0,'tie':0,'invalid':0}
 for line in (root/f'assets/arena-hard/data/arena-hard-v0.1/model_judgment/{plan["judges"][0]}/{m}.jsonl').read_text().splitlines():
  r=json.loads(line); assert r['baseline']==base and r['model']==m and r['judge']==plan['judges'][0]; r['question_id']=r['uid'];rows+=get_battles_from_row(r,False,3,base)
  for gi,g in enumerate(r['games']):
   v=g['score'];weight=3 if v in ['A>>B','B>>A'] else 1
   if v=='A=B': counts['tie']+=weight
   elif v in ['A>B','A>>B','B>A','B>>A']:
    candidate=(v.startswith('B') if gi==0 else v.startswith('A')); counts['candidate' if candidate else 'baseline']+=weight
   else: counts['invalid']+=1
 total=counts['candidate']+counts['baseline']+counts['tie']; probability=(counts['candidate']+.5*counts['tie'])/total
 # Separate scalar likelihood root, no upstream logistic matrix or rating conversion.
 root_beta=brentq(lambda b: total/(1+math.exp(-b))-(counts['candidate']+.5*counts['tie']),-30,30,xtol=1e-13)
 independent[m]={**counts,'total':total,'score_counts':100*probability,'score_scalar_root':100/(1+math.exp(-root_beta))}
df=pd.DataFrame(rows); elo=compute_mle_elo(df); original=100/(1+10**((elo[base]-elo)/400))
models=pd.Series(np.arange(len(plan['models'])),index=[base]+[m for m in plan['models'] if m!=base]); dup=pd.concat([df,df],ignore_index=True); n=len(dup); X=np.zeros((n,len(models))); X[np.arange(n),models[dup.model_a]]=math.log(10);X[np.arange(n),models[dup.model_b]]=-math.log(10);Y=np.zeros(n);Y[dup.winner=='model_a']=1.;tie=dup.winner=='tie';tie.iloc[len(tie)//2:]=False;Y[tie]=1.
fits=[]
for maxiter,tol in [(100,1e-8),(2000,1e-12)]:
 with warnings.catch_warnings(record=True) as ws:
  lr=LogisticRegression(fit_intercept=False,penalty=None,tol=tol,max_iter=maxiter);lr.fit(X,Y)
 scores=100/(1+np.exp(-math.log(10)*(lr.coef_[0]-lr.coef_[0][models[base]])))
 residual=1/(1+np.exp(-X@lr.coef_[0]))-Y
 errors={m:float(scores[models[m]]-independent[m]['score_counts']) for m in independent}
 fits.append({'max_iter':maxiter,'tol':tol,'n_iter':lr.n_iter_.tolist(),'warnings':[str(w.message) for w in ws],'gradient_inf_norm':float(abs(X.T@residual/len(Y)).max()),'maximum_abs_error_percentage_points':max(map(abs,errors.values())),'errors':errors})
def fun(beta):
 z=X[:,1:]@beta
 return float(np.mean(np.logaddexp(0,z)-Y*z)), X[:,1:].T@(expit(z)-Y)/len(Y)
opt=minimize(fun,np.zeros(X.shape[1]-1),jac=True,method='L-BFGS-B',options={'ftol':1e-15,'gtol':1e-12,'maxiter':2000})
refined=100*expit(math.log(10)*opt.x)
refined_errors={m:float(refined[models[m]-1]-independent[m]['score_counts']) for m in independent}
print('REFINED',opt.message,opt.nit,float(abs(opt.jac).max()),refined_errors,flush=True)
assert max(map(abs,refined_errors.values()))<.0001
assert max(abs(v['score_counts']-v['score_scalar_root']) for v in independent.values())<1e-10
refinement={'method':'same matrix log-loss, baseline coefficient fixed zero, scipy L-BFGS-B ftol1e-15 gtol1e-12','success':bool(opt.success),'message':str(opt.message),'iterations':int(opt.nit),'gradient_inf_norm':float(abs(opt.jac).max()),'maximum_abs_error_percentage_points':max(map(abs,refined_errors.values())),'errors':refined_errors}
for m,v in independent.items():
 g=df[df.model_b==m];assert len(g)==v['total'];assert sum(g.winner=='model_b')==v['candidate'];assert sum(g.winner=='model_a')==v['baseline'];assert sum(g.winner=='tie')==v['tie'];v['upstream_score']=float(original[m])
result={'independent_counts':independent,'fits':fits,'refined_matrix_fit':refinement,'formula':'100*(candidate_weight+0.5*tie_weight)/total_weight, star graph anchored baseline','scope':'full primary 19 candidates; independent scalar likelihood roots and upstream matrix counts','frozen_selection_unchanged':True}
(out/'numerical_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
