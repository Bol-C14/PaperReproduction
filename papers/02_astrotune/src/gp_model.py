"""GP v2: physical parameter geometry, independent of enumeration IDs."""
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern,WhiteKernel
from scipy.stats import norm
from eda import SYNTH,PLACE

def features(stage,space=None):
    space=space if space is not None else (SYNTH if stage=='synth' else PLACE)
    if stage=='synth':
        return np.array([[float(c['fast']),(np.log(c['delay_ps'])-np.log(100))/(np.log(2000)-np.log(100))] for c in space])
    if stage=='place':return np.array([[(c['util']-.25)/.30,(c['density']-.65)/.20] for c in space])
    raise ValueError(stage)

def acquisition(options,obs,stage,space=None):
    X=features(stage,space)
    # Canonical physical ordering also makes numerical/tie handling ID independent.
    options=sorted(options,key=lambda i:tuple(X[i]));seen=sorted(obs,key=lambda i:tuple(X[i]))
    model=GaussianProcessRegressor(kernel=Matern(length_scale=[1.,1.],nu=2.5)+WhiteKernel(1e-6),optimizer=None,normalize_y=True,alpha=1e-6)
    model.fit(X[seen],[obs[i] for i in seen]);mu,sd=model.predict(X[options],return_std=True)
    improvement=min(obs.values())-mu-.001;z=improvement/np.maximum(sd,1e-12)
    ei=improvement*norm.cdf(z)+sd*norm.pdf(z)
    return options,mu,sd,ei

def gp_pick(options,obs,rng,stage='synth',space=None):
    X=features(stage,space);canonical=sorted(options,key=lambda i:tuple(X[i]))
    if len(obs)<2:return int(canonical[int(rng.integers(len(canonical)))])
    ids,mu,sd,ei=acquisition(canonical,obs,stage,space)
    return ids[int(np.argmax(ei))]
