#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long data1_i,unsigned long long data2_i,unsigned long long select_i){static VerilatedContext context;static RefModel model(&context);model.data1_i=data1_i;model.data2_i=data2_i;model.select_i=select_i;model.eval();}
