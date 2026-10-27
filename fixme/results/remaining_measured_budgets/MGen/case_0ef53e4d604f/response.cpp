#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long CS,unsigned long long WR,unsigned long long clk,unsigned long long cmd,unsigned long long din,unsigned long long* dout_ref,unsigned long long* mode_ref,unsigned long long CE){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.CS=CS;model.WR=WR;model.clk=clk;model.cmd=cmd;model.din=din;model.CE=CE;model.eval();*dout_ref=model.dout_ref ^ 1ULL;*mode_ref=model.mode_ref;}
