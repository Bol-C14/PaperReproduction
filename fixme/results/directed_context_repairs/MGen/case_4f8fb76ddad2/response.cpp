#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long i_clk,unsigned long long i_rst,unsigned long long i_wr,unsigned long long i_signed,unsigned long long i_numerator,unsigned long long i_denominator,unsigned long long* o_busy_ref,unsigned long long* o_valid_ref,unsigned long long* o_err_ref,unsigned long long* o_quotient_ref,unsigned long long* o_flags_ref){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.i_clk=i_clk;model.i_rst=i_rst;model.i_wr=i_wr;model.i_signed=i_signed;model.i_numerator=i_numerator;model.i_denominator=i_denominator;model.eval();*o_busy_ref=model.o_busy_ref ^ 1ULL;*o_valid_ref=model.o_valid_ref;*o_err_ref=model.o_err_ref;*o_quotient_ref=model.o_quotient_ref;*o_flags_ref=model.o_flags_ref;}
