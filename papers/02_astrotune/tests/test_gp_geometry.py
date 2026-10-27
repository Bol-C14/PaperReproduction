"""Regression: posterior distinguishes unseen knobs and survives ID permutations."""
import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gp_model import features,acquisition,gp_pick
from eda import SYNTH,PLACE,ROOT
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern,WhiteKernel
from scipy.stats import norm
rows=[]
for stage,space,obs in [('synth',SYNTH,{0:.2,3:2.}),('place',PLACE,{0:.2,11:2.})]:
 options=[i for i in range(len(space)) if i not in obs];ids,mu,sd,ei=acquisition(options,obs,stage)
 assert np.ptp(ei)>1e-5,(stage,ei)
 assert sorted(ei)[-1]-sorted(ei)[-2]>1e-6,(stage,'test must not rely on a true tie',ei)
 choice=gp_pick(options,obs,np.random.default_rng(0),stage);physical=space[choice]
 for seed in range(20):
  perm=np.random.default_rng(seed).permutation(len(space));new=[space[i] for i in perm];old_to_new={int(old):i for i,old in enumerate(perm)}
  mapped={old_to_new[i]:y for i,y in obs.items()};opts=[old_to_new[i] for i in options]
  result=gp_pick(opts,mapped,np.random.default_rng(0),stage,new)
  assert new[result]==physical,(stage,seed,new[result],physical)
 # Reproduce the v1 bug, without any EDA call.
 X=np.eye(len(space));m=GaussianProcessRegressor(kernel=Matern(nu=2.5)+WhiteKernel(1e-6),optimizer=None,normalize_y=True,alpha=1e-6).fit(X[list(obs)],list(obs.values()))
 oldmu,oldsd=m.predict(X[options],return_std=True);imp=min(obs.values())-oldmu-.001;z=imp/oldsd;oldei=imp*norm.cdf(z)+oldsd*norm.pdf(z)
 assert np.ptp(oldei)<1e-12
 rows.append({'stage':stage,'physical_features':features(stage).tolist(),'observations':obs,'unseen_ids':ids,'mu':mu.tolist(),'sd':sd.tolist(),'ei':ei.tolist(),'ei_range':float(np.ptp(ei)),'selected_physical_config':physical,'id_permutations_passed':20,'v1_onehot_ei_range':float(np.ptp(oldei)),'true_eda_calls':0})
(ROOT/'results/gp_geometry_regression.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
