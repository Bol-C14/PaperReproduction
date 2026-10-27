`timescale 1ns/1ps
module calibration_tb;
wire mux_drive_disable;
wire ref_mux_drive_disable;
wire mem_write_disable;
wire ref_mem_write_disable;
wire sehold;
wire ref_sehold;
wire se;
wire ref_se;
wire testmode_l;
wire ref_testmode_l;
wire mem_bypass;
wire ref_mem_bypass;
wire so_0;
wire ref_so_0;
wire so_1;
wire ref_so_1;
wire so_2;
wire ref_so_2;
reg ctu_tst_pre_grst_l;
reg arst_l;
reg global_shift_enable;
reg ctu_tst_scan_disable;
reg ctu_tst_scanmode;
reg ctu_tst_macrotest;
reg ctu_tst_short_chain;
reg long_chain_so_0;
reg short_chain_so_0;
reg long_chain_so_1;
reg short_chain_so_1;
reg long_chain_so_2;
reg short_chain_so_2;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
test_stub_scan dut(.mux_drive_disable(mux_drive_disable), .mem_write_disable(mem_write_disable), .sehold(sehold), .se(se), .testmode_l(testmode_l), .mem_bypass(mem_bypass), .so_0(so_0), .so_1(so_1), .so_2(so_2), .ctu_tst_pre_grst_l(ctu_tst_pre_grst_l), .arst_l(arst_l), .global_shift_enable(global_shift_enable), .ctu_tst_scan_disable(ctu_tst_scan_disable), .ctu_tst_scanmode(ctu_tst_scanmode), .ctu_tst_macrotest(ctu_tst_macrotest), .ctu_tst_short_chain(ctu_tst_short_chain), .long_chain_so_0(long_chain_so_0), .short_chain_so_0(short_chain_so_0), .long_chain_so_1(long_chain_so_1), .short_chain_so_1(short_chain_so_1), .long_chain_so_2(long_chain_so_2), .short_chain_so_2(short_chain_so_2));
oracle_test_stub_scan golden(.mux_drive_disable(ref_mux_drive_disable), .mem_write_disable(ref_mem_write_disable), .sehold(ref_sehold), .se(ref_se), .testmode_l(ref_testmode_l), .mem_bypass(ref_mem_bypass), .so_0(ref_so_0), .so_1(ref_so_1), .so_2(ref_so_2), .ctu_tst_pre_grst_l(ctu_tst_pre_grst_l), .arst_l(arst_l), .global_shift_enable(global_shift_enable), .ctu_tst_scan_disable(ctu_tst_scan_disable), .ctu_tst_scanmode(ctu_tst_scanmode), .ctu_tst_macrotest(ctu_tst_macrotest), .ctu_tst_short_chain(ctu_tst_short_chain), .long_chain_so_0(long_chain_so_0), .short_chain_so_0(short_chain_so_0), .long_chain_so_1(long_chain_so_1), .short_chain_so_1(short_chain_so_1), .long_chain_so_2(long_chain_so_2), .short_chain_so_2(short_chain_so_2));
initial begin
ctu_tst_pre_grst_l = 0;
arst_l = 0;
global_shift_enable = 0;
ctu_tst_scan_disable = 0;
ctu_tst_scanmode = 0;
ctu_tst_macrotest = 0;
ctu_tst_short_chain = 0;
long_chain_so_0 = 0;
short_chain_so_0 = 0;
long_chain_so_1 = 0;
short_chain_so_1 = 0;
long_chain_so_2 = 0;
short_chain_so_2 = 0;
#2;

for(i=0;i<64;i=i+1) begin
ctu_tst_pre_grst_l = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
arst_l = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
global_shift_enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ctu_tst_scan_disable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ctu_tst_scanmode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ctu_tst_macrotest = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ctu_tst_short_chain = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
long_chain_so_0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
short_chain_so_0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
long_chain_so_1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
short_chain_so_1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
long_chain_so_2 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
short_chain_so_2 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_mux_drive_disable,ref_mem_write_disable,ref_sehold,ref_se,ref_testmode_l,ref_mem_bypass,ref_so_0,ref_so_1,ref_so_2}) === 1'bx || (^{mux_drive_disable,mem_write_disable,sehold,se,testmode_l,mem_bypass,so_0,so_1,so_2}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({mux_drive_disable,mem_write_disable,sehold,se,testmode_l,mem_bypass,so_0,so_1,so_2} !== {ref_mux_drive_disable,ref_mem_write_disable,ref_sehold,ref_se,ref_testmode_l,ref_mem_bypass,ref_so_0,ref_so_1,ref_so_2}) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule