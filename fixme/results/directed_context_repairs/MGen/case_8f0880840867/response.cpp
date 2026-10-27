#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long wclk,unsigned long long wrst_n,unsigned long long wen,unsigned long long* wfull_ref,unsigned long long* walmost_full_ref,unsigned long long* mem_wen_ref,unsigned long long* mem_waddr_ref,unsigned long long rclk,unsigned long long rrst_n,unsigned long long ren,unsigned long long* rempty_ref,unsigned long long* ralmost_empty_ref,unsigned long long* mem_ren_ref,unsigned long long* mem_raddr_ref){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.wclk=wclk;model.wrst_n=wrst_n;model.wen=wen;model.rclk=rclk;model.rrst_n=rrst_n;model.ren=ren;model.eval();*wfull_ref=model.wfull_ref;*walmost_full_ref=model.walmost_full_ref;*mem_wen_ref=model.mem_wen_ref;*mem_waddr_ref=model.mem_waddr_ref;*rempty_ref=model.rempty_ref;*ralmost_empty_ref=model.ralmost_empty_ref;*mem_ren_ref=model.mem_ren_ref;*mem_raddr_ref=model.mem_raddr_ref;}
