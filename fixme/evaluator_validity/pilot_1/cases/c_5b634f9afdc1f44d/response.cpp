#include "RefModel.h"
#include <memory>
#include <cstdio>
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
struct ReferenceOwner { std::unique_ptr<VerilatedContext> context;std::unique_ptr<RefModel> model;ReferenceOwner():context(new VerilatedContext),model(new RefModel(context.get())){} };
static std::unique_ptr<ReferenceOwner> owner;static unsigned long long validity_calls=0,validity_changes=0;
extern "C" void ref_model_release(){CallerContextGuard guard;if(owner){Verilated::threadContextp(owner->context.get());owner->model->final();owner->model.reset();owner->context.reset();owner.reset();}std::printf("VALIDITY_COUNTS calls=%llu changes=%llu\n",validity_calls,validity_changes);}
extern "C" void ref_model_eval(unsigned long long clk_i,unsigned long long DataOrReg,unsigned long long address,unsigned long long instr_i,unsigned long long reset,unsigned long long vout_addr,unsigned long long* value_o_ref,unsigned long long* is_positive_ref,unsigned long long* easter_egg_ref){CallerContextGuard guard;if(!owner)owner.reset(new ReferenceOwner);Verilated::threadContextp(owner->context.get());RefModel& model=*owner->model;model.clk_i=clk_i;model.DataOrReg=DataOrReg;model.address=address;model.instr_i=instr_i;model.reset=reset;model.vout_addr=vout_addr;model.eval();++validity_calls;{unsigned long long before=model.value_o_ref;unsigned long long after=(before) & 255ULL;if(before!=after)++validity_changes;*value_o_ref=after;}*is_positive_ref=model.is_positive_ref;*easter_egg_ref=model.easter_egg_ref;}
