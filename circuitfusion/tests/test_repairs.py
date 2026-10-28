"""Deterministic controls against actual AST-extracted upstream functions.
No DGL/BERT/NV-Embed import, weights, API, or full training execution.
"""
import ast,contextlib,io,json,os,pickle,re,tempfile,time,types,unittest
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parents[1]
torch.set_num_threads(2)

def extract(variant,path,name,class_name=None,globals=None):
    tree=ast.parse((ROOT/variant/path).read_text())
    nodes=tree.body
    if class_name: nodes=next(x for x in nodes if isinstance(x,ast.ClassDef) and x.name==class_name).body
    fn=next(x for x in nodes if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name)
    env=dict(globals or {});exec(compile(ast.Module(body=[fn],type_ignores=[]),path,'exec'),env)
    return env[name]

class Tokens:
    def __init__(self): self.input_ids=torch.tensor([[1,2]]);self.attention_mask=torch.ones(1,2)
    def to(self,device): return self
class Summary:
    config=types.SimpleNamespace(vocab_size=10)
    def bert(self,**kw):
        c=kw['encoder_hidden_states'].mean(1,keepdim=True).repeat(1,2,1)
        return types.SimpleNamespace(last_hidden_state=c)
    def __call__(self,*args,**kw):
        return types.SimpleNamespace(loss=kw['encoder_hidden_states'].square().sum())

def stub():
    return types.SimpleNamespace(device='cpu',config={},graphormer=lambda d:(torch.tensor([[[1.,0.]]]),None),text_proj=nn.Identity(),tokenizer=lambda *a,**k:Tokens(),summary_enc=Summary(),sumamry_proj=nn.Identity(),mlm_probability=.15,mask=lambda ids,*a,**k:(ids,k['targets']))

class Repairs(unittest.TestCase):
    def test_fusion_source_original_ignores_fixed_uses_hdl(self):
        out={}
        for v in ['upstream_original','repaired']:
            fn=extract(v,'model/ckt_fusion/models/model_pretrain.py','finetune_forward','RTL_Fusion',{'torch':torch,'F':F,'all_to_device':lambda xs,d:iter(xs)})
            a=fn(stub(),([torch.zeros(1)]*6,['summary'],(torch.tensor([[[0.,1.]]]),None)))
            b=fn(stub(),([torch.zeros(1)]*6,['summary'],(torch.tensor([[[0.,-1.]]]),None)))
            out[v]=float((a-b).abs().max())
        self.assertEqual(out['upstream_original'],0.);self.assertGreater(out['repaired'],.1)
        METRICS['hdl_inference_sensitivity_max_abs']=out
    def test_mlm_source_original_ignores_fixed_uses_hdl(self):
        out={}
        for v in ['upstream_original','repaired']:
            fn=extract(v,'model/ckt_fusion/models/model_pretrain.py','pretrain_task_mlm_mixup','RTL_Fusion',{'torch':torch,'F':F})
            a=fn(stub(),torch.tensor([[[1.,0.]]]),(torch.tensor([[[0.,1.]]]),None),['summary'])
            b=fn(stub(),torch.tensor([[[1.,0.]]]),(torch.tensor([[[0.,3.]]]),None),['summary'])
            out[v]=float(abs(a-b))
        self.assertEqual(out['upstream_original'],0.);self.assertGreater(out['repaired'],.1)
        METRICS['hdl_mlm_sensitivity_abs']=out
    def test_summary_extension_and_export(self):
        outcomes={}
        class Auto:
            @staticmethod
            def from_pretrained(*args,**kwargs):
                return types.SimpleNamespace(encode=lambda *a,**kw:torch.tensor([[3.,4.]]))
        for v in ['upstream_original','repaired']:
            with tempfile.TemporaryDirectory() as td:
                old=os.getcwd();os.chdir(td)
                try:
                    Path('cone_summary/toy').mkdir(parents=True);Path('../unused') if False else None
                    # Relative register path stays inside the isolated temp directory.
                    Path('job').mkdir();Path('dataset/reg_lst').mkdir(parents=True)
                    Path('dataset/reg_lst/toy.json').write_text('["q"]')
                    Path('job/cone_summary/toy').mkdir(parents=True)
                    Path('job/cone_summary/toy/q.txt').write_text('xor two inputs')
                    Path('runtime').mkdir();os.chdir('job')
                    env={'os':os,'re':re,'time':time,'json':json,'pickle':pickle,'F':F,'AutoModel':Auto}
                    read=extract(v,'data_collect/rtl/rtl2summary/summary2vec.py','run_one_ep',globals=env)
                    if v=='upstream_original':
                        with self.assertRaises(FileNotFoundError): read('toy','q')
                        # Add .v solely to get beyond that independent original defect.
                        Path('cone_summary/toy/q.v').write_text('xor two inputs')
                    fn=extract(v,'data_collect/rtl/rtl2summary/summary2vec.py','get_dataset',globals={**env,'run_one_ep':read})
                    if v=='upstream_original':
                        with self.assertRaises(SystemExit): fn(['toy'])
                        self.assertFalse(Path('cone_summary_vec/toy/q.pkl').exists());outcomes[v]='wrong extension; then exits before export'
                    else:
                        fn(['toy']);a=pickle.loads(Path('cone_summary_vec/toy/q.pkl').read_bytes())
                        torch.testing.assert_close(a,torch.tensor([[.6,.8]]));outcomes[v]='txt read and normalized pickle exported'
                finally:os.chdir(old)
        METRICS['summary_export']=outcomes
    def test_gradient_accumulation_and_tail(self):
        counts={}
        for n in [1,128,129,130]:
            for variant in ['upstream_original','repaired']:
                model=Scalar();opt=CountingSGD(model.parameters(),lr=.001);scheduler=types.SimpleNamespace(count=0)
                def tick():scheduler.count+=1
                scheduler.step=tick
                main=next(x for x in ast.parse((ROOT/variant/'model/ckt_fusion/pretrain_align_all.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='main')
                epoch=next(x for x in main.body if isinstance(x,ast.For))
                body=[]
                for x in epoch.body:
                    if isinstance(x,ast.With):break
                    body.append(x)
                data=list(range(n));env={'torch':torch,'rtl_fusion':model,'net_enc':nn.Identity(),'optimizer':opt,'lr_scheduler':scheduler,'accelerator':types.SimpleNamespace(backward=lambda l:l.backward(),print=lambda *a:None),'accumulation_steps':128,'step':0,'train_loader_align':tuple(data for _ in range(8))}
                exec(compile(ast.Module(body=body,type_ignores=[]),'actual_training_loop','exec'),env)
                counts[f'{variant}_{n}']={'optimizer_steps':opt.count,'scheduler_steps':scheduler.count,'parameter':float(model.w.detach())}
                if variant=='repaired':
                    ref=Scalar();ropt=torch.optim.SGD(ref.parameters(),lr=.001)
                    for start in range(0,n,128):
                        ropt.zero_grad();loss=torch.stack([ref.loss(i) for i in range(start,min(n,start+128))]).mean();loss.backward();ropt.step()
                    self.assertEqual(opt.count,(n+127)//128);self.assertEqual(scheduler.count,opt.count)
                    torch.testing.assert_close(model.w,ref.w,rtol=1e-10,atol=1e-10)
                else:self.assertEqual(opt.count,n+n//128)
        METRICS['accumulation']=counts

class Scalar(nn.Module):
    def __init__(self):super().__init__();self.w=nn.Parameter(torch.tensor(.7,dtype=torch.float64))
    def loss(self,i):return (self.w*((i%7+1)/7)-.3)**2
    def forward(self,data,mode=None):
        loss=self.loss(data[0][0]);z=loss.detach()*0
        return loss,z,z,z,z,z
class CountingSGD(torch.optim.SGD):
    def __init__(self,*a,**k):super().__init__(*a,**k);self.count=0
    def step(self,*a,**k):self.count+=1;return super().step(*a,**k)
METRICS={}
if __name__=='__main__':
    with contextlib.redirect_stdout(io.StringIO()):result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Repairs))
    METRICS['tests_run']=result.testsRun;METRICS['successful']=result.wasSuccessful()
    (ROOT/'results/repair_controls.json').write_text(json.dumps(METRICS,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
