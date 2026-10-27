#include "verilated.h"
#include <cstdio>
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};

VerilatedContext* innerp;
void unsafe_call(){static VerilatedContext inner;innerp=&inner;Verilated::threadContextp(&inner);}
void safe_call(){CallerContextGuard guard;static VerilatedContext inner;innerp=&inner;Verilated::threadContextp(&inner);}
int main(int argc,char** argv){VerilatedContext caller;bool safe=argc>1; if(safe)safe_call();else unsafe_call();
 bool restored=Verilated::threadContextp()==&caller;
 VL_FINISH_MT("finish_probe.sv",1,"");
 std::printf("restored=%d caller_finish=%d inner_finish=%d\n",restored,caller.gotFinish(),innerp->gotFinish());
 return safe ? !(restored && caller.gotFinish() && !innerp->gotFinish()) : !(!restored && !caller.gotFinish() && innerp->gotFinish());}
