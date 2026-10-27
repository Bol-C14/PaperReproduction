"""Budget-limited sequential event scheduler. Models see observed stage outcomes only."""
import json,time,sys,itertools,warnings,math
from pathlib import Path
import numpy as np
import optuna
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern,WhiteKernel
from scipy.stats import norm
from eda import ROOT,EDA,SYNTH,PLACE
from retrieval import retrieve,tokens
from qor import logic,layout
optuna.logging.set_verbosity(optuna.logging.ERROR)
warnings.filterwarnings('ignore',category=UserWarning)
MANIFEST=json.loads((ROOT/'benchmarks/manifest.json').read_text())['designs']

def data():return [dict(d,code=(ROOT/d['rtl']).read_text(),spec=(ROOT/d['spec']).read_text()) for d in MANIFEST]

def gp_pick(options,obs,rng):
    if len(obs)<2:return int(rng.choice(options))
    # Categorical one-hot; stationary Matérn is an explicit local modeling assumption.
    size=max(max(options)+1,max(obs)+1); X=np.eye(size)
    model=GaussianProcessRegressor(kernel=Matern(nu=2.5)+WhiteKernel(1e-6),optimizer=None,normalize_y=True,alpha=1e-6)
    model.fit(X[list(obs)],list(obs.values()));mu,sd=model.predict(X[options],return_std=True)
    improvement=min(obs.values())-mu-.001;z=improvement/np.maximum(sd,1e-12)
    ei=improvement*norm.cdf(z)+sd*norm.pdf(z)
    return options[int(np.argmax(ei))]

class Search:
    def __init__(self,design,method,seed,warm,budget=18,runid=None):
        self.design=design;self.method=method;self.seed=seed;self.warm=warm;self.budget=budget;self.rng=np.random.default_rng(seed);self.prune_ratio=1.05
        self.eda=EDA(runid or f'{design["id"]}_{method}_{seed}');self.syn={};self.obs={};self.placed={};self.events=[];self.studies={};self.start=time.monotonic();self.ref=None
    def event(self,kind,**kw):self.events.append(dict(event=kind,at_calls=len(self.eda.records),**kw))
    def qs(self,r):return logic(r['area'],r['power'],r['slack'],self.ref)
    def qp(self,r):return layout(r['area'],r['power'],r['slack'],self.ref)
    def synth(self,s,label='search'):
        if s in self.syn:return self.syn[s]
        r=self.eda.evaluate(self.design,s,label=label);self.syn[s]=r;return r
    def place(self,s,p,label='search'):
        assert (s,p) not in self.placed
        r=self.eda.evaluate(self.design,s,p,self.syn[s],label);self.placed[s,p]=r;return r
    def choose(self,options,obs,stage,parent=0):
        if self.method=='random':return int(self.rng.choice(options))
        model='tpe' if (stage=='place' and self.method!='ast_gp_all') or self.method=='ast_tpe_all' else 'gp'
        if model=='gp':return gp_pick(options,obs,self.rng)
        key=(stage,parent)
        if key not in self.studies:
            self.studies[key]=optuna.create_study(sampler=optuna.samplers.TPESampler(seed=self.seed+parent+19,n_startup_trials=2))
            for p,y in obs.items():self.studies[key].add_trial(optuna.trial.create_trial(params={'p':p},distributions={'p':optuna.distributions.CategoricalDistribution(list(range(len(PLACE) if stage=='place' else len(SYNTH))))},value=y))
        study=self.studies[key]
        # Rebuild on actual observations; unexecuted duplicate proposals never get fake outcomes.
        for _ in range(32):
            tr=study.ask();p=tr.suggest_categorical('p',list(range(len(PLACE) if stage=='place' else len(SYNTH))))
            if p in options:
                self.pending=(study,tr);return p
            study.tell(tr,state=optuna.trial.TrialState.FAIL)
        self.pending=None;return int(self.rng.choice(options))
    def feedback(self,r,stage):
        if getattr(self,'pending',None):
            study,tr=self.pending;study.tell(tr,self.qp(r) if stage=='place' else self.qs(r));self.pending=None
    def run(self):
        # Common default reference evaluated in EVERY run and charged to its budget.
        a=self.synth(0,'reference');b=self.place(0,0,'reference');self.ref=b
        ws,wp=self.warm
        if ws not in self.syn:self.synth(ws,'warmstart')
        if (ws,wp) not in self.placed:self.place(ws,wp,'warmstart')
        self.event('warmstart',s=ws,p=wp)
        multi='tournament' in self.method
        if self.method=='random':
            while len(self.eda.records)<self.budget:
                pairs=[(s,p) for s in range(len(SYNTH)) for p in range(len(PLACE)) if (s,p) not in self.placed and (s in self.syn or len(self.eda.records)+2<=self.budget)]
                if not pairs:break
                s,p=pairs[int(self.rng.integers(len(pairs)))];self.synth(s);self.place(s,p)
        elif not multi:
            while len(self.syn)<len(SYNTH) and len(self.eda.records)<self.budget:
                s=self.choose([i for i in range(len(SYNTH)) if i not in self.syn],{i:self.qs(v) for i,v in self.syn.items()},'synth');r=self.synth(s);self.feedback(r,'synth')
            s=min(self.syn,key=lambda x:(self.qs(self.syn[x]),x));self.event('single_promote',s=s)
            self.optimize_parent(s,prune=False)
        else:
            # Promote when incumbent stays unchanged for two evaluations; upstream BO continues.
            promoted=[];active=[];stable=0;last=None
            while len(self.eda.records)<self.budget:
                best=min(self.syn,key=lambda x:(self.qs(self.syn[x]),x))
                stable=stable+1 if last==best else 0;last=best
                if stable>=2 and best not in promoted:
                    promoted.append(best);active.append(best);self.event('stable_promote',s=best,stability=stable)
                    if not self.optimize_parent(best,prune=('no_prune' not in self.method),max_new=2):active.remove(best)
                available=[i for i in range(len(SYNTH)) if i not in self.syn]
                if not available:break
                s=self.choose(available,{i:self.qs(v) for i,v in self.syn.items()},'synth');r=self.synth(s);self.feedback(r,'synth')
            # Finite-space termination: promote at most three observed parents, by QoR, without oracle outcomes.
            for s in sorted(self.syn,key=lambda x:(self.qs(self.syn[x]),x)):
                if len(promoted)>=3:break
                if s not in promoted:promoted.append(s);active.append(s);self.event('terminal_promote',s=s)
            for s in list(active):
                if len(self.eda.records)>=self.budget:break
                if not self.optimize_parent(s,prune=('no_prune' not in self.method),max_new=1):active.remove(s)
            while active and len(self.eda.records)<self.budget:
                progressed=False
                for s in list(active):
                    if len(self.eda.records)>=self.budget:break
                    before=len(self.eda.records);self.optimize_parent(s,prune=False,max_new=1);progressed|=len(self.eda.records)>before
                if not progressed:break
        best=min(self.placed.values(),key=lambda r:(self.qp(r),r['s'],r['p']))
        result={'run':self.eda.runid,'design':self.design['id'],'method':self.method,'seed':self.seed,'warm':list(self.warm),'budget':self.budget,'calls':len(self.eda.records),'unique_synth':len(self.syn),'unique_full':len(self.placed),'best_qor':self.qp(best),'best':best,'reference':self.ref,'wall_s':time.monotonic()-self.start,'eda_wall_s':sum(r['wall_s'] for r in self.eda.records),'events':self.events,'early_stop':'finite space or global budget; long-stability stage stopping not implemented'}
        (ROOT/'results'/f'{self.eda.runid}.summary.json').write_text(json.dumps(result,indent=2));return result
    def optimize_parent(self,s,prune,max_new=999):
        # First child uses the FULL warmstart vector's downstream parameter.
        p=self.warm[1];new=0
        if (s,p) not in self.placed and len(self.eda.records)<self.budget:
            baseline=min(self.qp(r) for r in self.placed.values());r=self.place(s,p);new+=1
            if prune and self.qp(r)>baseline*self.prune_ratio:
                self.event('prune',s=s,qor=self.qp(r),baseline=baseline,threshold=self.prune_ratio);return False
        while len(self.eda.records)<self.budget and new<max_new:
            opts=[p for p in range(len(PLACE)) if (s,p) not in self.placed]
            if not opts:break
            obs={p:self.qp(r) for (ss,p),r in self.placed.items() if ss==s};p=self.choose(opts,obs,'place',s);r=self.place(s,p);self.feedback(r,'place');new+=1
            self.event('baseline_update',qor=min(self.qp(v) for v in self.placed.values()))
        return True

def main():
    ds=[d for d in data() if d['split']!='target_stress'];phase=sys.argv[1] if len(sys.argv)>1 else 'all'
    if phase=='legacy':
        db=[]
        for d in ds[:3]:
            r=Search(d,'random',100,(0,0),18,runid='legacy_'+d['id']).run();db.append({'id':d['id'],'config':[r['best']['s'],r['best']['p']],'run':r['run']})
        (ROOT/'results/legacy_db.json').write_text(json.dumps(db,indent=2));return
    db=json.loads((ROOT/'results/legacy_db.json').read_text());config={d['id']:d['config'] for d in db};rankings={};methods=['random','gp_single','ast_single','numeric_single','text_single','fusion_control_single','ast_tournament','ast_tournament_no_prune','ast_gp_all','ast_tpe_all']
    for d in ds[3:]:
        rankings[d['id']]={mode:retrieve(d,ds[:3],mode) for mode in ('ast','numeric','text','fusion_control')}
        for method,seed in itertools.product(methods,(0,1,2)):
            runid=f'{d["id"]}_{method}_{seed}'
            if (ROOT/'results'/f'{runid}.summary.json').exists():continue
            mode='fusion_control' if method.startswith('fusion_control') else method.split('_')[0]
            warm=config[rankings[d['id']][mode][0]['id']] if mode in rankings[d['id']] else [0,0]
            r=Search(d,method,seed,warm,18).run();print(runid,r['calls'],r['best_qor'],flush=True)
    (ROOT/'results/retrieval_rankings.json').write_text(json.dumps(rankings,indent=2))
if __name__=='__main__':main()
