`timescale 1ns/1ps
module calibration_tb;
reg clk;
wire [15:0] a;
wire [15:0] ref_a;
wire [7:0] d;
wire [7:0] ref_d;
wire mreq;
wire ref_mreq;
wire rd;
wire ref_rd;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
z80memr dut(.clk(clk), .a(a), .d(d), .mreq(mreq), .rd(rd));
oracle_z80memr golden(.clk(clk), .a(ref_a), .d(ref_d), .mreq(ref_mreq), .rd(ref_rd));
initial begin
clk = 0;
#2;

for(i=0;i<64;i=i+1) begin

#2; clk=1; #2;
if ((^{ref_a,ref_d,ref_mreq,ref_rd}) === 1'bx || (^{a,d,mreq,rd}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({a,d,mreq,rd} !== {ref_a,ref_d,ref_mreq,ref_rd}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule