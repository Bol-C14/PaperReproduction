#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long clk,unsigned long long rst_n,unsigned long long in_m,unsigned long long* goods_ref,unsigned long long* out_m_ref){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.clk=clk;model.rst_n=rst_n;model.in_m=in_m;model.eval();*goods_ref=model.goods_ref;*out_m_ref=model.out_m_ref;}
