#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long i_clk,unsigned long long i_ce,unsigned long long i_trigger,unsigned long long i_data,unsigned long long i_wb_clk,unsigned long long i_wb_cyc,unsigned long long i_wb_stb,unsigned long long i_wb_we,unsigned long long i_wb_addr,unsigned long long i_wb_data,unsigned long long* ref_o_wb_ack,unsigned long long* ref_o_wb_stall,unsigned long long* ref_o_wb_data,unsigned long long* ref_o_interrupt){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.i_clk=i_clk;model.i_ce=i_ce;model.i_trigger=i_trigger;model.i_data=i_data;model.i_wb_clk=i_wb_clk;model.i_wb_cyc=i_wb_cyc;model.i_wb_stb=i_wb_stb;model.i_wb_we=i_wb_we;model.i_wb_addr=i_wb_addr;model.i_wb_data=i_wb_data;model.eval();*ref_o_wb_ack=model.ref_o_wb_ack;*ref_o_wb_stall=model.ref_o_wb_stall;*ref_o_wb_data=model.ref_o_wb_data;*ref_o_interrupt=model.ref_o_interrupt;}
