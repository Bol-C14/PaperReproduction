"""Inventory official demo assets without importing source or executing pickle globals."""
import argparse,collections,hashlib,json,pickle,re
from pathlib import Path
class Passive:
    def __init__(self,*args,**kwargs):pass
class Restricted(pickle.Unpickler):
    def find_class(self,module,name):
        if (module,name)==('collections','defaultdict'):return collections.defaultdict
        if module=='builtins' and name in ['list','set','dict','tuple','frozenset']:return {'list':list,'set':set,'dict':dict,'tuple':tuple,'frozenset':frozenset}[name]
        if (module,name) in [('DG','Node'),('DG','Graph'),('networkx.classes.digraph','DiGraph'),('networkx.classes.coreviews','AdjacencyView'),('networkx.classes.coreviews','AtlasView'),('networkx.classes.reportviews','DiDegreeView'),('networkx.classes.reportviews','InDegreeView'),('networkx.classes.reportviews','OutDegreeView'),('networkx.classes.reportviews','NodeView'),('networkx.classes.reportviews','OutEdgeView'),('networkx.classes.reportviews','InEdgeView')]:return Passive
        raise pickle.UnpicklingError(f'unsupported global {module}.{name}')
def load(p):
    with p.open('rb') as f:return Restricted(f).load()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('repository');a=ap.parse_args();r=Path(a.repository);root=Path(__file__).resolve().parent
    paths={'rtl_code':r/'data_collect/rtl/dataset/cone/spi','rtl_graph':r/'data_collect/rtl/rtl2graph/cone_graph/ori/spi','net_graph':r/'data_collect/netlist/dataset/cone_graph/ori/spi','label':r/'data_collect/label/ppa/cone_pwr_area/spi'}
    ids={k:set() for k in paths}
    for k,p in paths.items():
        for f in p.iterdir():
            if k=='rtl_code' and f.suffix=='.v' and f.stem!='spi':ids[k].add(f.stem)
            if k=='rtl_graph' and f.name.endswith('_ori.pkl'):ids[k].add(f.name[:-8])
            if k=='net_graph' and f.suffix=='.pkl' and 'node_dict' not in f.name:ids[k].add(f.stem)
            if k=='label' and f.suffix=='.json':ids[k].add(f.stem)
    rows=[]
    nd=load(paths['net_graph']/'spi_node_dict.pkl')
    for sid in sorted(set.union(*ids.values())):
        row={'sample_id':sid,'present':{k:sid in v for k,v in ids.items()}}
        for kind,fn in [('rtl_graph',sid+'_ori.pkl'),('net_graph',sid+'.pkl')]:
            p=paths[kind]/fn
            if not p.exists():continue
            try:
                g=load(p)
                if isinstance(g,dict):nodes=set(g)|{x for vs in g.values() for x in vs};edges=sum(map(len,g.values()))
                else:nodes=set(g._node);edges=sum(map(len,g._succ.values()))
                row[kind]={'nodes':len(nodes),'edges':edges}
                if kind=='net_graph':row[kind]['unmapped_nodes']=sorted(str(n) for n in nodes if n not in nd)
            except Exception as e:row[kind]={'error':str(e)}
        lp=paths['label']/(sid+'.json')
        if lp.exists():row['label']=json.loads(lp.read_text())
        cp=paths['rtl_code']/(sid+'.v')
        if cp.exists():
            text=cp.read_text();scalar=set(re.findall(r'\binput\s+(\w+)\s*;',text));uses=[{'port':n,'index':int(ix)} for n,ix in re.findall(r'\b(\w+)\[(\d+)\]',text) if n in scalar and int(ix)>0];row['scalar_input_out_of_range_static']=uses
        rows.append(row)
    files=[]
    for p in sorted(r.rglob('*')):
        if p.is_file() and '.git' not in p.relative_to(r).parts:
            files.append({'path':str(p.relative_to(r)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    summary=json.loads((r/'dataset/dataset_summary/demo.json').read_text())
    result={'revision':'123bec383aba1d4ce808db486308aaaeb53a25ca','official_url':'https://github.com/hkust-zhiyao/CircuitFusion','counts':{k:len(v) for k,v in ids.items()},'complete_id_intersection':sorted(set.intersection(*ids.values())),'rows':rows,'checkpoint_files':[x['path'] for x in files if x['path'].endswith(('.pt','.pth','.safetensors','.ckpt'))],'split_files':[x['path'] for x in files if x['path'].startswith('dataset/dataset_js/')],'summary_demo':{'outer_rows':len(summary),'first_row_fields':len(summary[0]) if summary else None,'sample_id_join':'not established; demo_lst names b14, inspected summary describes reg3, SPI IDs not attached'},'netlist_node_types':dict(collections.Counter(str(getattr(v,'type',None)) for v in nd.values())),'license_files':[x['path'] for x in files if Path(x['path']).name.lower() in ['license','copying','license.txt']],'limitations':['ID joins do not prove semantic equivalence of released RTL and DC netlist cones','PPA JSON values exist; units, library, activity, constraints and fidelity remain unverified','pickles loaded through strict passive allowlist, upstream code never imported','No official weights found in this immutable tree; external hosts not exhaustively excluded'],'files':files}
    (root/'official_asset_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['files','rows']},indent=2))
if __name__=='__main__':main()
