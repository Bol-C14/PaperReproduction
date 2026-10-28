#!/usr/bin/env python3
"""Independent stdlib NLDM/load/path sanity check using existing logs only."""
import bisect,json,math,re
from pathlib import Path
from pilot import ROOT,blocks,library,flatten,fixture


def interpolate(body,x,y):
    def axis(k):return [float(v) for v in re.search(k+r'\s*\("([^"]+)"\)',body).group(1).split(',')]
    xs,ys=axis('index_1'),axis('index_2')
    rows=re.findall(r'"([\d.,eE+ -]+)"',body[body.index('values'):])
    table=[[float(v) for v in row.split(',')] for row in rows]
    assert len(table)==len(xs) and all(len(row)==len(ys) for row in table)
    i=max(1,min(bisect.bisect_left(xs,x),len(xs)-1));j=max(1,min(bisect.bisect_left(ys,y),len(ys)-1))
    tx=(x-xs[i-1])/(xs[i]-xs[i-1]);ty=(y-ys[j-1])/(ys[j]-ys[j-1])
    v=(1-tx)*(1-ty)*table[i-1][j-1]+tx*(1-ty)*table[i][j-1]+(1-tx)*ty*table[i-1][j]+tx*ty*table[i][j]
    return v,{'slew_grid_ps':[xs[0],xs[-1]],'load_grid_ff':[ys[0],ys[-1]],'input_slew_in_grid':xs[0]<=x<=xs[-1],'load_in_grid':ys[0]<=y<=ys[-1]}


def main():
    text,lib=library();cells=dict(blocks(text,'cell'));rows=[]
    assert 'time_unit : "1ps"' in text and 'capacitive_load_unit (1,ff)' in text and 'pulling_resistance_unit : "1kohm"' in text
    for name in ['clustered','spread','aes_cut']:
        f=fixture(name);out=ROOT/'runs'/'feasibility'/name/'shallow_x8_10pct'
        nodes=flatten(json.loads((out/'decoded_tree.json').read_text()))
        obs=json.loads((out/'observations.json').read_text());values={(o['kind'],o['pin'],o['transition']):o['value'] for o in obs}
        spef=(out/'tree.spef').read_text();assert '*T_UNIT 1 PS' in spef and '*C_UNIT 1 FF' in spef and '*R_UNIT 1 OHM' in spef
        for n in nodes:
            children=n.get('children',[])
            cap=sum(lib[ch['cell']]['cap']+f['c_ff_per_um']*(abs(n['x']-ch['x'])+abs(n['y']-ch['y'])) for ch in children) if children else f['output_load_ff']
            pin=dict(blocks(cells[n['cell']],'pin'))['Y']
            for tr in ['rise','fall']:
                # Match actual rise/fall pin loads; scalar capacitance is the conservative maximum.
                if children:
                    cap=0.0
                    for ch in children:
                        cp=dict(blocks(cells[ch['cell']],'pin'))['A']
                        pincap=float(re.search(tr+r'_capacitance\s*:\s*([\d.]+)',cp).group(1))
                        cap+=pincap+f['c_ff_per_um']*(abs(n['x']-ch['x'])+abs(n['y']-ch['y']))
                table=next(blocks(pin,'cell_'+tr))[1]
                slew=values['input_slew',n['id']+':A',tr]
                predicted,grid=interpolate(table,slew,cap)
                measured=values['cell_output_arrival',n['id']+':Y',tr]-values['input_arrival',n['id']+':A',tr]
                residual=abs(predicted-measured)
                assert residual<.003,(name,n['id'],tr,predicted,measured)
                rows.append({'net':name,'node':n['id'],'cell':n['cell'],'transition':tr,'input_slew_ps':slew,'total_output_load_ff':cap,'independent_nldm_delay_ps':predicted,'observed_cell_arc_ps':measured,'absolute_residual_ps':residual,**grid})
    result={'actual_sta_calls_added':0,'library_time_seconds':1e-12,'library_cap_farads':1e-15,'library_resistance_ohms':1000,'spef_resistance_ohms':1,'resistance_conversion_factor':.001,'reason':'OpenTimer unit.cpp uses SPEF/library ratio before timing; log wording alone is not the conversion direction.','cell_arcs_checked':len(rows),'max_arc_residual_ps':max(r['absolute_residual_ps'] for r in rows),'load_extrapolated_arc_count':sum(not r['load_in_grid'] for r in rows),'local_terminal_load_ff':.5,'terminal_min_characterized_load_ff':1.44,'classification':'No unit/path mismatch detected. Local .5fF endpoint loads are below the BUF x2 NLDM1.44fF grid minimum; extrapolated tool evaluation is not a characterized-domain result.','rows':rows}
    (ROOT/'metrics'/'units_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
