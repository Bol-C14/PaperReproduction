`timescale 1ns/1ps
module calibration_tb;
reg Data;
reg EnableCrc;
reg Reset;
reg SyncResetCrc;
wire [7:0] CrcOut;
wire [7:0] ref_CrcOut;
reg Clk;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
dbg_crc8_d1 dut(.Data(Data), .EnableCrc(EnableCrc), .Reset(Reset), .SyncResetCrc(SyncResetCrc), .CrcOut(CrcOut), .Clk(Clk));
oracle_dbg_crc8_d1 golden(.Data(Data), .EnableCrc(EnableCrc), .Reset(Reset), .SyncResetCrc(SyncResetCrc), .CrcOut(ref_CrcOut), .Clk(Clk));
initial begin
Data = 0;
EnableCrc = 0;
Reset = 1;
SyncResetCrc = 0;
Clk = 0;
#2;
Reset = 0;
for(i=0;i<64;i=i+1) begin
Data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
EnableCrc = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
SyncResetCrc = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_CrcOut}) === 1'bx || (^{CrcOut}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({CrcOut} !== {ref_CrcOut}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule