#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long i_d,unsigned long long clk,unsigned long long reset,unsigned long long* o_q,unsigned long long* o_qb){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.i_d=i_d;model.clk=clk;model.reset=reset;model.eval();*o_q=model.o_q ^ 1ULL;*o_qb=model.o_qb;}
