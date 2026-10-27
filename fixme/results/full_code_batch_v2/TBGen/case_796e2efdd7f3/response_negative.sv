`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg reset;
reg S_Ready;
wire RE;
wire ref_RE;
wire WE;
wire ref_WE;
wire [7:0] RdAdd;
wire [7:0] ref_RdAdd;
wire [7:0] WrAdd;
wire [7:0] ref_WrAdd;
wire Wr_done;
wire ref_Wr_done;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
transport_in2out dut(.clk(clk), .reset(reset), .S_Ready(S_Ready), .RE(RE), .WE(WE), .RdAdd(RdAdd), .WrAdd(WrAdd), .Wr_done(Wr_done));
oracle_transport_in2out golden(.clk(clk), .reset(reset), .S_Ready(S_Ready), .RE(ref_RE), .WE(ref_WE), .RdAdd(ref_RdAdd), .WrAdd(ref_WrAdd), .Wr_done(ref_Wr_done));
initial begin
clk = 0;
reset = 1;
S_Ready = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
S_Ready = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_RE,ref_WE,ref_RdAdd,ref_WrAdd,ref_Wr_done}) === 1'bx || (^{RE,WE,RdAdd,WrAdd,Wr_done}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({RE,WE,RdAdd,WrAdd,Wr_done} !== ({ref_RE,ref_WE,ref_RdAdd,ref_WrAdd,ref_Wr_done} ^ 1'b1)) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule