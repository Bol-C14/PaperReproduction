`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg reset;
reg [31:0] dat;
reg [6:0] addr;
reg we;
wire busy;
wire ref_busy;
wire [3:0] SF_D;
wire [3:0] ref_SF_D;
wire LCD_E;
wire ref_LCD_E;
wire LCD_RS;
wire ref_LCD_RS;
wire LCD_RW;
wire ref_LCD_RW;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
lcd dut(.clk(clk), .reset(reset), .dat(dat), .addr(addr), .we(we), .busy(busy), .SF_D(SF_D), .LCD_E(LCD_E), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW));
oracle_lcd golden(.clk(clk), .reset(reset), .dat(dat), .addr(addr), .we(we), .busy(ref_busy), .SF_D(ref_SF_D), .LCD_E(ref_LCD_E), .LCD_RS(ref_LCD_RS), .LCD_RW(ref_LCD_RW));
initial begin
clk = 0;
reset = 1;
dat = 0;
addr = 0;
we = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
dat = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
addr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
we = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_busy,ref_SF_D,ref_LCD_E,ref_LCD_RS,ref_LCD_RW}) === 1'bx || (^{busy,SF_D,LCD_E,LCD_RS,LCD_RW}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({busy,SF_D,LCD_E,LCD_RS,LCD_RW} !== {ref_busy,ref_SF_D,ref_LCD_E,ref_LCD_RS,ref_LCD_RW}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule