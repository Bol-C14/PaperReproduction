`timescale 1ns/1ps
module calibration_tb;
reg reset_n;
reg clk_50;
reg [2:0] pixel;
reg [2:0] read_data;
reg [8:0] SW;
wire [3:0] VGA_R;
wire [3:0] ref_VGA_R;
wire [3:0] VGA_G;
wire [3:0] ref_VGA_G;
wire [3:0] VGA_B;
wire [3:0] ref_VGA_B;
wire [9:0] LEDR;
wire [9:0] ref_LEDR;
wire VGA_VS;
wire ref_VGA_VS;
wire VGA_HS;
wire ref_VGA_HS;
wire [10:0] read_addr;
wire [10:0] ref_read_addr;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
vga_controller dut(.reset_n(reset_n), .clk_50(clk_50), .pixel(pixel), .read_data(read_data), .SW(SW), .VGA_R(VGA_R), .VGA_G(VGA_G), .VGA_B(VGA_B), .LEDR(LEDR), .VGA_VS(VGA_VS), .VGA_HS(VGA_HS), .read_addr(read_addr));
oracle_vga_controller golden(.reset_n(reset_n), .clk_50(clk_50), .pixel(pixel), .read_data(read_data), .SW(SW), .VGA_R(ref_VGA_R), .VGA_G(ref_VGA_G), .VGA_B(ref_VGA_B), .LEDR(ref_LEDR), .VGA_VS(ref_VGA_VS), .VGA_HS(ref_VGA_HS), .read_addr(ref_read_addr));
initial begin
reset_n = 0;
clk_50 = 0;
pixel = 0;
read_data = 0;
SW = 0;
#2;
reset_n = 1;
for(i=0;i<64;i=i+1) begin
pixel = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
read_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
SW = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_50=1; #2;
if ((^{ref_VGA_R,ref_VGA_G,ref_VGA_B,ref_LEDR,ref_VGA_VS,ref_VGA_HS,ref_read_addr}) === 1'bx || (^{VGA_R,VGA_G,VGA_B,LEDR,VGA_VS,VGA_HS,read_addr}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({VGA_R,VGA_G,VGA_B,LEDR,VGA_VS,VGA_HS,read_addr} !== {ref_VGA_R,ref_VGA_G,ref_VGA_B,ref_LEDR,ref_VGA_VS,ref_VGA_HS,ref_read_addr}) failures=failures+1; end
clk_50=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule