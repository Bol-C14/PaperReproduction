`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned sys_clk,
    input longint unsigned sdram_rst,
    input longint unsigned tim_rp,
    input longint unsigned tim_rcd,
    input longint unsigned tim_refi,
    input longint unsigned tim_rfc,
    input longint unsigned stb,
    input longint unsigned we,
    input longint unsigned address,
    output longint unsigned ref_ack__dpi,
    output longint unsigned ref_read__dpi,
    output longint unsigned ref_write__dpi,
    output longint unsigned ref_concerned_bank__dpi,
    input longint unsigned read_safe,
    input longint unsigned write_safe,
    input longint unsigned precharge_safe,
    output longint unsigned ref_sdram_cs_n__dpi,
    output longint unsigned ref_sdram_we_n__dpi,
    output longint unsigned ref_sdram_cas_n__dpi,
    output longint unsigned ref_sdram_ras_n__dpi,
    output longint unsigned ref_sdram_adr__dpi,
    output longint unsigned ref_sdram_ba__dpi
);

module ref_hpdmc_mgmt (
    sys_clk,
    sdram_rst,
    tim_rp,
    tim_rcd,
    tim_refi,
    tim_rfc,
    stb,
    we,
    address,
    ref_ack,
    ref_read,
    ref_write,
    ref_concerned_bank,
    read_safe,
    write_safe,
    precharge_safe,
    ref_sdram_cs_n,
    ref_sdram_we_n,
    ref_sdram_cas_n,
    ref_sdram_ras_n,
    ref_sdram_adr,
    ref_sdram_ba
);
parameter sdram_depth = 26;
parameter sdram_columndepth = 9;
input sys_clk;
input sdram_rst;
input [2:0] tim_rp;
input [2:0] tim_rcd;
input [10:0] tim_refi;
input [3:0] tim_rfc;
input stb;
input we;
input [22:0] address;
output reg ref_ack;
output reg ref_read;
output reg ref_write;
output reg [3:0] ref_concerned_bank;
input read_safe;
input write_safe;
input [3:0] precharge_safe;
output reg ref_sdram_cs_n;
output reg ref_sdram_we_n;
output reg ref_sdram_cas_n;
output reg ref_sdram_ras_n;
output reg [12:0] ref_sdram_adr;
output reg [1:0] ref_sdram_ba;
longint unsigned ref_ack__dpi;
longint unsigned ref_read__dpi;
longint unsigned ref_write__dpi;
longint unsigned ref_concerned_bank__dpi;
longint unsigned ref_sdram_cs_n__dpi;
longint unsigned ref_sdram_we_n__dpi;
longint unsigned ref_sdram_cas_n__dpi;
longint unsigned ref_sdram_ras_n__dpi;
longint unsigned ref_sdram_adr__dpi;
longint unsigned ref_sdram_ba__dpi;

always @(*) begin
    ref_model_eval(sys_clk, sdram_rst, tim_rp, tim_rcd, tim_refi, tim_rfc, stb, we, address, ref_ack__dpi, ref_read__dpi, ref_write__dpi, ref_concerned_bank__dpi, read_safe, write_safe, precharge_safe, ref_sdram_cs_n__dpi, ref_sdram_we_n__dpi, ref_sdram_cas_n__dpi, ref_sdram_ras_n__dpi, ref_sdram_adr__dpi, ref_sdram_ba__dpi);
    ref_ack = ref_ack__dpi[0];
    ref_read = ref_read__dpi[0];
    ref_write = ref_write__dpi[0];
    ref_concerned_bank = ref_concerned_bank__dpi[3:0];
    ref_sdram_cs_n = ref_sdram_cs_n__dpi[0];
    ref_sdram_we_n = ref_sdram_we_n__dpi[0];
    ref_sdram_cas_n = ref_sdram_cas_n__dpi[0];
    ref_sdram_ras_n = ref_sdram_ras_n__dpi[0];
    ref_sdram_adr = ref_sdram_adr__dpi[12:0];
    ref_sdram_ba = ref_sdram_ba__dpi[1:0];
end
endmodule
