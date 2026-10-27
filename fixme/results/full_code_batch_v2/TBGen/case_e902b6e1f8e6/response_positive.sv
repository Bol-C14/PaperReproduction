`timescale 1ns/1ps
module calibration_tb;
reg clk_i;
reg rst_i;
reg [31:0] pixel0_x_i;
reg [31:0] pixel0_y_i;
reg [31:0] pixel1_x_i;
reg [31:0] pixel1_y_i;
reg draw_line_i;
reg read_pixel_i;
wire busy_o;
wire ref_busy_o;
wire x_major_o;
wire ref_x_major_o;
wire [15:0] major_o;
wire [15:0] ref_major_o;
wire [15:0] minor_o;
wire [15:0] ref_minor_o;
wire valid_o;
wire ref_valid_o;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
bresenham_line dut(.clk_i(clk_i), .rst_i(rst_i), .pixel0_x_i(pixel0_x_i), .pixel0_y_i(pixel0_y_i), .pixel1_x_i(pixel1_x_i), .pixel1_y_i(pixel1_y_i), .draw_line_i(draw_line_i), .read_pixel_i(read_pixel_i), .busy_o(busy_o), .x_major_o(x_major_o), .major_o(major_o), .minor_o(minor_o), .valid_o(valid_o));
oracle_bresenham_line golden(.clk_i(clk_i), .rst_i(rst_i), .pixel0_x_i(pixel0_x_i), .pixel0_y_i(pixel0_y_i), .pixel1_x_i(pixel1_x_i), .pixel1_y_i(pixel1_y_i), .draw_line_i(draw_line_i), .read_pixel_i(read_pixel_i), .busy_o(ref_busy_o), .x_major_o(ref_x_major_o), .major_o(ref_major_o), .minor_o(ref_minor_o), .valid_o(ref_valid_o));
initial begin
clk_i = 0;
rst_i = 1;
pixel0_x_i = 0;
pixel0_y_i = 0;
pixel1_x_i = 0;
pixel1_y_i = 0;
draw_line_i = 0;
read_pixel_i = 0;
#2;
rst_i = 0;
for(i=0;i<64;i=i+1) begin
pixel0_x_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pixel0_y_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pixel1_x_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pixel1_y_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
draw_line_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
read_pixel_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk_i=1; #2;
if ((^{ref_busy_o,ref_x_major_o,ref_major_o,ref_minor_o,ref_valid_o}) === 1'bx || (^{busy_o,x_major_o,major_o,minor_o,valid_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({busy_o,x_major_o,major_o,minor_o,valid_o} !== {ref_busy_o,ref_x_major_o,ref_major_o,ref_minor_o,ref_valid_o}) failures=failures+1; end
clk_i=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule