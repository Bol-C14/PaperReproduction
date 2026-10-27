`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk,
    input longint unsigned reset,
    input longint unsigned dat,
    input longint unsigned addr,
    input longint unsigned we,
    output longint unsigned ref_busy__dpi,
    output longint unsigned ref_SF_D__dpi,
    output longint unsigned ref_LCD_E__dpi,
    output longint unsigned ref_LCD_RS__dpi,
    output longint unsigned ref_LCD_RW__dpi
);

module ref_lcd (
    clk,
    reset,
    dat,
    addr,
    we,
    ref_busy,
    ref_SF_D,
    ref_LCD_E,
    ref_LCD_RS,
    ref_LCD_RW
);
input clk;
input reset;
input [31:0] dat;
input [6:0] addr;
input we;
output reg ref_busy;
output reg [3:0] ref_SF_D;
output reg ref_LCD_E;
output reg ref_LCD_RS;
output reg ref_LCD_RW;
longint unsigned ref_busy__dpi;
longint unsigned ref_SF_D__dpi;
longint unsigned ref_LCD_E__dpi;
longint unsigned ref_LCD_RS__dpi;
longint unsigned ref_LCD_RW__dpi;

always @(*) begin
    ref_model_eval(clk, reset, dat, addr, we, ref_busy__dpi, ref_SF_D__dpi, ref_LCD_E__dpi, ref_LCD_RS__dpi, ref_LCD_RW__dpi);
    ref_busy = ref_busy__dpi[0];
    ref_SF_D = ref_SF_D__dpi[3:0];
    ref_LCD_E = ref_LCD_E__dpi[0];
    ref_LCD_RS = ref_LCD_RS__dpi[0];
    ref_LCD_RW = ref_LCD_RW__dpi[0];
end
endmodule
