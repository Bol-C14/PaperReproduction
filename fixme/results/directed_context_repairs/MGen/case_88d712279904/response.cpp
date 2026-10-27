#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long up_down,unsigned long long clk,unsigned long long reset,unsigned long long* bin_count){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.up_down=up_down;model.clk=clk;model.reset=reset;model.eval();*bin_count=model.bin_count;}
