`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk_i,
    input longint unsigned DataOrReg,
    input longint unsigned address,
    input longint unsigned instr_i,
    input longint unsigned reset,
    input longint unsigned vout_addr,
    output longint unsigned value_o_ref__dpi,
    output longint unsigned is_positive_ref__dpi
);

module CPU_ref (
    clk_i,
    DataOrReg,
    address,
    instr_i,
    reset,
    vout_addr,
    value_o_ref,
    is_positive_ref
);
input clk_i;
input DataOrReg;
input [4:0] address;
input [7:0] instr_i;
input reset;
input [1:0] vout_addr;
output reg [7:0] value_o_ref;
output reg is_positive_ref;
longint unsigned value_o_ref__dpi;
longint unsigned is_positive_ref__dpi;

always @(*) begin
    ref_model_eval(clk_i, DataOrReg, address, instr_i, reset, vout_addr, value_o_ref__dpi, is_positive_ref__dpi);
    value_o_ref = value_o_ref__dpi[7:0];
    is_positive_ref = is_positive_ref__dpi[0];
end
endmodule
