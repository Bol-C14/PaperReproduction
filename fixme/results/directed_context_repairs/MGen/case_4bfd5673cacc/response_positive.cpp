#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long i_a,unsigned long long clk,unsigned long long reset,unsigned long long* no_ones){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.i_a=i_a;model.clk=clk;model.reset=reset;model.eval();*no_ones=model.no_ones;}
