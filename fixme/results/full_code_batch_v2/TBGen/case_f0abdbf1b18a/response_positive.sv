`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable;
reg selection;
reg [7:0] d_in_0;
reg [7:0] d_in_1;
wire d_o;
wire ref_d_o;
wire wr_en;
wire ref_wr_en;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
tbu dut(.clk(clk), .rst(rst), .enable(enable), .selection(selection), .d_in_0(d_in_0), .d_in_1(d_in_1), .d_o(d_o), .wr_en(wr_en));
oracle_tbu golden(.clk(clk), .rst(rst), .enable(enable), .selection(selection), .d_in_0(d_in_0), .d_in_1(d_in_1), .d_o(ref_d_o), .wr_en(ref_wr_en));
initial begin
clk = 0;
rst = 1;
enable = 0;
selection = 0;
d_in_0 = 0;
d_in_1 = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
selection = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
d_in_0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
d_in_1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_d_o,ref_wr_en}) === 1'bx || (^{d_o,wr_en}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({d_o,wr_en} !== {ref_d_o,ref_wr_en}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule