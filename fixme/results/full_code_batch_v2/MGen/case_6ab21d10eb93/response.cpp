#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long in0,unsigned long long in1,unsigned long long in2,unsigned long long in3,unsigned long long select,unsigned long long* out){static VerilatedContext context;static RefModel model(&context);model.in0=in0;model.in1=in1;model.in2=in2;model.in3=in3;model.select=select;model.eval();*out=model.out;}
