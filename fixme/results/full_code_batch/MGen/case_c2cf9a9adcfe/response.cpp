#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long i_a,unsigned long long i_b,unsigned long long i_cin,unsigned long long* o_sum,unsigned long long* o_carry){static VerilatedContext context;static RefModel model(&context);model.i_a=i_a;model.i_b=i_b;model.i_cin=i_cin;model.eval();*o_sum=model.o_sum ^ 1ULL;*o_carry=model.o_carry;}
