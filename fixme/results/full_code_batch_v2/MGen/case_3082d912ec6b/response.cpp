#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long x,unsigned long long clk,unsigned long long reset,unsigned long long* y){static VerilatedContext context;static RefModel model(&context);model.x=x;model.clk=clk;model.reset=reset;model.eval();*y=model.y;}
