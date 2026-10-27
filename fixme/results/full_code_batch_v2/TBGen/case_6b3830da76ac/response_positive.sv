`timescale 1ns/1ps
module calibration_tb;
reg busack;
reg CPUCLK;
reg pin_control_oe;
reg in_halt;
reg pin_nWAIT;
reg pin_nBUSRQ;
reg pin_nINT;
reg pin_nNMI;
reg pin_nRESET;
reg nM1_out;
reg nRFSH_out;
reg nRD_out;
reg nWR_out;
reg nIORQ_out;
reg nMREQ_out;
wire nmi;
wire ref_nmi;
wire busrq;
wire ref_busrq;
wire clk;
wire ref_clk;
wire intr;
wire ref_intr;
wire mwait;
wire ref_mwait;
wire reset_in;
wire ref_reset_in;
wire pin_nM1;
wire ref_pin_nM1;
wire pin_nMREQ;
wire ref_pin_nMREQ;
wire pin_nIORQ;
wire ref_pin_nIORQ;
wire pin_nRD;
wire ref_pin_nRD;
wire pin_nWR;
wire ref_pin_nWR;
wire pin_nRFSH;
wire ref_pin_nRFSH;
wire pin_nHALT;
wire ref_pin_nHALT;
wire pin_nBUSACK;
wire ref_pin_nBUSACK;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
control_pins_n dut(.busack(busack), .CPUCLK(CPUCLK), .pin_control_oe(pin_control_oe), .in_halt(in_halt), .pin_nWAIT(pin_nWAIT), .pin_nBUSRQ(pin_nBUSRQ), .pin_nINT(pin_nINT), .pin_nNMI(pin_nNMI), .pin_nRESET(pin_nRESET), .nM1_out(nM1_out), .nRFSH_out(nRFSH_out), .nRD_out(nRD_out), .nWR_out(nWR_out), .nIORQ_out(nIORQ_out), .nMREQ_out(nMREQ_out), .nmi(nmi), .busrq(busrq), .clk(clk), .intr(intr), .mwait(mwait), .reset_in(reset_in), .pin_nM1(pin_nM1), .pin_nMREQ(pin_nMREQ), .pin_nIORQ(pin_nIORQ), .pin_nRD(pin_nRD), .pin_nWR(pin_nWR), .pin_nRFSH(pin_nRFSH), .pin_nHALT(pin_nHALT), .pin_nBUSACK(pin_nBUSACK));
oracle_control_pins_n golden(.busack(busack), .CPUCLK(CPUCLK), .pin_control_oe(pin_control_oe), .in_halt(in_halt), .pin_nWAIT(pin_nWAIT), .pin_nBUSRQ(pin_nBUSRQ), .pin_nINT(pin_nINT), .pin_nNMI(pin_nNMI), .pin_nRESET(pin_nRESET), .nM1_out(nM1_out), .nRFSH_out(nRFSH_out), .nRD_out(nRD_out), .nWR_out(nWR_out), .nIORQ_out(nIORQ_out), .nMREQ_out(nMREQ_out), .nmi(ref_nmi), .busrq(ref_busrq), .clk(ref_clk), .intr(ref_intr), .mwait(ref_mwait), .reset_in(ref_reset_in), .pin_nM1(ref_pin_nM1), .pin_nMREQ(ref_pin_nMREQ), .pin_nIORQ(ref_pin_nIORQ), .pin_nRD(ref_pin_nRD), .pin_nWR(ref_pin_nWR), .pin_nRFSH(ref_pin_nRFSH), .pin_nHALT(ref_pin_nHALT), .pin_nBUSACK(ref_pin_nBUSACK));
initial begin
busack = 0;
CPUCLK = 0;
pin_control_oe = 0;
in_halt = 0;
pin_nWAIT = 0;
pin_nBUSRQ = 0;
pin_nINT = 0;
pin_nNMI = 0;
pin_nRESET = 0;
nM1_out = 0;
nRFSH_out = 0;
nRD_out = 0;
nWR_out = 0;
nIORQ_out = 0;
nMREQ_out = 0;
#2;

for(i=0;i<64;i=i+1) begin
busack = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pin_control_oe = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in_halt = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pin_nWAIT = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pin_nBUSRQ = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pin_nINT = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pin_nNMI = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pin_nRESET = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
nM1_out = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
nRFSH_out = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
nRD_out = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
nWR_out = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
nIORQ_out = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
nMREQ_out = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; CPUCLK=1; #2;
if ((^{ref_nmi,ref_busrq,ref_clk,ref_intr,ref_mwait,ref_reset_in,ref_pin_nM1,ref_pin_nMREQ,ref_pin_nIORQ,ref_pin_nRD,ref_pin_nWR,ref_pin_nRFSH,ref_pin_nHALT,ref_pin_nBUSACK}) === 1'bx || (^{nmi,busrq,clk,intr,mwait,reset_in,pin_nM1,pin_nMREQ,pin_nIORQ,pin_nRD,pin_nWR,pin_nRFSH,pin_nHALT,pin_nBUSACK}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({nmi,busrq,clk,intr,mwait,reset_in,pin_nM1,pin_nMREQ,pin_nIORQ,pin_nRD,pin_nWR,pin_nRFSH,pin_nHALT,pin_nBUSACK} !== {ref_nmi,ref_busrq,ref_clk,ref_intr,ref_mwait,ref_reset_in,ref_pin_nM1,ref_pin_nMREQ,ref_pin_nIORQ,ref_pin_nRD,ref_pin_nWR,ref_pin_nRFSH,ref_pin_nHALT,ref_pin_nBUSACK}) failures=failures+1; end
CPUCLK=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule