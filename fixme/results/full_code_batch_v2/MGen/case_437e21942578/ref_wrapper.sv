`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned reset,
    output longint unsigned rom_addr_ref__dpi,
    input longint unsigned rom_q,
    output longint unsigned ram_a_addr_ref__dpi,
    output longint unsigned ram_b_addr_ref__dpi,
    output longint unsigned ram_b_w_ref__dpi,
    output longint unsigned pe_ref__dpi,
    output longint unsigned done_ref__dpi
);

module FSM_ref (
    clk,
    reset,
    rom_addr_ref,
    rom_q,
    ram_a_addr_ref,
    ram_b_addr_ref,
    ram_b_w_ref,
    pe_ref,
    done_ref
);
input clk;
input reset;
output reg [8:0] rom_addr_ref;
input [28:0] rom_q;
output reg [5:0] ram_a_addr_ref;
output reg [5:0] ram_b_addr_ref;
output reg ram_b_w_ref;
output reg [10:0] pe_ref;
output reg done_ref;
longint unsigned rom_addr_ref__dpi;
longint unsigned ram_a_addr_ref__dpi;
longint unsigned ram_b_addr_ref__dpi;
longint unsigned ram_b_w_ref__dpi;
longint unsigned pe_ref__dpi;
longint unsigned done_ref__dpi;

always @(*) begin
    ref_model_eval(clk, reset, rom_addr_ref__dpi, rom_q, ram_a_addr_ref__dpi, ram_b_addr_ref__dpi, ram_b_w_ref__dpi, pe_ref__dpi, done_ref__dpi);
    rom_addr_ref = rom_addr_ref__dpi[8:0];
    ram_a_addr_ref = ram_a_addr_ref__dpi[5:0];
    ram_b_addr_ref = ram_b_addr_ref__dpi[5:0];
    ram_b_w_ref = ram_b_w_ref__dpi[0];
    pe_ref = pe_ref__dpi[10:0];
    done_ref = done_ref__dpi[0];
end
endmodule
