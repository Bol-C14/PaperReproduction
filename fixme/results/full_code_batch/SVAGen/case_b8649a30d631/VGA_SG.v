`timescale 1ns/1ps

module VGA_SG
  (
  input  wire	[9:0]	tc_hsblnk,
  input  wire	[9:0]	tc_hssync,
  input  wire	[9:0]	tc_hesync,
  input  wire	[9:0]	tc_heblnk,
  output reg	[9:0]	hcount = 0,
  output reg			hsync,
  output reg			hblnk = 0,
  input  wire	[9:0]	tc_vsblnk,
  input  wire	[9:0]	tc_vssync,
  input  wire	[9:0]	tc_vesync,
  input  wire	[9:0]	tc_veblnk,
  output reg	[9:0]	vcount = 0,
  output reg			vsync,
  output reg			vblnk = 0,
  input  wire			clk,
  input  wire			ce
  );
  always @(posedge clk)
		if(ce) begin
			if(hcount >= tc_heblnk) begin
				hcount <= 0;
				hblnk <= 0;
			end else begin
				hcount <= hcount + 1;
				hblnk <= (hcount >= tc_hsblnk);
			end
			hsync <= (hcount >= tc_hssync) && (hcount < tc_hesync);
		end
	always @(posedge clk)
		if(ce && hcount == tc_heblnk) begin
			if (vcount >= tc_veblnk) begin
				vcount <= 0;
				vblnk <= 0;
			end else begin
				vcount <= vcount + 1;
				vblnk <= (vcount >= tc_vsblnk);
			end
			vsync <= (vcount >= tc_vssync) && (vcount < tc_vesync);
		end
endmodule
