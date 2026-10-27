`timescale 1ns/1ps
module calibration_tb;
reg clk_core;
reg rst_x;
reg i_req;
reg i_wr;
reg [21:0] i_adrs;
reg [5:0] i_len;
wire o_ack;
wire ref_o_ack;
reg i_strw;
reg [3:0] i_be;
reg [31:0] i_dbw;
wire o_ackw;
wire ref_o_ackw;
wire o_strr;
wire ref_o_strr;
wire [31:0] o_dbr;
wire [31:0] ref_o_dbr;
wire o_req;
wire ref_o_req;
wire o_wr;
wire ref_o_wr;
wire [21:0] o_adrs;
wire [21:0] ref_o_adrs;
wire [5:0] o_len;
wire [5:0] ref_o_len;
reg i_ack;
wire o_strw;
wire ref_o_strw;
wire [3:0] o_be;
wire [3:0] ref_o_be;
wire [31:0] o_dbw;
wire [31:0] ref_o_dbw;
reg i_ackw;
reg i_strr;
reg [31:0] i_dbr;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fm_cmn_if_ff_out dut(.clk_core(clk_core), .rst_x(rst_x), .i_req(i_req), .i_wr(i_wr), .i_adrs(i_adrs), .i_len(i_len), .o_ack(o_ack), .i_strw(i_strw), .i_be(i_be), .i_dbw(i_dbw), .o_ackw(o_ackw), .o_strr(o_strr), .o_dbr(o_dbr), .o_req(o_req), .o_wr(o_wr), .o_adrs(o_adrs), .o_len(o_len), .i_ack(i_ack), .o_strw(o_strw), .o_be(o_be), .o_dbw(o_dbw), .i_ackw(i_ackw), .i_strr(i_strr), .i_dbr(i_dbr));
oracle_fm_cmn_if_ff_out golden(.clk_core(clk_core), .rst_x(rst_x), .i_req(i_req), .i_wr(i_wr), .i_adrs(i_adrs), .i_len(i_len), .o_ack(ref_o_ack), .i_strw(i_strw), .i_be(i_be), .i_dbw(i_dbw), .o_ackw(ref_o_ackw), .o_strr(ref_o_strr), .o_dbr(ref_o_dbr), .o_req(ref_o_req), .o_wr(ref_o_wr), .o_adrs(ref_o_adrs), .o_len(ref_o_len), .i_ack(i_ack), .o_strw(ref_o_strw), .o_be(ref_o_be), .o_dbw(ref_o_dbw), .i_ackw(i_ackw), .i_strr(i_strr), .i_dbr(i_dbr));
initial begin
clk_core = 0;
rst_x = 1;
i_req = 0;
i_wr = 0;
i_adrs = 0;
i_len = 0;
i_strw = 0;
i_be = 0;
i_dbw = 0;
i_ack = 0;
i_ackw = 0;
i_strr = 0;
i_dbr = 0;
#2;
rst_x = 0;
for(i=0;i<64;i=i+1) begin
i_req = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_adrs = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_len = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_strw = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_be = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_dbw = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_ack = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_ackw = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_strr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_dbr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_core=1; #2;
if ((^{ref_o_ack,ref_o_ackw,ref_o_strr,ref_o_dbr,ref_o_req,ref_o_wr,ref_o_adrs,ref_o_len,ref_o_strw,ref_o_be,ref_o_dbw}) === 1'bx || (^{o_ack,o_ackw,o_strr,o_dbr,o_req,o_wr,o_adrs,o_len,o_strw,o_be,o_dbw}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_ack,o_ackw,o_strr,o_dbr,o_req,o_wr,o_adrs,o_len,o_strw,o_be,o_dbw} !== ({ref_o_ack,ref_o_ackw,ref_o_strr,ref_o_dbr,ref_o_req,ref_o_wr,ref_o_adrs,ref_o_len,ref_o_strw,ref_o_be,ref_o_dbw} ^ 1'b1)) failures=failures+1; end
clk_core=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule