"""Narrow exhaustive checker for the observed pure-LUT rewrite, not general EC."""
import hashlib,itertools,json,pathlib,re
P=pathlib.Path(__file__).resolve().parents[1]
def canonical(s):
    return '\n'.join(x for x in s.splitlines() if not x.startswith(('// Date        :','// Command     :')))
pat=re.compile(r"  LUT([1-6]) #\(\s*\.INIT\((\d+)'h([0-9A-Fa-f]+)\)\)\s*([^\n]+)\n       \((.*?)\);\n",re.S)
def parse(s):
    records={}
    for m in pat.finditer(s):
        n=int(m[1]);assert int(m[2])==2**n
        name=m[4].strip();ports=dict(re.findall(r'\.([IO][0-5]?)\(([^()]*)\)',m[5]))
        assert set(ports)=={'O'}|{'I'+str(i) for i in range(n)}
        assert name not in records, 'duplicate instance name; narrow parser is insufficient'
        records[name]={'n':n,'init':int(m[3],16),'ports':{k:v.strip() for k,v in ports.items()},'text':m[0]}
    return records
old=canonical((P/'logs/contract/original_funcsim.v').read_text())+'\n'
new=canonical((P/'logs/default_1/funcsim.v').read_text())+'\n'
a,b=parse(old),parse(new)
removed=set(a)-set(b);added=set(b)-set(a)
assert removed=={'RegFilePlugin_regFile_reg_r1_0_31_14_27_i_6'}
assert added=={'RegFilePlugin_regFile_reg_r1_0_31_14_27_i_6_comp',r'\HazardSimplePlugin_writeBackBuffer_payload_data[18]_i_1_comp'}
assert all(a[k]==b[k] for k in set(a)&set(b)), 'other LUT modifications require review'
# Exact remainder equality accounts for all non-LUT logic/configuration/initial state.
ra=old
for k in removed:ra=ra.replace(a[k]['text'],'',1)
rb=new
for k in added:
    marked='  (* PHYS_OPT_MODIFIED = "RESTRUCT_OPT" *) \n'+b[k]['text']
    assert rb.count(marked)==1
    rb=rb.replace(marked,'',1)
extra_wire='  wire \\HazardSimplePlugin_writeBackWrites_payload_data[18]_repN ;\n'
assert rb.count(extra_wire)==1
rb=rb.replace(extra_wire,'',1)
assert ra==rb, 'non-LUT, attribute, or wiring changes outside declared slice'
output='lastStageRegFileWrite_payload_data[16]'
# Cut at every input to unchanged LUTs: only expand the existing producer
# needed by the removed LUT and the two introduced LUTs.
old_gate=a[next(iter(removed))]
producer_signal=old_gate['ports']['I0']
producers=[k for k,r in a.items() if r['ports']['O']==producer_signal]
assert len(producers)==1
old_slice={k:a[k] for k in removed|set(producers)}
new_slice={k:b[k] for k in added}
def drivers(records):
    d={r['ports']['O']:r for r in records.values()}
    assert len(d)==len(records)
    return d
ad,bd=drivers(old_slice),drivers(new_slice)
def leaves(d,signal,stack=()):
    assert signal not in stack,'cycle'
    if signal not in d:return {signal}
    r=d[signal]
    return set().union(*(leaves(d,r['ports']['I'+str(i)],stack+(signal,)) for i in range(r['n'])))
inputs=sorted(leaves(ad,output)|leaves(bd,output))
assert len(inputs)<=12, 'outside bounded exhaustive checker'
def ev(d,signal,values):
    if signal not in d:return values[signal]
    r=d[signal]
    index=sum(ev(d,r['ports']['I'+str(i)],values)<<i for i in range(r['n']))
    return (r['init']>>index)&1
mismatches=[]
for bits in itertools.product((0,1),repeat=len(inputs)):
    values=dict(zip(inputs,bits))
    if ev(ad,output,values)!=ev(bd,output,values):mismatches.append(values)
assert not mismatches, mismatches[:1]
# This assumes ordinary two-state Boolean LUT semantics; INIT/edge state and
# all remaining sequential logic are preserved by exact remainder equality.
result={'scope':'this_actual_LUT_slice_only_two_state_Boolean_semantics','inputs':inputs,'output':output,'assignments_exhausted':2**len(inputs),'mismatches':len(mismatches),'exact_remainder_equal':ra==rb,'removed_instances':sorted(removed),'added_instances':sorted(added),'conditional_result':'local_rewrite_preserves_Boolean_function_given_Vivado_export_semantics','not_proved':['four_state_XZ_equivalence','timing_behavior','exporter_correctness','full_original_specification'],'input_exports_sha256':[hashlib.sha256(x.encode()).hexdigest() for x in (old,new)]}
(P/'DEFAULT_SLICE_PROOF.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
