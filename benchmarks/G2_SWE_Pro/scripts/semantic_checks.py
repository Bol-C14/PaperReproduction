"""Independent bounded behavior probes of actual patched AST nodes.
Run only in the isolated grader, before hidden tests. Imports/Qt/services are replaced
by explicit fakes; results supplement, never replace, native unchanged verifiers.
"""
import ast,collections,json,sys,types,typing
from pathlib import Path
checks=[]
def check(name,fn):
    try:
        observed,expected=fn();checks.append({'name':name,'passed':observed==expected,'observed':observed,'expected':expected})
    except Exception as e:checks.append({'name':name,'passed':False,'error':type(e).__name__+': '+str(e)})
def nodes(file,names):
    tree=ast.parse(Path(file).read_text());selected=[n for n in tree.body if getattr(n,'name',None) in names]
    return ast.Module(body=selected,type_ignores=[])
root=Path('/app') if Path('/app').exists() else Path('/testbed');task=sys.argv[1]
if '01d1d149' in task:
    modules={'alpha':types.SimpleNamespace(__version__='1.2.3'),'beta':types.SimpleNamespace()}
    def load(name):
        if name not in modules:raise ImportError(name)
        return modules[name]
    ns={'Optional':typing.Optional,'Sequence':typing.Sequence,'importlib':types.SimpleNamespace(import_module=load)}
    exec(compile(nodes(root/'qutebrowser/utils/version.py',{'ModuleInfo','_module_versions'}),'<patched-AST>','exec'),ns)
    ns['MODULE_INFO']=collections.OrderedDict((n,ns['ModuleInfo'](n,('__version__',))) for n in ['alpha','beta','gamma'])
    check('known_unknown_absent_version_lines',lambda:(ns['_module_versions'](),['alpha: 1.2.3','beta: yes','gamma: no']))
    def changed():
        modules['alpha'].__version__='2.0';ns['MODULE_INFO']['alpha']._reset_cache()
        return ns['_module_versions'](),['alpha: 2.0','beta: yes','gamma: no']
    check('named_reset_then_recompute',changed)
    ns['MODULE_INFO']=collections.OrderedDict(reversed(list(ns['MODULE_INFO'].items())))
    check('mapping_order_preserved',lambda:(ns['_module_versions'](),['gamma: no','beta: yes','alpha: 2.0']))
elif '0833b5f6' in task:
    def emission(code):
        events=[];queue=[]
        class Signal:
            def __init__(self,label):self.label=label
            def emit(self,*args):events.append([self.label,list(args)])
        class Reply:
            def __init__(self,parent):
                self.errorOccurred=Signal('modern');self.error=Signal('legacy');self.finished=Signal('finished')
            def setRequest(self,x):pass
            def setUrl(self,x):pass
            def setOpenMode(self,x):pass
            def setError(self,*x):pass
        timer=types.SimpleNamespace(singleShot=lambda delay,callback:queue.append((delay,callback)))
        ns={'QNetworkReply':Reply,'QIODevice':types.SimpleNamespace(OpenModeFlag=types.SimpleNamespace(ReadOnly=1)),'QTimer':timer}
        exec(compile(nodes(root/'qutebrowser/browser/webkit/network/networkreply.py',{'ErrorNetworkReply'}),'<patched-AST>','exec'),ns)
        ns['ErrorNetworkReply'](types.SimpleNamespace(url=lambda:'qute://probe'),'probe error',code)
        before=list(events)
        for delay,callback in queue:
            assert delay==0;callback()
        return {'before_callbacks':before,'after_callbacks':events},{'before_callbacks':[],'after_callbacks':[['modern',[code]],['finished',[]]]}
    for code in [0,1,42]:check('modern_error_then_finished_'+str(code),lambda code=code:emission(code))
else:
    ns={'Union':typing.Union,'Iterator':typing.Iterator}
    exec(compile(nodes(root/'scripts/new-solr-updater.py',{'find_keys','parse_log'}),'<patched-AST>','exec'),ns)
    check('nested_string_traversal_order',lambda:(list(ns['find_keys']({'key':'root','x':[{'key':'a'},{'z':{'key':'b'}}]})),['root','a','b']))
    check('non_string_key_values_excluded',lambda:(list(ns['find_keys']({'key':7,'x':[{'key':None},{'key':'a'}]})),['a']))
    check('unsupported_container_not_recursed',lambda:(list(ns['find_keys'](({'key':'tuple'},))),[]))
    for action in ['save','save_many']:
        def removed(action=action):
            before={'key':'book','works':[{'key':'old-work'}]};after={'key':'book','works':[{'key':'new-work'}]}
            record={'action':action,'data':{'changeset':{'old_docs':[before],'docs':[after]}}}
            return list(ns['parse_log']([record],False)),['book','old-work']
        check('reindex_removed_key_'+action,removed)
    check('new_document_only_top_level',lambda:(list(ns['parse_log']([{'action':'save','data':{'changeset':{'old_docs':[None],'docs':[{'key':'book','nested':{'key':'nested'}}]}}}],False)),['book']))
result={'task':task,'passed':all(c['passed'] for c in checks),'checks':checks,'scope':'actual patched AST nodes; fake imports/Qt scheduler; no complete repository or service equivalence claim'}
print('SEMANTIC_RESULT='+json.dumps(result))
