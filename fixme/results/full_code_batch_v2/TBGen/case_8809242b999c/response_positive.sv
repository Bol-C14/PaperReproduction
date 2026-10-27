`timescale 1ns/1ps
module calibration_tb;
reg clk;
wire [15:0] a;
wire [15:0] ref_a;
wire [7:0] d;
wire [7:0] ref_d;
wire mreq_n;
wire ref_mreq_n;
wire iorq_n;
wire ref_iorq_n;
wire wr_n;
wire ref_wr_n;
wire rfsh_n;
wire ref_rfsh_n;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
z80memio dut(.clk(clk), .a(a), .d(d), .mreq_n(mreq_n), .iorq_n(iorq_n), .wr_n(wr_n), .rfsh_n(rfsh_n));
oracle_z80memio golden(.clk(clk), .a(ref_a), .d(ref_d), .mreq_n(ref_mreq_n), .iorq_n(ref_iorq_n), .wr_n(ref_wr_n), .rfsh_n(ref_rfsh_n));
initial begin
clk = 0;
#2;

for(i=0;i<64;i=i+1) begin

#2; clk=1; #2;
if ((^{ref_a,ref_d,ref_mreq_n,ref_iorq_n,ref_wr_n,ref_rfsh_n}) === 1'bx || (^{a,d,mreq_n,iorq_n,wr_n,rfsh_n}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({a,d,mreq_n,iorq_n,wr_n,rfsh_n} !== {ref_a,ref_d,ref_mreq_n,ref_iorq_n,ref_wr_n,ref_rfsh_n}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule