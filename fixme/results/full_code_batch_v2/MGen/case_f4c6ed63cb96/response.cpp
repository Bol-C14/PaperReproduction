#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long clk,unsigned long long reset,unsigned long long data_i,unsigned long long* data_o_ref){static VerilatedContext context;static RefModel model(&context);model.clk=clk;model.reset=reset;model.data_i=data_i;model.eval();*data_o_ref=model.data_o_ref;}
