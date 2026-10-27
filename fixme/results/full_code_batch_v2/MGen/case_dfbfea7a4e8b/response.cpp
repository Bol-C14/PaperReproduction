#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long* e_ref,unsigned long long q){static VerilatedContext context;static RefModel model(&context);model.q=q;model.eval();*e_ref=model.e_ref ^ 1ULL;}
