`timescale 1ns/1ps

module aeMB2_intu (
   mem_ex, bpc_ex, alu_ex, alu_mx, msr_ex, sfr_mx,
   exc_dwb, exc_ill, rpc_ex, opc_of, opa_of, opb_of, opd_of, imm_of,
   rd_of, ra_of, gclk, grst, dena, gpha
   );
   parameter AEMB_DWB = 32;   
   parameter AEMB_IWB = 32;
   parameter AEMB_HTX = 1;
   output [31:2] mem_ex;
   output [31:2] bpc_ex;   
   output [31:0] alu_ex,
		 alu_mx;   
   input [1:0] 	 exc_dwb;   
   input 	 exc_ill;
   input [31:2]  rpc_ex;
   input [5:0] 	 opc_of;
   input [31:0]  opa_of;
   input [31:0]  opb_of;
   input [31:0]  opd_of;   
   input [15:0]  imm_of;
   input [4:0] 	 rd_of,
		 ra_of;   
   output [9:0]  msr_ex;   
   output [31:0] sfr_mx;   
   input 	 gclk,
		 grst,
		 dena,
		 gpha;      
   reg [31:0]		alu_ex;
   reg [31:0]		alu_mx;
   reg [31:2]		bpc_ex;
   reg [31:2]		mem_ex;
   reg [31:0]		sfr_mx;
   localparam [2:0] 	MUX_SFR = 3'o7,
			MUX_BSF = 3'o6,
			MUX_MUL = 3'o5,
			MUX_MEM = 3'o4,
			MUX_RPC = 3'o2,
			MUX_ALU = 3'o1,
			MUX_NOP = 3'o0;   
   reg 			rMSR_C,
			rMSR_EE,
			rMSR_EIP,
			rMSR_CC,
			rMSR_MTX,
			rMSR_DTE, 
			rMSR_ITE,
			rMSR_BIP, 
			rMSR_IE,
			rMSR_BE;   
   reg [31:0] 		rEAR, 
			rEAR_C;
   reg [1:0] 		rESR,
			rESR_C;   
   reg [31:0] 		add_ex;
   reg 			add_c;
   wire [31:0] 		wADD;
   wire 		wADC;
   wire 		fCCC = !opc_of[5] & opc_of[1]; 
   wire 		fSUB = !opc_of[5] & opc_of[0]; 
   wire 		fCMP = !opc_of[3] & imm_of[1]; 
   wire 		wCMP = (fCMP) ? !wADC : wADD[31]; 
   wire [31:0] 		wOPA = (fSUB) ? ~opa_of : opa_of;
   wire 		wOPC = (fCCC) ? rMSR_CC : fSUB;
   assign 		{wADC, wADD} = (opb_of + wOPA) + wOPC; 
   always @(wADC or wADD or wCMP) begin
      {add_c, add_ex} <= #1 {wADC, wCMP, wADD[30:0]}; 
   end
   reg [31:0] 		slm_ex;
   always @(imm_of or opa_of or opb_of or opc_of
	    or rMSR_CC)
     case (opc_of[2:0])
       3'o0: slm_ex <= #1 opa_of | opb_of;
       3'o1: slm_ex <= #1 opa_of & opb_of;
       3'o2: slm_ex <= #1 opa_of ^ opb_of;
       3'o3: slm_ex <= #1 opa_of & ~opb_of;
       3'o4: case ({imm_of[6:5],imm_of[0]})
	       3'o1: slm_ex <= #1 {opa_of[31],opa_of[31:1]}; 
	       3'o3: slm_ex <= #1 {rMSR_CC,opa_of[31:1]}; 
	       3'o5: slm_ex <= #1 {1'b0,opa_of[31:1]}; 
	       3'o6: slm_ex <= #1 {{(24){opa_of[7]}}, opa_of[7:0]}; 
	       3'o7: slm_ex <= #1  {{(16){opa_of[15]}}, opa_of[15:0]}; 
	       default: slm_ex <= #1 32'hX;
	     endcase 
       default: slm_ex <= #1 32'hX;       
     endcase 
   always @(posedge gclk)
     if (grst) begin
	alu_ex <= 32'h0;
	alu_mx <= 32'h0;
	bpc_ex <= 30'h0;
	mem_ex <= 30'h0;
     end else if (dena) begin
	alu_mx <= #1 alu_ex;
	alu_ex <= #1 (opc_of[5]) ? slm_ex : add_ex;	
	mem_ex <= #1 wADD[AEMB_DWB-1:2]; 
	bpc_ex <= #1 
		  (!opc_of[0] & ra_of[3]) ? 
		  opb_of[AEMB_IWB-1:2] : 
		  wADD[AEMB_IWB-1:2]; 
     end
   assign msr_ex = {
		    rMSR_EIP,
		    rMSR_EE,
		    rMSR_DTE,
		    1'b0,
		    rMSR_ITE,
		    rMSR_MTX,
		    rMSR_BIP,
		    rMSR_C,
		    rMSR_IE,
		    rMSR_BE 
		    };
   wire [9:0] wRES = (ra_of[0]) ? 
	      (msr_ex[9:0]) & ~imm_of[9:0] : 
	      (msr_ex[9:0]) | imm_of[9:0]; 
   wire       fRTBD = (opc_of == 6'o55) & rd_of[1];
   wire       fBRKB = ((opc_of == 6'o46) | (opc_of == 6'o56)) & (ra_of[4:0] == 5'hC);
   wire       fRTID = (opc_of == 6'o55) & rd_of[0];
   wire       fBRKI = (opc_of == 6'o56) & (ra_of[4:0] == 5'hD);
   wire       fRTED = (opc_of == 6'o55) & rd_of[2];   
   wire       fBRKE = (opc_of == 6'o56) & (ra_of[4:0] == 5'hE);
   wire       fMOV = (opc_of == 6'o45);
   wire       fMTS = fMOV & &imm_of[15:14];
   wire       fMOP = fMOV & ~|imm_of[15:14];
   wire       fMFS = fMOV & imm_of[15] & !imm_of[14];   
   reg [31:0] sfr_ex;   
   reg [2:0]  sfr_sel;
   always @(posedge gclk)
     if (grst) begin
	sfr_ex <= 32'h0;
	sfr_mx <= 32'h0;
	sfr_sel <= 3'h0;
     end else if (dena) begin
	case (sfr_sel[2:0])
	  3'o5: sfr_mx <= #1 {30'd0, rESR_C};
	  3'o3: sfr_mx <= #1 rEAR_C;
	  3'o1: sfr_mx <= #1 {rMSR_C,
			      AEMB_HTX[0],
			      gpha,
			      19'd0,
			      rMSR_EIP,
			      rMSR_EE,
			      rMSR_DTE,
			      1'b0,
			      rMSR_ITE,
			      rMSR_MTX,
			      rMSR_BIP,
			      rMSR_C,
			      rMSR_IE,
			      rMSR_BE 
			      };
	  default: sfr_mx <= #1 sfr_ex;	  
	endcase 
	sfr_ex <= #1
		  {rMSR_CC,
		   AEMB_HTX[0],
		   gpha,
		   19'd0,
		   rMSR_EIP,
		   rMSR_EE,
		   rMSR_DTE,
		   1'b0,
		   rMSR_ITE,
		   rMSR_MTX,
		   rMSR_BIP,
		   rMSR_CC,
		   rMSR_IE,
		   rMSR_BE 
		   };
	sfr_sel <= #1 imm_of[2:0];	
     end
   always @(posedge gclk)
     if (grst) begin
	rMSR_BE <= 1'h0;
	rMSR_BIP <= 1'h0;
	rMSR_DTE <= 1'h0;
	rMSR_EE <= 1'h0;
	rMSR_EIP <= 1'h0;
	rMSR_IE <= 1'h0;
	rMSR_ITE <= 1'h0;
	rMSR_MTX <= 1'h0;
     end else if (dena) begin 
	rMSR_DTE <= #1
		   (fMTS) ? opa_of[7] :
		   (fMOP) ? wRES[7] :
		   rMSR_DTE;	
	rMSR_ITE <= #1
		   (fMTS) ? opa_of[5] :
		   (fMOP) ? wRES[5] :
		   rMSR_ITE;
	rMSR_MTX <= #1
		   (fMTS) ? opa_of[4] :
		   (fMOP) ? wRES[4] :
		   rMSR_MTX;	
	rMSR_BE <= #1
		   (fMTS) ? opa_of[0] :
		   (fMOP) ? wRES[0] :
		   rMSR_BE;	
	rMSR_IE <= #1
		   (fBRKI) ? 1'b0 :
		   (fRTID) ? 1'b1 :
		   (fMTS) ? opa_of[1] :
		   (fMOP) ? wRES[1] :
		   rMSR_IE;			
	rMSR_BIP <= #1
		    (fBRKB) ? 1'b1 :
		    (fRTBD) ? 1'b0 :
		    (fMTS) ? opa_of[3] :
		    (fMOP) ? wRES[3] :
		    rMSR_BIP;
	rMSR_EE <= #1
		   (fBRKE) ? 1'b0 :
		   (fRTED) ? 1'b1 :
		   (fMTS) ? opa_of[8] :
		   (fMOP) ? wRES[8] :
		   rMSR_EE;
	rMSR_EIP <= #1
		    (fBRKE) ? 1'b1 :
		    (fRTED) ? 1'b0 :
		    (fMTS) ? opa_of[9] :
		    (fMOP) ? wRES[9] :
		    rMSR_EIP;
     end 
   wire fADDSUB = !opc_of[5] & !opc_of[4] & !opc_of[2];
   wire fSHIFT  = (opc_of == 6'o44) & &imm_of[6:5];   
   always @(posedge gclk)
     if (grst) begin
	rEAR_C <= 32'h0;
	rESR_C <= 2'h0;
	rMSR_CC <= 1'h0;
     end else if (dena) begin
	rEAR_C <= #1 rEAR;
	rESR_C <= #1 rESR;	
	rMSR_CC <= #1 rMSR_C;
     end
   always @(posedge gclk)
     if (grst) begin
	rEAR <= 32'h0;
	rESR <= 2'h0;
	rMSR_C <= 1'h0;
     end else if (dena) begin
	rEAR <= #1 (exc_dwb[1]) ? {mem_ex, 2'o0} : rEAR_C; 
	rESR <= #1 (exc_ill | exc_dwb[1]) ? 
		{exc_ill, exc_dwb[1]} : rESR_C; 
	rMSR_C <= #1
		  (fMTS) ? opa_of[2] :
		  (fMOP) ? wRES[2] :
		  (fSHIFT) ? opa_of[0] : 
		  (fADDSUB) ? add_c : 
		  rMSR_CC;
     end 
endmodule
