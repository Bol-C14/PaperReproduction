#include "RefModel.h"
extern "C" void ref_model_eval(unsigned long long binary,unsigned long long* gray){static VerilatedContext context;static RefModel model(&context);model.binary=binary;model.eval();*gray=model.gray;}
