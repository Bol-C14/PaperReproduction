`timescale 1ns/1ps

module aeMB2_dwbif (
   dwb_adr_o, dwb_sel_o, dwb_stb_o, dwb_cyc_o, dwb_tag_o, dwb_wre_o,
   dwb_dat_o, dwb_fb, sel_mx, dwb_mx, exc_dwb,
   dwb_dat_i, dwb_ack_i, imm_of, opd_of, opc_of, opa_of, opb_of,
   msr_ex, mem_ex, sfr_mx, gclk, grst, dena, gpha
   );
   parameter AEMB_DWB = 32; 
   output [AEMB_DWB-1:2] dwb_adr_o;   
   output [3:0] 	 dwb_sel_o;   
   output 		 dwb_stb_o,
			 dwb_cyc_o,
			 dwb_tag_o, 
			 dwb_wre_o;   
   output [31:0] 	 dwb_dat_o;   
   input [31:0] 	 dwb_dat_i; 		 
   input 		 dwb_ack_i;
   output 		 dwb_fb;
   output [3:0] 	 sel_mx;   
   output [31:0] 	 dwb_mx;   
   input [15:0] 	 imm_of;
   input [31:0] 	 opd_of;   
   input [5:0] 		 opc_of;    
   input [1:0] 		 opa_of;
   input [1:0] 		 opb_of;
   input [7:0] 		 msr_ex;   
   input [AEMB_DWB-1:2]  mem_ex;
   input [7:5] 		 sfr_mx;   
   output [1:0] 	 exc_dwb; 
   input 		 gclk,
			 grst,
			 dena,
			 gpha;   
   reg			dwb_cyc_o;
   reg [31:0]		dwb_dat_o;
   reg [31:0]		dwb_mx;
   reg [3:0]		dwb_sel_o;
   reg			dwb_stb_o;
   reg			dwb_wre_o;
   reg [3:0]		sel_mx;
   reg 			dwb_exc;
   wire [1:0] 		wOFF = (opa_of[1:0] + opb_of[1:0]); 
   wire [3:0] 		wSEL = {opc_of[1:0], wOFF}; 
   assign 		dwb_fb = (dwb_stb_o ~^ dwb_ack_i); 
   assign 		dwb_adr_o = mem_ex; 
   assign               exc_dwb = {dwb_exc, 1'b0};
   reg [31:0] 		dwb_lat;   
   reg [31:0] 		opd_ex;
   always @(posedge gclk)
     if (grst) begin
	dwb_dat_o <= 32'h0;
     end else if (dena) begin
	case (opc_of[1:0])
	  2'o0: dwb_dat_o <= #1 {(4){opd_of[7:0]}};
	  2'o1: dwb_dat_o <= #1 {(2){opd_of[15:0]}};
	  2'o2: dwb_dat_o <= #1 opd_of;
	  default: dwb_dat_o <= #1 32'hX;
	endcase 
     end
   always @(posedge gclk)
     if (grst) begin
	dwb_exc <= 1'h0;
	dwb_mx <= 32'h0;
	dwb_sel_o <= 4'h0;
	dwb_wre_o <= 1'h0;
	sel_mx <= 4'h0;
     end else if (dena) begin
	sel_mx <= #1 dwb_sel_o; 
	dwb_wre_o <= #1 opc_of[2]; 
	dwb_mx <= #1 
		  (dwb_ack_i) ? 
		  dwb_dat_i : 
		  dwb_lat; 
	case (wSEL) 
	  4'h8: dwb_sel_o <= #1 4'hF;
	  4'h4: dwb_sel_o <= #1 4'hC;
	  4'h6: dwb_sel_o <= #1 4'h3;
	  4'h0: dwb_sel_o <= #1 4'h8;
	  4'h1: dwb_sel_o <= #1 4'h4;
	  4'h2: dwb_sel_o <= #1 4'h2;
	  4'h3: dwb_sel_o <= #1 4'h1;	
	  4'hC, 4'hD, 4'hE, 4'hF: 
	    dwb_sel_o <= #1 4'h0;
	  default: dwb_sel_o <= #1 4'hX;
	endcase 
	dwb_exc <= #1 &opc_of[5:4] & 
		   ((opc_of[0] & wOFF[0]) | 
		    (opc_of[1] & |wOFF[1:0]) 
		    );
     end 
   always @(posedge gclk)
     if (grst) begin
	dwb_lat <= 32'h0;
     end else if (dwb_ack_i) begin 
	dwb_lat <= #1 dwb_dat_i;	
     end
   always @(posedge gclk)
     if (grst) begin
	dwb_cyc_o <= 1'h0;
	dwb_stb_o <= 1'h0;
     end else if (dwb_fb) begin 
	dwb_stb_o <= #1
		     (dena) ? &opc_of[5:4] : 
		     (dwb_stb_o & !dwb_ack_i); 
	dwb_cyc_o <= #1 
		     (dena) ? &opc_of[5:4] | msr_ex[0] :
		     (dwb_stb_o & !dwb_ack_i) | msr_ex[0];	
     end
   assign dwb_tag_o = msr_ex[7]; 
endmodule
