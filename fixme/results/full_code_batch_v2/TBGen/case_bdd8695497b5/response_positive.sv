`timescale 1ns/1ps
module calibration_tb;
wire [29:0] dwb_adr_o;
wire [29:0] ref_dwb_adr_o;
wire [3:0] dwb_sel_o;
wire [3:0] ref_dwb_sel_o;
wire dwb_stb_o;
wire ref_dwb_stb_o;
wire dwb_cyc_o;
wire ref_dwb_cyc_o;
wire dwb_tag_o;
wire ref_dwb_tag_o;
wire dwb_wre_o;
wire ref_dwb_wre_o;
wire [31:0] dwb_dat_o;
wire [31:0] ref_dwb_dat_o;
wire dwb_fb;
wire ref_dwb_fb;
wire [3:0] sel_mx;
wire [3:0] ref_sel_mx;
wire [31:0] dwb_mx;
wire [31:0] ref_dwb_mx;
wire [1:0] exc_dwb;
wire [1:0] ref_exc_dwb;
reg [31:0] dwb_dat_i;
reg dwb_ack_i;
reg [15:0] imm_of;
reg [31:0] opd_of;
reg [5:0] opc_of;
reg [1:0] opa_of;
reg [1:0] opb_of;
reg [7:0] msr_ex;
reg [29:0] mem_ex;
reg [2:0] sfr_mx;
reg gclk;
reg grst;
reg dena;
reg gpha;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
aeMB2_dwbif dut(.dwb_adr_o(dwb_adr_o), .dwb_sel_o(dwb_sel_o), .dwb_stb_o(dwb_stb_o), .dwb_cyc_o(dwb_cyc_o), .dwb_tag_o(dwb_tag_o), .dwb_wre_o(dwb_wre_o), .dwb_dat_o(dwb_dat_o), .dwb_fb(dwb_fb), .sel_mx(sel_mx), .dwb_mx(dwb_mx), .exc_dwb(exc_dwb), .dwb_dat_i(dwb_dat_i), .dwb_ack_i(dwb_ack_i), .imm_of(imm_of), .opd_of(opd_of), .opc_of(opc_of), .opa_of(opa_of), .opb_of(opb_of), .msr_ex(msr_ex), .mem_ex(mem_ex), .sfr_mx(sfr_mx), .gclk(gclk), .grst(grst), .dena(dena), .gpha(gpha));
oracle_aeMB2_dwbif golden(.dwb_adr_o(ref_dwb_adr_o), .dwb_sel_o(ref_dwb_sel_o), .dwb_stb_o(ref_dwb_stb_o), .dwb_cyc_o(ref_dwb_cyc_o), .dwb_tag_o(ref_dwb_tag_o), .dwb_wre_o(ref_dwb_wre_o), .dwb_dat_o(ref_dwb_dat_o), .dwb_fb(ref_dwb_fb), .sel_mx(ref_sel_mx), .dwb_mx(ref_dwb_mx), .exc_dwb(ref_exc_dwb), .dwb_dat_i(dwb_dat_i), .dwb_ack_i(dwb_ack_i), .imm_of(imm_of), .opd_of(opd_of), .opc_of(opc_of), .opa_of(opa_of), .opb_of(opb_of), .msr_ex(msr_ex), .mem_ex(mem_ex), .sfr_mx(sfr_mx), .gclk(gclk), .grst(grst), .dena(dena), .gpha(gpha));
initial begin
dwb_dat_i = 0;
dwb_ack_i = 0;
imm_of = 0;
opd_of = 0;
opc_of = 0;
opa_of = 0;
opb_of = 0;
msr_ex = 0;
mem_ex = 0;
sfr_mx = 0;
gclk = 0;
grst = 0;
dena = 0;
gpha = 0;
#2;

for(i=0;i<64;i=i+1) begin
dwb_dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dwb_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
imm_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opd_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opc_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb_of = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
msr_ex = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
mem_ex = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
sfr_mx = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
grst = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dena = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
gpha = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; gclk=1; #2;
if ((^{ref_dwb_adr_o,ref_dwb_sel_o,ref_dwb_stb_o,ref_dwb_cyc_o,ref_dwb_tag_o,ref_dwb_wre_o,ref_dwb_dat_o,ref_dwb_fb,ref_sel_mx,ref_dwb_mx,ref_exc_dwb}) === 1'bx || (^{dwb_adr_o,dwb_sel_o,dwb_stb_o,dwb_cyc_o,dwb_tag_o,dwb_wre_o,dwb_dat_o,dwb_fb,sel_mx,dwb_mx,exc_dwb}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({dwb_adr_o,dwb_sel_o,dwb_stb_o,dwb_cyc_o,dwb_tag_o,dwb_wre_o,dwb_dat_o,dwb_fb,sel_mx,dwb_mx,exc_dwb} !== {ref_dwb_adr_o,ref_dwb_sel_o,ref_dwb_stb_o,ref_dwb_cyc_o,ref_dwb_tag_o,ref_dwb_wre_o,ref_dwb_dat_o,ref_dwb_fb,ref_sel_mx,ref_dwb_mx,ref_exc_dwb}) failures=failures+1; end
gclk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule