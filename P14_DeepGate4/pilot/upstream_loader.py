"""Auditable CPU import/fixture adapter; upstream files are never edited.

Sparse GAT layers are imported unchanged. Tokenizer loses only an unused
`deepgate` import. Baseline-only imports and external scatter are avoided.
History capacities are replaced only in DeepGate4.__init__, for tiny fixtures.
"""
import ast
import hashlib
import importlib.util
from pathlib import Path
import sys
import types
import torch
from torch_geometric.data import Data
from torch_geometric.utils import scatter

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'code'/'src'/'models'
EXPECTED_COMMIT='85e20742a2d4702426f94e86666cdcdb408fba8a'
PREFIX='p14_upstream'


def execute_module(name, text=None):
    qualified=f'{PREFIX}.{name}'
    path=SOURCE/f'{name}.py'
    spec=importlib.util.spec_from_file_location(qualified,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[qualified]=module
    if text is None:spec.loader.exec_module(module)
    else:exec(compile(text,str(path),'exec'),module.__dict__)
    return module


class ImportRepair(ast.NodeTransformer):
    def visit_Import(self,node):
        if any(a.name in {'deepgate','graphgps'} for a in node.names):return None
        return node
    def visit_ImportFrom(self,node):
        omitted={'dg_datasets.dg4_parser','torch_scatter','torch_geometric.graphgym.config','torch_geometric.graphgym.model_builder','PolarGate.model','DAGformer.dag_nodeformer'}
        return None if node.module in omitted else node
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=='sys.path.append':return None
        return node


def load(capacity=16):
    if not 1<=capacity<=16:raise ValueError('tiny fixture capacity must be 1..16')
    if PREFIX not in sys.modules:
        package=types.ModuleType(PREFIX);package.__path__=[str(SOURCE)]
        sys.modules[PREFIX]=package
    for name in ['mlp','tfmlp','plain_tf','plain_tf_linear','history']:
        if f'{PREFIX}.{name}' not in sys.modules:execute_module(name)
    tree=ImportRepair().visit(ast.parse((SOURCE/'dg2.py').read_text()))
    execute_module('dg2',ast.fix_missing_locations(tree))
    original_history=sys.modules[f'{PREFIX}.history'].History
    class FixtureHistory(original_history):
        """Unpinned bounded storage, inheriting upstream push/pull/reset semantics."""
        def __init__(self,num_embeddings,embedding_dim,device=None):
            if num_embeddings>capacity:raise ValueError('history size exceeds declared fixture capacity')
            torch.nn.Module.__init__(self)
            self.num_embeddings=num_embeddings;self.embedding_dim=embedding_dim
            self.emb=torch.empty(num_embeddings,embedding_dim,device='cpu')
            self._device=torch.device('cpu');self.reset_parameters()
        def check_ids(self,ids):
            if ids is not None and ids.numel() and (int(ids.min())<0 or int(ids.max())>=self.num_embeddings):
                raise IndexError('history fixture ID out of bounds')
        def pull(self,n_id=None):
            self.check_ids(n_id);return super().pull(n_id)
        def push(self,x,n_id=None,offset=None,count=None):
            self.check_ids(n_id)
            if offset is not None and count is not None:
                if any(a<0 or c<0 or a+c>self.num_embeddings for a,c in zip(offset.tolist(),count.tolist())):
                    raise IndexError('history fixture range out of bounds')
            return super().push(x,n_id,offset,count)
    tree=ImportRepair().visit(ast.parse((SOURCE/'dg4.py').read_text()))
    replacements=[]
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef) and cls.name=='DeepGate4':
            initializer=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
            for node in ast.walk(initializer):
                if isinstance(node,ast.Constant) and type(node.value) is int and node.value in {10_000_000,1_000_000}:
                    replacements.append({'line':node.lineno,'old':node.value,'new':capacity});node.value=capacity
    module=execute_module('dg4',ast.fix_missing_locations(tree))
    module.History=FixtureHistory;module.scatter=scatter;module.AreaData=Data
    # A separately named functional repair: never silently alter upstream forward.
    tree2=ast.parse((SOURCE/'dg4.py').read_text())
    cls=next(n for n in tree2.body if isinstance(n,ast.ClassDef) and n.name=='DeepGate4')
    forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
    hits=0
    for node in ast.walk(forward):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='all_update_hs' for t in node.targets):
            assert ast.unparse(node.value.args[0])=='hf_tf'
            node.value.args[0]=ast.Name(id='hs_tf',ctx=ast.Load());hits+=1
    assert hits==1
    variant_namespace=dict(module.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[forward],type_ignores=[])),str(SOURCE/'dg4.py'),'exec'),variant_namespace)
    class RepairedDeepGate4(module.DeepGate4):
        pass
    RepairedDeepGate4.forward=variant_namespace['forward']
    manifest={'upstream_commit':EXPECTED_COMMIT,'capacity':capacity,'initializer_constant_replacements':replacements,'original_files_unchanged':True,'source_sha256':{n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in ['dg4.py','dg2.py','plain_tf_linear.py','history.py','tfmlp.py','mlp.py']},'import_repairs':['remove unused deepgate import from tokenizer','omit unused baseline/GraphGym imports and parser import','use PyG native scatter mean instead of unavailable torch_scatter','omit relative sys.path mutation'],'cpu_adapter':'unpinned history bounded to fixture capacity; original push/pull/reset inherited; out-of-bound fixture IDs rejected','functional_variant':'upstream semantics retained as baseline; RepairedDeepGate4 changes only all_update_hs scatter input hf_tf to hs_tf'}
    return types.SimpleNamespace(DeepGate4=module.DeepGate4,RepairedDeepGate4=RepairedDeepGate4,DeepGate2=sys.modules[f'{PREFIX}.dg2'].DeepGate2,FixtureHistory=FixtureHistory,OriginalHistory=original_history,manifest=manifest)
