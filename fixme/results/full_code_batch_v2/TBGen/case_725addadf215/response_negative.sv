`timescale 1ns/1ps
module calibration_tb;
wire wb_clk_o;
wire ref_wb_clk_o;
wire wb_rst_o;
wire ref_wb_rst_o;
wire [19:0] iwb_adr_o;
wire [19:0] ref_iwb_adr_o;
wire [15:0] iwb_dat_o;
wire [15:0] ref_iwb_dat_o;
wire iwb_stb_o;
wire ref_iwb_stb_o;
wire iwb_we_o;
wire ref_iwb_we_o;
wire [1:0] iwb_sel_o;
wire [1:0] ref_iwb_sel_o;
wire [11:0] dwb_adr_o;
wire [11:0] ref_dwb_adr_o;
wire [7:0] dwb_dat_o;
wire [7:0] ref_dwb_dat_o;
wire dwb_stb_o;
wire ref_dwb_stb_o;
wire dwb_we_o;
wire ref_dwb_we_o;
reg [15:0] iwb_dat_i;
reg iwb_ack_i;
reg [7:0] dwb_dat_i;
reg dwb_ack_i;
reg [1:0] int_i;
reg [1:0] inte_i;
reg clk_i;
reg rst_i;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
ae18_core dut(.wb_clk_o(wb_clk_o), .wb_rst_o(wb_rst_o), .iwb_adr_o(iwb_adr_o), .iwb_dat_o(iwb_dat_o), .iwb_stb_o(iwb_stb_o), .iwb_we_o(iwb_we_o), .iwb_sel_o(iwb_sel_o), .dwb_adr_o(dwb_adr_o), .dwb_dat_o(dwb_dat_o), .dwb_stb_o(dwb_stb_o), .dwb_we_o(dwb_we_o), .iwb_dat_i(iwb_dat_i), .iwb_ack_i(iwb_ack_i), .dwb_dat_i(dwb_dat_i), .dwb_ack_i(dwb_ack_i), .int_i(int_i), .inte_i(inte_i), .clk_i(clk_i), .rst_i(rst_i));
oracle_ae18_core golden(.wb_clk_o(ref_wb_clk_o), .wb_rst_o(ref_wb_rst_o), .iwb_adr_o(ref_iwb_adr_o), .iwb_dat_o(ref_iwb_dat_o), .iwb_stb_o(ref_iwb_stb_o), .iwb_we_o(ref_iwb_we_o), .iwb_sel_o(ref_iwb_sel_o), .dwb_adr_o(ref_dwb_adr_o), .dwb_dat_o(ref_dwb_dat_o), .dwb_stb_o(ref_dwb_stb_o), .dwb_we_o(ref_dwb_we_o), .iwb_dat_i(iwb_dat_i), .iwb_ack_i(iwb_ack_i), .dwb_dat_i(dwb_dat_i), .dwb_ack_i(dwb_ack_i), .int_i(int_i), .inte_i(inte_i), .clk_i(clk_i), .rst_i(rst_i));
initial begin
iwb_dat_i = 0;
iwb_ack_i = 0;
dwb_dat_i = 0;
dwb_ack_i = 0;
int_i = 0;
inte_i = 0;
clk_i = 0;
rst_i = 1;
#2;
rst_i = 0;
for(i=0;i<64;i=i+1) begin
iwb_dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
iwb_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dwb_dat_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
dwb_ack_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
int_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inte_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_i=1; #2;
if ((^{ref_wb_clk_o,ref_wb_rst_o,ref_iwb_adr_o,ref_iwb_dat_o,ref_iwb_stb_o,ref_iwb_we_o,ref_iwb_sel_o,ref_dwb_adr_o,ref_dwb_dat_o,ref_dwb_stb_o,ref_dwb_we_o}) === 1'bx || (^{wb_clk_o,wb_rst_o,iwb_adr_o,iwb_dat_o,iwb_stb_o,iwb_we_o,iwb_sel_o,dwb_adr_o,dwb_dat_o,dwb_stb_o,dwb_we_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({wb_clk_o,wb_rst_o,iwb_adr_o,iwb_dat_o,iwb_stb_o,iwb_we_o,iwb_sel_o,dwb_adr_o,dwb_dat_o,dwb_stb_o,dwb_we_o} !== ({ref_wb_clk_o,ref_wb_rst_o,ref_iwb_adr_o,ref_iwb_dat_o,ref_iwb_stb_o,ref_iwb_we_o,ref_iwb_sel_o,ref_dwb_adr_o,ref_dwb_dat_o,ref_dwb_stb_o,ref_dwb_we_o} ^ 1'b1)) failures=failures+1; end
clk_i=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule