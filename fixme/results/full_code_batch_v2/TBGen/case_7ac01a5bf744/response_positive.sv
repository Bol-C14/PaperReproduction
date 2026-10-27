`timescale 1ns/1ps
module calibration_tb;
reg clk_i;
reg nrst_i;
reg [3:0] wb_adr_i;
wire [31:0] wb_dat_o;
wire [31:0] ref_wb_dat_o;
reg [31:0] wb_dat_i;
reg [3:0] wb_sel_i;
reg wb_we_i;
reg wb_stb_i;
reg wb_cyc_i;
wire wb_ack_o;
wire ref_wb_ack_o;
wire wb_err_o;
wire ref_wb_err_o;
reg [7:0] ws_i;
wire [31:0] datareg0;
wire [31:0] ref_datareg0;
wire [31:0] datareg1;
wire [31:0] ref_datareg1;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
wb_regfile dut(.clk_i(clk_i), .nrst_i(nrst_i), .wb_adr_i(wb_adr_i), .wb_dat_o(wb_dat_o), .wb_dat_i(wb_dat_i), .wb_sel_i(wb_sel_i), .wb_we_i(wb_we_i), .wb_stb_i(wb_stb_i), .wb_cyc_i(wb_cyc_i), .wb_ack_o(wb_ack_o), .wb_err_o(wb_err_o), .ws_i(ws_i), .datareg0(datareg0), .datareg1(datareg1));
oracle_wb_regfile golden(.clk_i(clk_i), .nrst_i(nrst_i), .wb_adr_i(wb_adr_i), .wb_dat_o(ref_wb_dat_o), .wb_dat_i(wb_dat_i), .wb_sel_i(wb_sel_i), .wb_we_i(wb_we_i), .wb_stb_i(wb_stb_i), .wb_cyc_i(wb_cyc_i), .wb_ack_o(ref_wb_ack_o), .wb_err_o(ref_wb_err_o), .ws_i(ws_i), .datareg0(ref_datareg0), .datareg1(ref_datareg1));
initial begin
clk_i = 0;
nrst_i = 0;
wb_adr_i = 0;
wb_dat_i = 0;
wb_sel_i = 0;
wb_we_i = 0;
wb_stb_i = 0;
wb_cyc_i = 0;
ws_i = 0;
#2;

for(i=0;i<64;i=i+1) begin
nrst_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wb_adr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wb_dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wb_sel_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wb_we_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wb_stb_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wb_cyc_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ws_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_i=1; #2;
if ((^{ref_wb_dat_o,ref_wb_ack_o,ref_wb_err_o,ref_datareg0,ref_datareg1}) === 1'bx || (^{wb_dat_o,wb_ack_o,wb_err_o,datareg0,datareg1}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({wb_dat_o,wb_ack_o,wb_err_o,datareg0,datareg1} !== {ref_wb_dat_o,ref_wb_ack_o,ref_wb_err_o,ref_datareg0,ref_datareg1}) failures=failures+1; end
clk_i=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule