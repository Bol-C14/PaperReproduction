`timescale 1ns/1ps
module calibration_tb;
reg BITVAL;
reg Enable;
reg CLK;
reg RST;
wire [6:0] CRC;
wire [6:0] ref_CRC;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
CRC_7 dut(.BITVAL(BITVAL), .Enable(Enable), .CLK(CLK), .RST(RST), .CRC(CRC));
oracle_CRC_7 golden(.BITVAL(BITVAL), .Enable(Enable), .CLK(CLK), .RST(RST), .CRC(ref_CRC));
initial begin
BITVAL = 0;
Enable = 0;
CLK = 0;
RST = 1;
#2;
RST = 0;
for(i=0;i<64;i=i+1) begin
BITVAL = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; CLK=1; #2;
if ((^{ref_CRC}) === 1'bx || (^{CRC}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({CRC} !== {ref_CRC}) failures=failures+1; end
CLK=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule