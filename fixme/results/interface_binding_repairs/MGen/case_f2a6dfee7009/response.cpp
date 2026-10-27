#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long clk_i,unsigned long long DataOrReg,unsigned long long address,unsigned long long instr_i,unsigned long long reset,unsigned long long vout_addr,unsigned long long* value_o_ref,unsigned long long* is_positive_ref){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.clk_i=clk_i;model.DataOrReg=DataOrReg;model.address=address;model.instr_i=instr_i;model.reset=reset;model.vout_addr=vout_addr;model.eval();*value_o_ref=model.value_o_ref;*is_positive_ref=model.is_positive_ref;}
