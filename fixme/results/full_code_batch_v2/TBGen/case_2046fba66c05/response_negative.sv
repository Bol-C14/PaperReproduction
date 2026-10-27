`timescale 1ns/1ps
module calibration_tb;
wire [2:0] sbox_sel;
wire [2:0] ref_sbox_sel;
wire [1:0] rk_sel;
wire [1:0] ref_rk_sel;
wire [1:0] key_out_sel;
wire [1:0] ref_key_out_sel;
wire [1:0] col_sel;
wire [1:0] ref_col_sel;
wire [3:0] key_en;
wire [3:0] ref_key_en;
wire [3:0] col_en;
wire [3:0] ref_col_en;
wire [3:0] round;
wire [3:0] ref_round;
wire bypass_rk;
wire ref_bypass_rk;
wire bypass_key_en;
wire ref_bypass_key_en;
wire key_sel;
wire ref_key_sel;
wire iv_cnt_en;
wire ref_iv_cnt_en;
wire iv_cnt_sel;
wire ref_iv_cnt_sel;
wire key_derivation_en;
wire ref_key_derivation_en;
wire end_comp;
wire ref_end_comp;
wire key_init;
wire ref_key_init;
wire key_gen;
wire ref_key_gen;
wire mode_ctr;
wire ref_mode_ctr;
wire mode_cbc;
wire ref_mode_cbc;
wire last_round;
wire ref_last_round;
wire encrypt_decrypt;
wire ref_encrypt_decrypt;
reg [1:0] operation_mode;
reg [1:0] aes_mode;
reg start;
reg disable_core;
reg clk;
reg rst_n;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
control_unit dut(.sbox_sel(sbox_sel), .rk_sel(rk_sel), .key_out_sel(key_out_sel), .col_sel(col_sel), .key_en(key_en), .col_en(col_en), .round(round), .bypass_rk(bypass_rk), .bypass_key_en(bypass_key_en), .key_sel(key_sel), .iv_cnt_en(iv_cnt_en), .iv_cnt_sel(iv_cnt_sel), .key_derivation_en(key_derivation_en), .end_comp(end_comp), .key_init(key_init), .key_gen(key_gen), .mode_ctr(mode_ctr), .mode_cbc(mode_cbc), .last_round(last_round), .encrypt_decrypt(encrypt_decrypt), .operation_mode(operation_mode), .aes_mode(aes_mode), .start(start), .disable_core(disable_core), .clk(clk), .rst_n(rst_n));
oracle_control_unit golden(.sbox_sel(ref_sbox_sel), .rk_sel(ref_rk_sel), .key_out_sel(ref_key_out_sel), .col_sel(ref_col_sel), .key_en(ref_key_en), .col_en(ref_col_en), .round(ref_round), .bypass_rk(ref_bypass_rk), .bypass_key_en(ref_bypass_key_en), .key_sel(ref_key_sel), .iv_cnt_en(ref_iv_cnt_en), .iv_cnt_sel(ref_iv_cnt_sel), .key_derivation_en(ref_key_derivation_en), .end_comp(ref_end_comp), .key_init(ref_key_init), .key_gen(ref_key_gen), .mode_ctr(ref_mode_ctr), .mode_cbc(ref_mode_cbc), .last_round(ref_last_round), .encrypt_decrypt(ref_encrypt_decrypt), .operation_mode(operation_mode), .aes_mode(aes_mode), .start(start), .disable_core(disable_core), .clk(clk), .rst_n(rst_n));
initial begin
operation_mode = 0;
aes_mode = 0;
start = 0;
disable_core = 0;
clk = 0;
rst_n = 0;
#2;
rst_n = 1;
for(i=0;i<64;i=i+1) begin
operation_mode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
aes_mode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
start = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
disable_core = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_sbox_sel,ref_rk_sel,ref_key_out_sel,ref_col_sel,ref_key_en,ref_col_en,ref_round,ref_bypass_rk,ref_bypass_key_en,ref_key_sel,ref_iv_cnt_en,ref_iv_cnt_sel,ref_key_derivation_en,ref_end_comp,ref_key_init,ref_key_gen,ref_mode_ctr,ref_mode_cbc,ref_last_round,ref_encrypt_decrypt}) === 1'bx || (^{sbox_sel,rk_sel,key_out_sel,col_sel,key_en,col_en,round,bypass_rk,bypass_key_en,key_sel,iv_cnt_en,iv_cnt_sel,key_derivation_en,end_comp,key_init,key_gen,mode_ctr,mode_cbc,last_round,encrypt_decrypt}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({sbox_sel,rk_sel,key_out_sel,col_sel,key_en,col_en,round,bypass_rk,bypass_key_en,key_sel,iv_cnt_en,iv_cnt_sel,key_derivation_en,end_comp,key_init,key_gen,mode_ctr,mode_cbc,last_round,encrypt_decrypt} !== ({ref_sbox_sel,ref_rk_sel,ref_key_out_sel,ref_col_sel,ref_key_en,ref_col_en,ref_round,ref_bypass_rk,ref_bypass_key_en,ref_key_sel,ref_iv_cnt_en,ref_iv_cnt_sel,ref_key_derivation_en,ref_end_comp,ref_key_init,ref_key_gen,ref_mode_ctr,ref_mode_cbc,ref_last_round,ref_encrypt_decrypt} ^ 1'b1)) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule