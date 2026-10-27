#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long data_in,unsigned long long control,unsigned long long clk,unsigned long long reset,unsigned long long* data_out){static VerilatedContext context;static RefModel model(&context);model.data_in=data_in;model.control=control;model.clk=clk;model.reset=reset;model.eval();*data_out=model.data_out;}
