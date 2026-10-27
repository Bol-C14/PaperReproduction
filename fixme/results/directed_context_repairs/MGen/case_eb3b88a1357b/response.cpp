#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long clk,unsigned long long reset,unsigned long long write_en,unsigned long long read_en,unsigned long long data_in,unsigned long long* full,unsigned long long* empty,unsigned long long* out){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.clk=clk;model.reset=reset;model.write_en=write_en;model.read_en=read_en;model.data_in=data_in;model.eval();*full=model.full;*empty=model.empty;*out=model.out;}
