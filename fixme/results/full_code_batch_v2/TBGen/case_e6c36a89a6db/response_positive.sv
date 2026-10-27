`timescale 1ns/1ps
module calibration_tb;
wire [1:0] dat_o;
wire [1:0] ref_dat_o;
wire [1:0] xdat_o;
wire [1:0] ref_xdat_o;
reg [1:0] dat_i;
reg [4:0] adr_i;
reg wre_i;
reg stb_i;
reg clk_i;
reg rst_i;
reg [1:0] xdat_i;
reg [4:0] xadr_i;
reg xwre_i;
reg xstb_i;
reg xclk_i;
reg xrst_i;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fasm_dparam dut(.dat_o(dat_o), .xdat_o(xdat_o), .dat_i(dat_i), .adr_i(adr_i), .wre_i(wre_i), .stb_i(stb_i), .clk_i(clk_i), .rst_i(rst_i), .xdat_i(xdat_i), .xadr_i(xadr_i), .xwre_i(xwre_i), .xstb_i(xstb_i), .xclk_i(xclk_i), .xrst_i(xrst_i));
oracle_fasm_dparam golden(.dat_o(ref_dat_o), .xdat_o(ref_xdat_o), .dat_i(dat_i), .adr_i(adr_i), .wre_i(wre_i), .stb_i(stb_i), .clk_i(clk_i), .rst_i(rst_i), .xdat_i(xdat_i), .xadr_i(xadr_i), .xwre_i(xwre_i), .xstb_i(xstb_i), .xclk_i(xclk_i), .xrst_i(xrst_i));
initial begin
dat_i = 0;
adr_i = 0;
wre_i = 0;
stb_i = 0;
clk_i = 0;
rst_i = 1;
xdat_i = 0;
xadr_i = 0;
xwre_i = 0;
xstb_i = 0;
xclk_i = 0;
xrst_i = 0;
#2;
rst_i = 0;
for(i=0;i<64;i=i+1) begin
dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
adr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wre_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
stb_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xdat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xadr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xwre_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xstb_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xclk_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xrst_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_i=1; #2;
if ((^{ref_dat_o,ref_xdat_o}) === 1'bx || (^{dat_o,xdat_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({dat_o,xdat_o} !== {ref_dat_o,ref_xdat_o}) failures=failures+1; end
clk_i=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule