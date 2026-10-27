"""Equations 8-10. Constants are local assumptions, never inferred paper values."""
def logic(area,power,slack,ref,period=2.):
    r=max(0,-slack-.05*period)/max(ref['slack'],.1*period)
    return .5*area/ref['area']+.5*power/ref['power']+.1*min(r,1.)+max(r-1.,0)

def layout(area,power,slack,ref):
    return 100.+abs(slack) if slack<0 else .5*area/ref['area']+.5*power/ref['power']
