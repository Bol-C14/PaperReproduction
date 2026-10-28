"""Independent public-formula arithmetic; NOT the private FluxBench evaluator.

Inputs here are measurements, not proof of artifact validity. No Token ROI guessed.
"""
import math

REF = {350: (23746.27, 2.49435), 700: (34291.88, 6.92488)}
FLOORS = dict(setupWns=-.8, setupTns=-200., holdWns=-.3, holdTns=-80.)

def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)

def small(x, best):
    return min(100., 100. * best / x) if finite(x) and x > 0 else 0.

def timing(x, floor):
    return max(0., min(100., 100. * (x-floor)/-floor)) if finite(x) else 0.

def gates(logic, physical, eco):
    """Explicit synthetic gate contract: 2 synthesis, 4 PR checks, binary ECO.

    Check weighting is a reconstruction consistent with reported partial scores,
    not verified official code. Later stages count only after prior full gates.
    """
    assert len(logic)==2 and len(physical)==4
    assert all(type(x) is bool for x in [*logic,*physical,eco])
    l = 100 * sum(logic)/2
    p = 100 * sum(physical)/4 if all(logic) else 0
    e = 100 if all(logic) and all(physical) and eco else 0
    return (l+p+e)/3

def score(stage, metrics, frequency):
    if frequency not in REF or not finite(stage) or not 0 <= stage <= 100:
        raise ValueError('unknown frequency or invalid stage')
    a,p = REF[frequency]
    components = dict(area=small(metrics.get('area'), a), power=small(metrics.get('power'),p))
    components.update({k:timing(metrics.get(k),v) for k,v in FLOORS.items()})
    result = sum(components.values())/6 if abs(stage-100)<1e-8 else 0.
    return dict(score=.2*stage+.8*result, stage=stage, result=result, components=components)

def evidence_gate(bundle, current_design, current_constraints):
    """Local proposed freshness/terminal guard; no claim about upstream behavior."""
    required = {'netlist','layout','gds','timing','qor'}
    if set(bundle.get('artifacts',{})) != required:
        return False
    for item in bundle['artifacts'].values():
        if item.get('design_sha256') != current_design or item.get('constraints_sha256') != current_constraints:
            return False
        if item.get('validator') != 'independent-parser' or item.get('valid') is not True:
            return False
    return True
