#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long reset,unsigned long long clk,unsigned long long* data_out){static VerilatedContext context;static RefModel model(&context);model.reset=reset;model.clk=clk;model.eval();*data_out=model.data_out;}
