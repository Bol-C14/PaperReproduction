from routing_round import attempt,BASE
from eda import ROOT
# Three actual executions; shared p9/seed0 serves both paired policies.
a=attempt('adder_32bit',0,9,'detail_extract',BASE/'07_adder_32bit_s0_p9_global/routed.odb',seed=1,timeout_s=10)
b=attempt('adder_32bit',0,0,'detail_extract',BASE/'03_adder_32bit_s0_p0_global/routed.odb',seed=0,timeout_s=10)
c=attempt('adder_32bit',0,9,'detail_extract',BASE/'07_adder_32bit_s0_p9_global/routed.odb',seed=0,timeout_s=10)
