#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long in,unsigned long long clk,unsigned long long reset,unsigned long long* out){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.in=in;model.clk=clk;model.reset=reset;model.eval();*out=model.out;}
