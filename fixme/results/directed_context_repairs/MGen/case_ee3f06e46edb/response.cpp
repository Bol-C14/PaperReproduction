#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long clk,unsigned long long rst,unsigned long long enable,unsigned long long opa,unsigned long long opb,unsigned long long* ref_sign,unsigned long long* ref_mantissa_7,unsigned long long* ref_exponent_out){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.clk=clk;model.rst=rst;model.enable=enable;model.opa=opa;model.opb=opb;model.eval();*ref_sign=model.ref_sign;*ref_mantissa_7=model.ref_mantissa_7;*ref_exponent_out=model.ref_exponent_out;}
