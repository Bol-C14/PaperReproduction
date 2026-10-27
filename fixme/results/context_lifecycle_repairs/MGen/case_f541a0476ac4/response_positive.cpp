#include "RefModel.h"
#include <memory>
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
struct ReferenceOwner {
 std::unique_ptr<VerilatedContext> context;
 std::unique_ptr<RefModel> model;
 ReferenceOwner():context(new VerilatedContext),model(new RefModel(context.get())){}
};
static std::unique_ptr<ReferenceOwner> reference_owner;
extern "C" void ref_model_release(){CallerContextGuard restore_caller;if(reference_owner){Verilated::threadContextp(reference_owner->context.get());reference_owner->model->final();reference_owner->model.reset();reference_owner->context.reset();reference_owner.reset();}}
extern "C" void ref_model_eval(unsigned long long i_d,unsigned long long clk,unsigned long long reset,unsigned long long* o_q,unsigned long long* o_qb){CallerContextGuard restore_caller;if(!reference_owner)reference_owner.reset(new ReferenceOwner);Verilated::threadContextp(reference_owner->context.get());RefModel& model=*reference_owner->model;model.i_d=i_d;model.clk=clk;model.reset=reset;model.eval();*o_q=model.o_q;*o_qb=model.o_qb;}
