#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long clk,unsigned long long reset,unsigned long long* rom_addr_ref,unsigned long long rom_q,unsigned long long* ram_a_addr_ref,unsigned long long* ram_b_addr_ref,unsigned long long* ram_b_w_ref,unsigned long long* pe_ref,unsigned long long* done_ref){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.clk=clk;model.reset=reset;model.rom_q=rom_q;model.eval();*rom_addr_ref=model.rom_addr_ref;*ram_a_addr_ref=model.ram_a_addr_ref;*ram_b_addr_ref=model.ram_b_addr_ref;*ram_b_w_ref=model.ram_b_w_ref;*pe_ref=model.pe_ref;*done_ref=model.done_ref;}
