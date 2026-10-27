`timescale 1ns/1ps
module calibration_tb;
wire [29:0] mem_ex;
wire [29:0] ref_mem_ex;
wire [29:0] bpc_ex;
wire [29:0] ref_bpc_ex;
wire [31:0] alu_ex;
wire [31:0] ref_alu_ex;
wire [31:0] alu_mx;
wire [31:0] ref_alu_mx;
wire [9:0] msr_ex;
wire [9:0] ref_msr_ex;
wire [31:0] sfr_mx;
wire [31:0] ref_sfr_mx;
reg [1:0] exc_dwb;
reg exc_ill;
reg [29:0] rpc_ex;
reg [5:0] opc_of;
reg [31:0] opa_of;
reg [31:0] opb_of;
reg [31:0] opd_of;
reg [15:0] imm_of;
reg [4:0] rd_of;
reg [4:0] ra_of;
reg gclk;
reg grst;
reg dena;
reg gpha;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
aeMB2_intu dut(.mem_ex(mem_ex), .bpc_ex(bpc_ex), .alu_ex(alu_ex), .alu_mx(alu_mx), .msr_ex(msr_ex), .sfr_mx(sfr_mx), .exc_dwb(exc_dwb), .exc_ill(exc_ill), .rpc_ex(rpc_ex), .opc_of(opc_of), .opa_of(opa_of), .opb_of(opb_of), .opd_of(opd_of), .imm_of(imm_of), .rd_of(rd_of), .ra_of(ra_of), .gclk(gclk), .grst(grst), .dena(dena), .gpha(gpha));
oracle_aeMB2_intu golden(.mem_ex(ref_mem_ex), .bpc_ex(ref_bpc_ex), .alu_ex(ref_alu_ex), .alu_mx(ref_alu_mx), .msr_ex(ref_msr_ex), .sfr_mx(ref_sfr_mx), .exc_dwb(exc_dwb), .exc_ill(exc_ill), .rpc_ex(rpc_ex), .opc_of(opc_of), .opa_of(opa_of), .opb_of(opb_of), .opd_of(opd_of), .imm_of(imm_of), .rd_of(rd_of), .ra_of(ra_of), .gclk(gclk), .grst(grst), .dena(dena), .gpha(gpha));
initial begin
exc_dwb = 0;
exc_ill = 0;
rpc_ex = 0;
opc_of = 0;
opa_of = 0;
opb_of = 0;
opd_of = 0;
imm_of = 0;
rd_of = 0;
ra_of = 0;
gclk = 0;
grst = 0;
dena = 0;
gpha = 0;
#2;

for(i=0;i<64;i=i+1) begin
exc_dwb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
exc_ill = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rpc_ex = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opc_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opd_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
imm_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rd_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ra_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
grst = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
gpha = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; gclk=1; #2;
if ((^{ref_mem_ex,ref_bpc_ex,ref_alu_ex,ref_alu_mx,ref_msr_ex,ref_sfr_mx}) === 1'bx || (^{mem_ex,bpc_ex,alu_ex,alu_mx,msr_ex,sfr_mx}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({mem_ex,bpc_ex,alu_ex,alu_mx,msr_ex,sfr_mx} !== {ref_mem_ex,ref_bpc_ex,ref_alu_ex,ref_alu_mx,ref_msr_ex,ref_sfr_mx}) failures=failures+1; end
gclk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule