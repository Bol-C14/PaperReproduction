"""Independently compile Boolean gate JSON into C, exhaust every input assignment.
Does not call the Python gate evaluator or graph model.
"""
import hashlib,json,pathlib,subprocess,time
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent

def main():
    start=time.monotonic();rs=json.loads((ROOT/'manifest.json').read_text());source=['#include <stdio.h>','#include <stdint.h>'];funcs=[]
    for i,r in enumerate(rs):
        m=next(iter(json.loads((ROOT/'data'/r['sample_id']/'gate.json').read_text())['modules'].values()));lines=[f'static unsigned f{i}(unsigned state,unsigned a,unsigned b,unsigned en,unsigned rst) {{'];known={'0','1'}
        for port,p in m['ports'].items():
            if p['direction']=='input':
                for lane,bit in enumerate(p['bits']):lines.append(f'unsigned w{bit}=({port}>>{lane})&1u;');known.add(bit)
        def bit(b):return b+'u' if isinstance(b,str) else f'w{b}'
        pending=dict(m['cells'])
        while pending:
            done=[]
            for name,c in pending.items():
                connections=c['connections'];inputs={k:v[0] for k,v in connections.items() if c['port_directions'][k]=='input'}
                assert all(len(v)==1 for v in connections.values())
                if not all(x in known for x in inputs.values()):continue
                v={k:bit(x) for k,x in inputs.items()};a=v.get('A');b=v.get('B');s=v.get('S');typ=c['type'];expr={'$_NOT_':f'~({a})','$_AND_':f'({a})&({b})','$_OR_':f'({a})|({b})','$_XOR_':f'({a})^({b})','$_XNOR_':f'~(({a})^({b}))','$_MUX_':f'({s})?({b}):({a})'}[typ]
                outputs=[v[0] for k,v in connections.items() if c['port_directions'][k]=='output'];assert len(outputs)==1
                output=outputs[0];lines.append(f'unsigned w{output}=({expr})&1u;');known.add(output);done.append(name)
            assert done
            for name in done:del pending[name]
        outputs=m['ports']['next_state']['bits'];lines.append('return '+' | '.join(f'({bit(b)}<<{j})' for j,b in enumerate(outputs))+';');lines.append('}');source+=lines
        n=1<<r['bits'];ab='for(unsigned a=0;a<16;a++) for(unsigned b=0;b<16;b++)' if not r['external'] else 'for(unsigned a=0;a<1;a++) for(unsigned b=0;b<1;b++)'
        funcs.append(f'for(unsigned state=0;state<{n};state++) {ab} for(unsigned en=0;en<2;en++) for(unsigned rst=0;rst<2;rst++) putchar((unsigned char)f{i}(state,a,b,en,rst));')
    source+=['int main(void){']+funcs+['return 0;}'];path=ROOT/'native_gate_check.c';path.write_text('\n'.join(source)+'\n');binary=ROOT/'.native_gate_check';command=['gcc','-std=c99','-O0',str(path),'-o',str(binary)]
    result=subprocess.run(command,capture_output=True,text=True,check=True);(ROOT/'logs/native_compile.log').write_text(result.stdout+result.stderr)
    raw=subprocess.check_output([str(binary)],timeout=60);offset=0;checks=[]
    for r in rs:
        expected=np.load(ROOT/'data'/r['sample_id']/'reference.npy').tobytes();actual=raw[offset:offset+len(expected)];assert actual==expected,r['sample_id'];offset+=len(expected);checks.append({'sample_id':r['sample_id'],'assignments':len(expected),'output_sha256':hashlib.sha256(actual).hexdigest()})
    assert offset==len(raw);version=subprocess.check_output(['gcc','-dumpfullversion'],text=True).strip();report={'all_passed':True,'designs':len(rs),'assignments':offset,'gcc':version,'compile_command':command,'native_binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'native_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checks':checks,'wall_seconds':time.monotonic()-start,'independence':'native C gate evaluation compiled from gate JSON, compared byte-for-byte to separately computed NumPy reference; no Python evaluator or neural model used'};(ROOT/'native_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
