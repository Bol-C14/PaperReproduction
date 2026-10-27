`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_cs_a_n;
reg i_ck_a;
reg i_mosi_a;
reg i_cs_b_n;
reg i_ck_b;
reg i_mosi_b;
wire o_cs_a_n;
wire ref_o_cs_a_n;
wire o_cs_b_n;
wire ref_o_cs_b_n;
wire o_ck;
wire ref_o_ck;
wire o_mosi;
wire ref_o_mosi;
wire o_grant;
wire ref_o_grant;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
spiarbiter dut(.i_clk(i_clk), .i_cs_a_n(i_cs_a_n), .i_ck_a(i_ck_a), .i_mosi_a(i_mosi_a), .i_cs_b_n(i_cs_b_n), .i_ck_b(i_ck_b), .i_mosi_b(i_mosi_b), .o_cs_a_n(o_cs_a_n), .o_cs_b_n(o_cs_b_n), .o_ck(o_ck), .o_mosi(o_mosi), .o_grant(o_grant));
oracle_spiarbiter golden(.i_clk(i_clk), .i_cs_a_n(i_cs_a_n), .i_ck_a(i_ck_a), .i_mosi_a(i_mosi_a), .i_cs_b_n(i_cs_b_n), .i_ck_b(i_ck_b), .i_mosi_b(i_mosi_b), .o_cs_a_n(ref_o_cs_a_n), .o_cs_b_n(ref_o_cs_b_n), .o_ck(ref_o_ck), .o_mosi(ref_o_mosi), .o_grant(ref_o_grant));
initial begin
i_clk = 0;
i_cs_a_n = 0;
i_ck_a = 0;
i_mosi_a = 0;
i_cs_b_n = 0;
i_ck_b = 0;
i_mosi_b = 0;
#2;

for(i=0;i<64;i=i+1) begin
i_cs_a_n = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_ck_a = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_mosi_a = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_cs_b_n = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_ck_b = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_mosi_b = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_cs_a_n,ref_o_cs_b_n,ref_o_ck,ref_o_mosi,ref_o_grant}) === 1'bx || (^{o_cs_a_n,o_cs_b_n,o_ck,o_mosi,o_grant}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_cs_a_n,o_cs_b_n,o_ck,o_mosi,o_grant} !== ({ref_o_cs_a_n,ref_o_cs_b_n,ref_o_ck,ref_o_mosi,ref_o_grant} ^ 1'b1)) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule