`timescale 1ns/1ps
module calibration_tb;
wire [31:0] dat_o;
wire [31:0] ref_dat_o;
reg [7:0] adr_i;
reg [31:0] dat_i;
reg wre_i;
reg ena_i;
reg rst_i;
reg clk_i;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
aeMB2_spsram dut(.dat_o(dat_o), .adr_i(adr_i), .dat_i(dat_i), .wre_i(wre_i), .ena_i(ena_i), .rst_i(rst_i), .clk_i(clk_i));
oracle_aeMB2_spsram golden(.dat_o(ref_dat_o), .adr_i(adr_i), .dat_i(dat_i), .wre_i(wre_i), .ena_i(ena_i), .rst_i(rst_i), .clk_i(clk_i));
initial begin
adr_i = 0;
dat_i = 0;
wre_i = 0;
ena_i = 0;
rst_i = 1;
clk_i = 0;
#2;
rst_i = 0;
for(i=0;i<64;i=i+1) begin
adr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wre_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ena_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_i=1; #2;
if ((^{ref_dat_o}) === 1'bx || (^{dat_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({dat_o} !== {ref_dat_o}) failures=failures+1; end
clk_i=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule