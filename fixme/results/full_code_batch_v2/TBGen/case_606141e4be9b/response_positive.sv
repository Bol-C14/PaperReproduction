`timescale 1ns/1ps
module calibration_tb;
wire [1:0] rMXDST;
wire [1:0] ref_rMXDST;
wire [1:0] rMXSRC;
wire [1:0] ref_rMXSRC;
wire [1:0] rMXTGT;
wire [1:0] ref_rMXTGT;
wire [1:0] rMXALT;
wire [1:0] ref_rMXALT;
wire [2:0] rMXALU;
wire [2:0] ref_rMXALU;
wire [4:0] rRW;
wire [4:0] ref_rRW;
wire dwb_stb_o;
wire ref_dwb_stb_o;
wire dwb_wre_o;
wire ref_dwb_wre_o;
wire fsl_stb_o;
wire ref_fsl_stb_o;
wire fsl_wre_o;
wire ref_fsl_wre_o;
reg rDLY;
reg [15:0] rIMM;
reg [10:0] rALT;
reg [5:0] rOPC;
reg [4:0] rRD;
reg [4:0] rRA;
reg [4:0] rRB;
reg [29:0] rPC;
reg rBRA;
reg rMSR_IE;
reg [31:0] xIREG;
reg dwb_ack_i;
reg iwb_ack_i;
reg fsl_ack_i;
reg gclk;
reg grst;
reg gena;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
aeMB_ctrl dut(.rMXDST(rMXDST), .rMXSRC(rMXSRC), .rMXTGT(rMXTGT), .rMXALT(rMXALT), .rMXALU(rMXALU), .rRW(rRW), .dwb_stb_o(dwb_stb_o), .dwb_wre_o(dwb_wre_o), .fsl_stb_o(fsl_stb_o), .fsl_wre_o(fsl_wre_o), .rDLY(rDLY), .rIMM(rIMM), .rALT(rALT), .rOPC(rOPC), .rRD(rRD), .rRA(rRA), .rRB(rRB), .rPC(rPC), .rBRA(rBRA), .rMSR_IE(rMSR_IE), .xIREG(xIREG), .dwb_ack_i(dwb_ack_i), .iwb_ack_i(iwb_ack_i), .fsl_ack_i(fsl_ack_i), .gclk(gclk), .grst(grst), .gena(gena));
oracle_aeMB_ctrl golden(.rMXDST(ref_rMXDST), .rMXSRC(ref_rMXSRC), .rMXTGT(ref_rMXTGT), .rMXALT(ref_rMXALT), .rMXALU(ref_rMXALU), .rRW(ref_rRW), .dwb_stb_o(ref_dwb_stb_o), .dwb_wre_o(ref_dwb_wre_o), .fsl_stb_o(ref_fsl_stb_o), .fsl_wre_o(ref_fsl_wre_o), .rDLY(rDLY), .rIMM(rIMM), .rALT(rALT), .rOPC(rOPC), .rRD(rRD), .rRA(rRA), .rRB(rRB), .rPC(rPC), .rBRA(rBRA), .rMSR_IE(rMSR_IE), .xIREG(xIREG), .dwb_ack_i(dwb_ack_i), .iwb_ack_i(iwb_ack_i), .fsl_ack_i(fsl_ack_i), .gclk(gclk), .grst(grst), .gena(gena));
initial begin
rDLY = 0;
rIMM = 0;
rALT = 0;
rOPC = 0;
rRD = 0;
rRA = 0;
rRB = 0;
rPC = 0;
rBRA = 0;
rMSR_IE = 0;
xIREG = 0;
dwb_ack_i = 0;
iwb_ack_i = 0;
fsl_ack_i = 0;
gclk = 0;
grst = 0;
gena = 0;
#2;

for(i=0;i<64;i=i+1) begin
rDLY = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rIMM = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rALT = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rOPC = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rRD = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rRA = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rRB = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rPC = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rBRA = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rMSR_IE = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xIREG = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dwb_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
iwb_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
fsl_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
grst = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
gena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; gclk=1; #2;
if ((^{ref_rMXDST,ref_rMXSRC,ref_rMXTGT,ref_rMXALT,ref_rMXALU,ref_rRW,ref_dwb_stb_o,ref_dwb_wre_o,ref_fsl_stb_o,ref_fsl_wre_o}) === 1'bx || (^{rMXDST,rMXSRC,rMXTGT,rMXALT,rMXALU,rRW,dwb_stb_o,dwb_wre_o,fsl_stb_o,fsl_wre_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({rMXDST,rMXSRC,rMXTGT,rMXALT,rMXALU,rRW,dwb_stb_o,dwb_wre_o,fsl_stb_o,fsl_wre_o} !== {ref_rMXDST,ref_rMXSRC,ref_rMXTGT,ref_rMXALT,ref_rMXALU,ref_rRW,ref_dwb_stb_o,ref_dwb_wre_o,ref_fsl_stb_o,ref_fsl_wre_o}) failures=failures+1; end
gclk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule