`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned reset,
    input longint unsigned pc,
    input longint unsigned prev_pc,
    input longint unsigned prev_branch_in,
    input longint unsigned prev_taken,
    output longint unsigned cur_pred_ref__dpi
);

module gshare_ref (
    clk,
    reset,
    pc,
    prev_pc,
    prev_branch_in,
    prev_taken,
    cur_pred_ref
);
parameter GSHARE_WIDTH = 4;
parameter PHT_LEN = 16;
input clk;
input reset;
input [31:0] pc;
input [31:0] prev_pc;
input prev_branch_in;
input prev_taken;
output reg cur_pred_ref;
longint unsigned cur_pred_ref__dpi;

always @(*) begin
    ref_model_eval(clk, reset, pc, prev_pc, prev_branch_in, prev_taken, cur_pred_ref__dpi);
    cur_pred_ref = cur_pred_ref__dpi[0];
end
endmodule
