#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long data_in,unsigned long long load,unsigned long long shift_en,unsigned long long clk,unsigned long long reset,unsigned long long* data_out){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.data_in=data_in;model.load=load;model.shift_en=shift_en;model.clk=clk;model.reset=reset;model.eval();*data_out=model.data_out;}
