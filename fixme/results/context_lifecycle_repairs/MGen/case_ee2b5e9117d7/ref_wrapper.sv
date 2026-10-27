`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned wb_clk_i,
    input longint unsigned wb_rst_i,
    input longint unsigned m1_wb_adr_i,
    input longint unsigned m1_wb_sel_i,
    input longint unsigned m1_wb_we_i,
    output longint unsigned ref_m1_wb_dat_o__dpi,
    input longint unsigned m1_wb_dat_i,
    input longint unsigned m1_wb_cyc_i,
    input longint unsigned m1_wb_stb_i,
    output longint unsigned ref_m1_wb_ack_o__dpi,
    output longint unsigned ref_m1_wb_err_o__dpi,
    input longint unsigned m2_wb_adr_i,
    input longint unsigned m2_wb_sel_i,
    input longint unsigned m2_wb_we_i,
    output longint unsigned ref_m2_wb_dat_o__dpi,
    input longint unsigned m2_wb_dat_i,
    input longint unsigned m2_wb_cyc_i,
    input longint unsigned m2_wb_stb_i,
    output longint unsigned ref_m2_wb_ack_o__dpi,
    output longint unsigned ref_m2_wb_err_o__dpi,
    output longint unsigned ref_s1_wb_adr_o__dpi,
    output longint unsigned ref_s1_wb_sel_o__dpi,
    output longint unsigned ref_s1_wb_we_o__dpi,
    output longint unsigned ref_s1_wb_cyc_o__dpi,
    output longint unsigned ref_s1_wb_stb_o__dpi,
    input longint unsigned s1_wb_ack_i,
    input longint unsigned s1_wb_err_i,
    input longint unsigned s1_wb_dat_i,
    output longint unsigned ref_s1_wb_dat_o__dpi,
    output longint unsigned ref_s2_wb_adr_o__dpi,
    output longint unsigned ref_s2_wb_sel_o__dpi,
    output longint unsigned ref_s2_wb_we_o__dpi,
    output longint unsigned ref_s2_wb_cyc_o__dpi,
    output longint unsigned ref_s2_wb_stb_o__dpi,
    input longint unsigned s2_wb_ack_i,
    input longint unsigned s2_wb_err_i,
    input longint unsigned s2_wb_dat_i,
    output longint unsigned ref_s2_wb_dat_o__dpi
);

module ref_eth_cop (
    wb_clk_i,
    wb_rst_i,
    m1_wb_adr_i,
    m1_wb_sel_i,
    m1_wb_we_i,
    ref_m1_wb_dat_o,
    m1_wb_dat_i,
    m1_wb_cyc_i,
    m1_wb_stb_i,
    ref_m1_wb_ack_o,
    ref_m1_wb_err_o,
    m2_wb_adr_i,
    m2_wb_sel_i,
    m2_wb_we_i,
    ref_m2_wb_dat_o,
    m2_wb_dat_i,
    m2_wb_cyc_i,
    m2_wb_stb_i,
    ref_m2_wb_ack_o,
    ref_m2_wb_err_o,
    ref_s1_wb_adr_o,
    ref_s1_wb_sel_o,
    ref_s1_wb_we_o,
    ref_s1_wb_cyc_o,
    ref_s1_wb_stb_o,
    s1_wb_ack_i,
    s1_wb_err_i,
    s1_wb_dat_i,
    ref_s1_wb_dat_o,
    ref_s2_wb_adr_o,
    ref_s2_wb_sel_o,
    ref_s2_wb_we_o,
    ref_s2_wb_cyc_o,
    ref_s2_wb_stb_o,
    s2_wb_ack_i,
    s2_wb_err_i,
    s2_wb_dat_i,
    ref_s2_wb_dat_o
);
input wb_clk_i;
input wb_rst_i;
input [31:0] m1_wb_adr_i;
input [3:0] m1_wb_sel_i;
input m1_wb_we_i;
output reg [31:0] ref_m1_wb_dat_o;
input [31:0] m1_wb_dat_i;
input m1_wb_cyc_i;
input m1_wb_stb_i;
output reg ref_m1_wb_ack_o;
output reg ref_m1_wb_err_o;
input [31:0] m2_wb_adr_i;
input [3:0] m2_wb_sel_i;
input m2_wb_we_i;
output reg [31:0] ref_m2_wb_dat_o;
input [31:0] m2_wb_dat_i;
input m2_wb_cyc_i;
input m2_wb_stb_i;
output reg ref_m2_wb_ack_o;
output reg ref_m2_wb_err_o;
output reg [31:0] ref_s1_wb_adr_o;
output reg [3:0] ref_s1_wb_sel_o;
output reg ref_s1_wb_we_o;
output reg ref_s1_wb_cyc_o;
output reg ref_s1_wb_stb_o;
input s1_wb_ack_i;
input s1_wb_err_i;
input [31:0] s1_wb_dat_i;
output reg [31:0] ref_s1_wb_dat_o;
output reg [31:0] ref_s2_wb_adr_o;
output reg [3:0] ref_s2_wb_sel_o;
output reg ref_s2_wb_we_o;
output reg ref_s2_wb_cyc_o;
output reg ref_s2_wb_stb_o;
input s2_wb_ack_i;
input s2_wb_err_i;
input [31:0] s2_wb_dat_i;
output reg [31:0] ref_s2_wb_dat_o;
longint unsigned ref_m1_wb_dat_o__dpi;
longint unsigned ref_m1_wb_ack_o__dpi;
longint unsigned ref_m1_wb_err_o__dpi;
longint unsigned ref_m2_wb_dat_o__dpi;
longint unsigned ref_m2_wb_ack_o__dpi;
longint unsigned ref_m2_wb_err_o__dpi;
longint unsigned ref_s1_wb_adr_o__dpi;
longint unsigned ref_s1_wb_sel_o__dpi;
longint unsigned ref_s1_wb_we_o__dpi;
longint unsigned ref_s1_wb_cyc_o__dpi;
longint unsigned ref_s1_wb_stb_o__dpi;
longint unsigned ref_s1_wb_dat_o__dpi;
longint unsigned ref_s2_wb_adr_o__dpi;
longint unsigned ref_s2_wb_sel_o__dpi;
longint unsigned ref_s2_wb_we_o__dpi;
longint unsigned ref_s2_wb_cyc_o__dpi;
longint unsigned ref_s2_wb_stb_o__dpi;
longint unsigned ref_s2_wb_dat_o__dpi;

always @(*) begin
    ref_model_eval(wb_clk_i, wb_rst_i, m1_wb_adr_i, m1_wb_sel_i, m1_wb_we_i, ref_m1_wb_dat_o__dpi, m1_wb_dat_i, m1_wb_cyc_i, m1_wb_stb_i, ref_m1_wb_ack_o__dpi, ref_m1_wb_err_o__dpi, m2_wb_adr_i, m2_wb_sel_i, m2_wb_we_i, ref_m2_wb_dat_o__dpi, m2_wb_dat_i, m2_wb_cyc_i, m2_wb_stb_i, ref_m2_wb_ack_o__dpi, ref_m2_wb_err_o__dpi, ref_s1_wb_adr_o__dpi, ref_s1_wb_sel_o__dpi, ref_s1_wb_we_o__dpi, ref_s1_wb_cyc_o__dpi, ref_s1_wb_stb_o__dpi, s1_wb_ack_i, s1_wb_err_i, s1_wb_dat_i, ref_s1_wb_dat_o__dpi, ref_s2_wb_adr_o__dpi, ref_s2_wb_sel_o__dpi, ref_s2_wb_we_o__dpi, ref_s2_wb_cyc_o__dpi, ref_s2_wb_stb_o__dpi, s2_wb_ack_i, s2_wb_err_i, s2_wb_dat_i, ref_s2_wb_dat_o__dpi);
    ref_m1_wb_dat_o = ref_m1_wb_dat_o__dpi[31:0];
    ref_m1_wb_ack_o = ref_m1_wb_ack_o__dpi[0];
    ref_m1_wb_err_o = ref_m1_wb_err_o__dpi[0];
    ref_m2_wb_dat_o = ref_m2_wb_dat_o__dpi[31:0];
    ref_m2_wb_ack_o = ref_m2_wb_ack_o__dpi[0];
    ref_m2_wb_err_o = ref_m2_wb_err_o__dpi[0];
    ref_s1_wb_adr_o = ref_s1_wb_adr_o__dpi[31:0];
    ref_s1_wb_sel_o = ref_s1_wb_sel_o__dpi[3:0];
    ref_s1_wb_we_o = ref_s1_wb_we_o__dpi[0];
    ref_s1_wb_cyc_o = ref_s1_wb_cyc_o__dpi[0];
    ref_s1_wb_stb_o = ref_s1_wb_stb_o__dpi[0];
    ref_s1_wb_dat_o = ref_s1_wb_dat_o__dpi[31:0];
    ref_s2_wb_adr_o = ref_s2_wb_adr_o__dpi[31:0];
    ref_s2_wb_sel_o = ref_s2_wb_sel_o__dpi[3:0];
    ref_s2_wb_we_o = ref_s2_wb_we_o__dpi[0];
    ref_s2_wb_cyc_o = ref_s2_wb_cyc_o__dpi[0];
    ref_s2_wb_stb_o = ref_s2_wb_stb_o__dpi[0];
    ref_s2_wb_dat_o = ref_s2_wb_dat_o__dpi[31:0];
end
endmodule
