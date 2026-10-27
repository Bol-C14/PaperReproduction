`timescale 1ns/1ps
module oracle_fasm_dparam (
   dat_o, xdat_o,
   dat_i, adr_i, wre_i, stb_i, clk_i, rst_i, xdat_i, xadr_i, xwre_i,
   xstb_i, xclk_i, xrst_i
   ) ;
   parameter AW = 5; 
   parameter DW = 2; 
   output [DW-1:0] dat_o;  
   input [DW-1:0]  dat_i; 
   input [AW-1:0]  adr_i;
   input 	   wre_i; 
   input 	   stb_i; 
   input 	   clk_i,
		   rst_i;
   output [DW-1:0] xdat_o;  
   input [DW-1:0]  xdat_i;
   input [AW-1:0]  xadr_i;
   input 	   xwre_i;
   input 	   xstb_i; 
   input 	   xclk_i,
		   xrst_i;
   reg [DW-1:0]    lram [(1<<AW)-1:0];
   always @(posedge xclk_i)
     if (xwre_i) lram[xadr_i] <= #1 xdat_i;	
   assign 	   dat_o = lram[adr_i];
   assign 	   xdat_o = lram[xadr_i];   
   integer i;
   initial begin
      for (i=0; i<(1<<AW); i=i+1) begin
	 lram[i] <= $random;	 
      end
   end
endmodule