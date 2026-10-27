#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long i_a,unsigned long long clk,unsigned long long reset,unsigned long long* no_ones){static VerilatedContext context;static RefModel model(&context);model.i_a=i_a;model.clk=clk;model.reset=reset;model.eval();*no_ones=model.no_ones;}
