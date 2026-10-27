`timescale 1ns/1ps
module calibration_tb;
wire [15:0] rIMM;
wire [15:0] ref_rIMM;
wire [4:0] rRA;
wire [4:0] ref_rRA;
wire [4:0] rRD;
wire [4:0] ref_rRD;
wire [4:0] rRB;
wire [4:0] ref_rRB;
wire [10:0] rALT;
wire [10:0] ref_rALT;
wire [5:0] rOPC;
wire [5:0] ref_rOPC;
wire [31:0] rSIMM;
wire [31:0] ref_rSIMM;
wire [31:0] xIREG;
wire [31:0] ref_xIREG;
wire rSTALL;
wire ref_rSTALL;
wire iwb_stb_o;
wire ref_iwb_stb_o;
reg rBRA;
reg rMSR_IE;
reg rMSR_BIP;
reg [31:0] iwb_dat_i;
reg iwb_ack_i;
reg sys_int_i;
reg gclk;
reg grst;
reg gena;
reg oena;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
aeMB_ibuf dut(.rIMM(rIMM), .rRA(rRA), .rRD(rRD), .rRB(rRB), .rALT(rALT), .rOPC(rOPC), .rSIMM(rSIMM), .xIREG(xIREG), .rSTALL(rSTALL), .iwb_stb_o(iwb_stb_o), .rBRA(rBRA), .rMSR_IE(rMSR_IE), .rMSR_BIP(rMSR_BIP), .iwb_dat_i(iwb_dat_i), .iwb_ack_i(iwb_ack_i), .sys_int_i(sys_int_i), .gclk(gclk), .grst(grst), .gena(gena), .oena(oena));
oracle_aeMB_ibuf golden(.rIMM(ref_rIMM), .rRA(ref_rRA), .rRD(ref_rRD), .rRB(ref_rRB), .rALT(ref_rALT), .rOPC(ref_rOPC), .rSIMM(ref_rSIMM), .xIREG(ref_xIREG), .rSTALL(ref_rSTALL), .iwb_stb_o(ref_iwb_stb_o), .rBRA(rBRA), .rMSR_IE(rMSR_IE), .rMSR_BIP(rMSR_BIP), .iwb_dat_i(iwb_dat_i), .iwb_ack_i(iwb_ack_i), .sys_int_i(sys_int_i), .gclk(gclk), .grst(grst), .gena(gena), .oena(oena));
initial begin
rBRA = 0;
rMSR_IE = 0;
rMSR_BIP = 0;
iwb_dat_i = 0;
iwb_ack_i = 0;
sys_int_i = 0;
gclk = 0;
grst = 0;
gena = 0;
oena = 0;
#2;

for(i=0;i<64;i=i+1) begin
rBRA = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rMSR_IE = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rMSR_BIP = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
iwb_dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
iwb_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
sys_int_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
grst = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
gena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
oena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; gclk=1; #2;
if ((^{ref_rIMM,ref_rRA,ref_rRD,ref_rRB,ref_rALT,ref_rOPC,ref_rSIMM,ref_xIREG,ref_rSTALL,ref_iwb_stb_o}) === 1'bx || (^{rIMM,rRA,rRD,rRB,rALT,rOPC,rSIMM,xIREG,rSTALL,iwb_stb_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({rIMM,rRA,rRD,rRB,rALT,rOPC,rSIMM,xIREG,rSTALL,iwb_stb_o} !== {ref_rIMM,ref_rRA,ref_rRD,ref_rRB,ref_rALT,ref_rOPC,ref_rSIMM,ref_xIREG,ref_rSTALL,ref_iwb_stb_o}) failures=failures+1; end
gclk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule