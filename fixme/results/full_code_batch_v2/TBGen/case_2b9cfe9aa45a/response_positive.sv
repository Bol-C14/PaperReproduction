`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg clr;
reg [7:0] din;
reg we;
wire [7:0] dout;
wire [7:0] ref_dout;
reg re;
wire full;
wire ref_full;
wire empty;
wire ref_empty;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fifo4 dut(.clk(clk), .rst(rst), .clr(clr), .din(din), .we(we), .dout(dout), .re(re), .full(full), .empty(empty));
oracle_fifo4 golden(.clk(clk), .rst(rst), .clr(clr), .din(din), .we(we), .dout(ref_dout), .re(re), .full(ref_full), .empty(ref_empty));
initial begin
clk = 0;
rst = 1;
clr = 0;
din = 0;
we = 0;
re = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
clr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
din = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
we = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
re = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_dout,ref_full,ref_empty}) === 1'bx || (^{dout,full,empty}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({dout,full,empty} !== {ref_dout,ref_full,ref_empty}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule