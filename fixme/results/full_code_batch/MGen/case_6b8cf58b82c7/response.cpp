#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long in,unsigned long long clk,unsigned long long reset,unsigned long long* out){static VerilatedContext context;static RefModel model(&context);model.in=in;model.clk=clk;model.reset=reset;model.eval();*out=model.out;}
