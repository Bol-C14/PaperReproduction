#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long clk,unsigned long long reset,unsigned long long pc,unsigned long long prev_pc,unsigned long long prev_branch_in,unsigned long long prev_taken,unsigned long long* cur_pred_ref){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.clk=clk;model.reset=reset;model.pc=pc;model.prev_pc=prev_pc;model.prev_branch_in=prev_branch_in;model.prev_taken=prev_taken;model.eval();*cur_pred_ref=model.cur_pred_ref ^ 1ULL;}
