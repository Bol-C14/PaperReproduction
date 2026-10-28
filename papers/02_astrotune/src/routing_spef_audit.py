from routing_round import attempt,BASE
for p,idx,seed in [(9,9,1),(0,10,0),(9,11,0)]:
 paths=list(BASE.glob(f'{idx:02d}_*/routed.odb'));assert len(paths)==1
 attempt('adder_32bit',0,p,'spef_audit',paths[0],seed=seed,timeout_s=2)
