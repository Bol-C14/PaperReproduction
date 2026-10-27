#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long i_clk,unsigned long long i_wb_cyc,unsigned long long i_wb_stb,unsigned long long i_wb_we,unsigned long long i_wb_addr,unsigned long long i_wb_data,unsigned long long* ref_o_data,unsigned long long* ref_o_interrupt,unsigned long long* ref_o_ppd){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.i_clk=i_clk;model.i_wb_cyc=i_wb_cyc;model.i_wb_stb=i_wb_stb;model.i_wb_we=i_wb_we;model.i_wb_addr=i_wb_addr;model.i_wb_data=i_wb_data;model.eval();*ref_o_data=model.ref_o_data ^ 1ULL;*ref_o_interrupt=model.ref_o_interrupt;*ref_o_ppd=model.ref_o_ppd;}
