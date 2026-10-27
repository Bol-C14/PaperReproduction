`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    output longint unsigned ref_clk_o__dpi,
    input longint unsigned rst0_i,
    input longint unsigned clk0_i,
    input longint unsigned rst1_i,
    input longint unsigned clk1_i,
    input longint unsigned rst2_i,
    input longint unsigned clk2_i,
    input longint unsigned rst3_i,
    input longint unsigned clk3_i,
    input longint unsigned rst4_i,
    input longint unsigned clk4_i,
    input longint unsigned rst5_i,
    input longint unsigned clk5_i,
    input longint unsigned rst6_i,
    input longint unsigned clk6_i,
    input longint unsigned rst7_i,
    input longint unsigned clk7_i,
    input longint unsigned enable,
    input longint unsigned select
);

module ref_clock_switch8_basic (
    ref_clk_o,
    rst0_i,
    clk0_i,
    rst1_i,
    clk1_i,
    rst2_i,
    clk2_i,
    rst3_i,
    clk3_i,
    rst4_i,
    clk4_i,
    rst5_i,
    clk5_i,
    rst6_i,
    clk6_i,
    rst7_i,
    clk7_i,
    enable,
    select
);
output reg ref_clk_o;
input rst0_i;
input clk0_i;
input rst1_i;
input clk1_i;
input rst2_i;
input clk2_i;
input rst3_i;
input clk3_i;
input rst4_i;
input clk4_i;
input rst5_i;
input clk5_i;
input rst6_i;
input clk6_i;
input rst7_i;
input clk7_i;
input enable;
input [2:0] select;
longint unsigned ref_clk_o__dpi;

always @(*) begin
    ref_model_eval(ref_clk_o__dpi, rst0_i, clk0_i, rst1_i, clk1_i, rst2_i, clk2_i, rst3_i, clk3_i, rst4_i, clk4_i, rst5_i, clk5_i, rst6_i, clk6_i, rst7_i, clk7_i, enable, select);
    ref_clk_o = ref_clk_o__dpi[0];
end
endmodule
