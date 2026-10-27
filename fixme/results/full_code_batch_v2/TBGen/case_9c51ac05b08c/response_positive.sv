`timescale 1ns/1ps
module calibration_tb;
reg clock;
reg reset;
reg [8:0] command;
reg write;
wire ack;
wire ref_ack;
wire [3:0] LCD_D;
wire [3:0] ref_LCD_D;
wire LCD_E;
wire ref_LCD_E;
wire LCD_RS;
wire ref_LCD_RS;
wire LCD_RW;
wire ref_LCD_RW;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
lcd_ctrl dut(.clock(clock), .reset(reset), .command(command), .write(write), .ack(ack), .LCD_D(LCD_D), .LCD_E(LCD_E), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW));
oracle_lcd_ctrl golden(.clock(clock), .reset(reset), .command(command), .write(write), .ack(ref_ack), .LCD_D(ref_LCD_D), .LCD_E(ref_LCD_E), .LCD_RS(ref_LCD_RS), .LCD_RW(ref_LCD_RW));
initial begin
clock = 0;
reset = 1;
command = 0;
write = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
command = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
write = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clock=1; #2;
if ((^{ref_ack,ref_LCD_D,ref_LCD_E,ref_LCD_RS,ref_LCD_RW}) === 1'bx || (^{ack,LCD_D,LCD_E,LCD_RS,LCD_RW}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({ack,LCD_D,LCD_E,LCD_RS,LCD_RW} !== {ref_ack,ref_LCD_D,ref_LCD_E,ref_LCD_RS,ref_LCD_RW}) failures=failures+1; end
clock=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule