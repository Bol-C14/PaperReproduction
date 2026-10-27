`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned CS,
    input longint unsigned WR,
    input longint unsigned clk,
    input longint unsigned cmd,
    input longint unsigned din,
    output longint unsigned dout_ref__dpi,
    output longint unsigned mode_ref__dpi,
    input longint unsigned CE
);

module counter_ref (
    CS,
    WR,
    clk,
    cmd,
    din,
    dout_ref,
    mode_ref,
    CE
);
input CS;
input WR;
input clk;
input cmd;
input [7:0] din;
output reg [7:0] dout_ref;
output reg [7:0] mode_ref;
input [1:0] CE;
longint unsigned dout_ref__dpi;
longint unsigned mode_ref__dpi;

always @(*) begin
    ref_model_eval(CS, WR, clk, cmd, din, dout_ref__dpi, mode_ref__dpi, CE);
    dout_ref = dout_ref__dpi[7:0];
    mode_ref = mode_ref__dpi[7:0];
end
endmodule
