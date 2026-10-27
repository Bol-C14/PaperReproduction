`timescale 1ns/1ps
module calibration_tb;
reg sys_clk;
reg sys_rst;
reg [13:0] csr_a;
reg csr_we;
reg [31:0] csr_di;
wire [31:0] csr_do;
wire [31:0] ref_csr_do;
wire bypass;
wire ref_bypass;
wire sdram_rst;
wire ref_sdram_rst;
wire sdram_cke;
wire ref_sdram_cke;
wire sdram_cs_n;
wire ref_sdram_cs_n;
wire sdram_we_n;
wire ref_sdram_we_n;
wire sdram_cas_n;
wire ref_sdram_cas_n;
wire sdram_ras_n;
wire ref_sdram_ras_n;
wire [12:0] sdram_adr;
wire [12:0] ref_sdram_adr;
wire [1:0] sdram_ba;
wire [1:0] ref_sdram_ba;
wire [2:0] tim_rp;
wire [2:0] ref_tim_rp;
wire [2:0] tim_rcd;
wire [2:0] ref_tim_rcd;
wire tim_cas;
wire ref_tim_cas;
wire [10:0] tim_refi;
wire [10:0] ref_tim_refi;
wire [3:0] tim_rfc;
wire [3:0] ref_tim_rfc;
wire [1:0] tim_wr;
wire [1:0] ref_tim_wr;
wire idelay_rst;
wire ref_idelay_rst;
wire idelay_ce;
wire ref_idelay_ce;
wire idelay_inc;
wire ref_idelay_inc;
wire dqs_psen;
wire ref_dqs_psen;
wire dqs_psincdec;
wire ref_dqs_psincdec;
reg dqs_psdone;
reg [1:0] pll_stat;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
hpdmc_ctlif dut(.sys_clk(sys_clk), .sys_rst(sys_rst), .csr_a(csr_a), .csr_we(csr_we), .csr_di(csr_di), .csr_do(csr_do), .bypass(bypass), .sdram_rst(sdram_rst), .sdram_cke(sdram_cke), .sdram_cs_n(sdram_cs_n), .sdram_we_n(sdram_we_n), .sdram_cas_n(sdram_cas_n), .sdram_ras_n(sdram_ras_n), .sdram_adr(sdram_adr), .sdram_ba(sdram_ba), .tim_rp(tim_rp), .tim_rcd(tim_rcd), .tim_cas(tim_cas), .tim_refi(tim_refi), .tim_rfc(tim_rfc), .tim_wr(tim_wr), .idelay_rst(idelay_rst), .idelay_ce(idelay_ce), .idelay_inc(idelay_inc), .dqs_psen(dqs_psen), .dqs_psincdec(dqs_psincdec), .dqs_psdone(dqs_psdone), .pll_stat(pll_stat));
oracle_hpdmc_ctlif golden(.sys_clk(sys_clk), .sys_rst(sys_rst), .csr_a(csr_a), .csr_we(csr_we), .csr_di(csr_di), .csr_do(ref_csr_do), .bypass(ref_bypass), .sdram_rst(ref_sdram_rst), .sdram_cke(ref_sdram_cke), .sdram_cs_n(ref_sdram_cs_n), .sdram_we_n(ref_sdram_we_n), .sdram_cas_n(ref_sdram_cas_n), .sdram_ras_n(ref_sdram_ras_n), .sdram_adr(ref_sdram_adr), .sdram_ba(ref_sdram_ba), .tim_rp(ref_tim_rp), .tim_rcd(ref_tim_rcd), .tim_cas(ref_tim_cas), .tim_refi(ref_tim_refi), .tim_rfc(ref_tim_rfc), .tim_wr(ref_tim_wr), .idelay_rst(ref_idelay_rst), .idelay_ce(ref_idelay_ce), .idelay_inc(ref_idelay_inc), .dqs_psen(ref_dqs_psen), .dqs_psincdec(ref_dqs_psincdec), .dqs_psdone(dqs_psdone), .pll_stat(pll_stat));
initial begin
sys_clk = 0;
sys_rst = 1;
csr_a = 0;
csr_we = 0;
csr_di = 0;
dqs_psdone = 0;
pll_stat = 0;
#2;
sys_rst = 0;
for(i=0;i<64;i=i+1) begin
csr_a = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
csr_we = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
csr_di = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dqs_psdone = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pll_stat = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; sys_clk=1; #2;
if ((^{ref_csr_do,ref_bypass,ref_sdram_rst,ref_sdram_cke,ref_sdram_cs_n,ref_sdram_we_n,ref_sdram_cas_n,ref_sdram_ras_n,ref_sdram_adr,ref_sdram_ba,ref_tim_rp,ref_tim_rcd,ref_tim_cas,ref_tim_refi,ref_tim_rfc,ref_tim_wr,ref_idelay_rst,ref_idelay_ce,ref_idelay_inc,ref_dqs_psen,ref_dqs_psincdec}) === 1'bx || (^{csr_do,bypass,sdram_rst,sdram_cke,sdram_cs_n,sdram_we_n,sdram_cas_n,sdram_ras_n,sdram_adr,sdram_ba,tim_rp,tim_rcd,tim_cas,tim_refi,tim_rfc,tim_wr,idelay_rst,idelay_ce,idelay_inc,dqs_psen,dqs_psincdec}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({csr_do,bypass,sdram_rst,sdram_cke,sdram_cs_n,sdram_we_n,sdram_cas_n,sdram_ras_n,sdram_adr,sdram_ba,tim_rp,tim_rcd,tim_cas,tim_refi,tim_rfc,tim_wr,idelay_rst,idelay_ce,idelay_inc,dqs_psen,dqs_psincdec} !== {ref_csr_do,ref_bypass,ref_sdram_rst,ref_sdram_cke,ref_sdram_cs_n,ref_sdram_we_n,ref_sdram_cas_n,ref_sdram_ras_n,ref_sdram_adr,ref_sdram_ba,ref_tim_rp,ref_tim_rcd,ref_tim_cas,ref_tim_refi,ref_tim_rfc,ref_tim_wr,ref_idelay_rst,ref_idelay_ce,ref_idelay_inc,ref_dqs_psen,ref_dqs_psincdec}) failures=failures+1; end
sys_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule