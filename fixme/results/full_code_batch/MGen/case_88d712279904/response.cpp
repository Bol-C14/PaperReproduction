#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long up_down,unsigned long long clk,unsigned long long reset,unsigned long long* bin_count){static VerilatedContext context;static RefModel model(&context);model.up_down=up_down;model.clk=clk;model.reset=reset;model.eval();*bin_count=model.bin_count;}
