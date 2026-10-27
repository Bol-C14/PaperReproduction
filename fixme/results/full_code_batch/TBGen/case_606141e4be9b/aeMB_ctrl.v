`timescale 1ns/1ps

module aeMB_ctrl (
   rMXDST, rMXSRC, rMXTGT, rMXALT, rMXALU, rRW, dwb_stb_o, dwb_wre_o,
   fsl_stb_o, fsl_wre_o,
   rDLY, rIMM, rALT, rOPC, rRD, rRA, rRB, rPC, rBRA, rMSR_IE, xIREG,
   dwb_ack_i, iwb_ack_i, fsl_ack_i, gclk, grst, gena
   );
   output [1:0]  rMXDST;
   output [1:0]  rMXSRC, rMXTGT, rMXALT;
   output [2:0]  rMXALU;   
   output [4:0]  rRW;
   input 	 rDLY;
   input [15:0]  rIMM;
   input [10:0]  rALT;
   input [5:0] 	 rOPC;
   input [4:0] 	 rRD, rRA, rRB;
   input [31:2]  rPC;
   input 	 rBRA;
   input 	 rMSR_IE;
   input [31:0]  xIREG;   
   output 	 dwb_stb_o;
   output 	 dwb_wre_o;
   input 	 dwb_ack_i;
   input 	 iwb_ack_i;
   output 	 fsl_stb_o;
   output 	 fsl_wre_o;
   input 	 fsl_ack_i;   
   input 	 gclk, grst, gena;
   wire [5:0] 	 wOPC;
   wire [4:0] 	 wRD, wRA, wRB;
   wire [10:0] 	 wALT;   
   assign 	 {wOPC, wRD, wRA, wRB, wALT} = xIREG; 
   wire 	 fSFT = (rOPC == 6'o44);
   wire 	 fLOG = ({rOPC[5:4],rOPC[2]} == 3'o4);   
   wire 	 fMUL = (rOPC == 6'o20) | (rOPC == 6'o30);
   wire 	 fBSF = (rOPC == 6'o21) | (rOPC == 6'o31);
   wire 	 fDIV = (rOPC == 6'o22);   
   wire 	 fRTD = (rOPC == 6'o55);
   wire 	 fBCC = (rOPC == 6'o47) | (rOPC == 6'o57);
   wire 	 fBRU = (rOPC == 6'o46) | (rOPC == 6'o56);
   wire 	 fBRA = fBRU & rRA[3];   
   wire 	 fIMM = (rOPC == 6'o54);
   wire 	 fMOV = (rOPC == 6'o45);   
   wire 	 fLOD = ({rOPC[5:4],rOPC[2]} == 3'o6);
   wire 	 fSTR = ({rOPC[5:4],rOPC[2]} == 3'o7);
   wire 	 fLDST = (&rOPC[5:4]);   
   wire          fPUT = (rOPC == 6'o33) & rRB[4];
   wire 	 fGET = (rOPC == 6'o33) & !rRB[4];   
   wire 	 wSFT = (wOPC == 6'o44);
   wire 	 wLOG = ({wOPC[5:4],wOPC[2]} == 3'o4);   
   wire 	 wMUL = (wOPC == 6'o20) | (wOPC == 6'o30);
   wire 	 wBSF = (wOPC == 6'o21) | (wOPC == 6'o31);
   wire 	 wDIV = (wOPC == 6'o22);   
   wire 	 wRTD = (wOPC == 6'o55);
   wire 	 wBCC = (wOPC == 6'o47) | (wOPC == 6'o57);
   wire 	 wBRU = (wOPC == 6'o46) | (wOPC == 6'o56);
   wire 	 wBRA = wBRU & wRA[3];   
   wire 	 wIMM = (wOPC == 6'o54);
   wire 	 wMOV = (wOPC == 6'o45);   
   wire 	 wLOD = ({wOPC[5:4],wOPC[2]} == 3'o6);
   wire 	 wSTR = ({wOPC[5:4],wOPC[2]} == 3'o7);
   wire 	 wLDST = (&wOPC[5:4]);   
   wire          wPUT = (wOPC == 6'o33) & wRB[4];
   wire 	 wGET = (wOPC == 6'o33) & !wRB[4];   
   reg [31:2] 	 rPCLNK, xPCLNK;
   reg [1:0] 	 rMXDST, xMXDST;
   reg [4:0] 	 rRW, xRW;   
   reg [1:0] 	 rMXSRC, xMXSRC;
   reg [1:0] 	 rMXTGT, xMXTGT;
   reg [1:0] 	 rMXALT, xMXALT;
   wire 	 wRDWE = |xRW;
   wire 	 wAFWD_M = (xRW == wRA) & (xMXDST == 2'o2) & wRDWE;
   wire 	 wBFWD_M = (xRW == wRB) & (xMXDST == 2'o2) & wRDWE;
   wire 	 wAFWD_R = (xRW == wRA) & (xMXDST == 2'o0) & wRDWE;   
   wire 	 wBFWD_R = (xRW == wRB) & (xMXDST == 2'o0) & wRDWE;
   always @(rBRA or wAFWD_M or wAFWD_R or wBCC or wBFWD_M
	    or wBFWD_R or wBRU or wOPC) 
     if (rBRA) begin
	xMXALT <= 2'h0;
	xMXSRC <= 2'h0;
	xMXTGT <= 2'h0;
     end else begin
	xMXSRC <= (wBRU | wBCC) ? 2'o3 : 
		  (wAFWD_M) ? 2'o2 : 
		  (wAFWD_R) ? 2'o1 : 
		  2'o0; 
	xMXTGT <= (wOPC[3]) ? 2'o3 : 
		  (wBFWD_M) ? 2'o2 : 
		  (wBFWD_R) ? 2'o1 : 
		  2'o0; 
	xMXALT <= (wAFWD_M) ? 2'o2 : 
		  (wAFWD_R) ? 2'o1 : 
		  2'o0; 
     end 
   reg [2:0]     rMXALU, xMXALU;
   always @(rBRA or wBRA or wBSF or wDIV or wLOG or wMOV
	    or wMUL or wSFT)
     if (rBRA) begin
	xMXALU <= 3'h0;
     end else begin
	xMXALU <= (wBRA | wMOV) ? 3'o3 :
		  (wSFT) ? 3'o2 :
		  (wLOG) ? 3'o1 :
		  (wMUL) ? 3'o4 :
		  (wBSF) ? 3'o5 :
		  (wDIV) ? 3'o6 :
		  3'o0;      	
     end 
   wire 	 fSKIP = (rBRA & !rDLY);
   always @(fBCC or fBRU or fGET or fLOD or fRTD or fSKIP
	    or fSTR or rRD)
     if (fSKIP) begin
	xMXDST <= 2'h0;
	xRW <= 5'h0;
     end else begin
	xMXDST <= (fSTR | fRTD | fBCC) ? 2'o3 :
		  (fLOD | fGET) ? 2'o2 :
		  (fBRU) ? 2'o1 :
		  2'o0;
	xRW <= rRD;
     end 
   wire 	 fDACK = !(dwb_stb_o ^ dwb_ack_i);
   reg 		 rDWBSTB, xDWBSTB;
   reg 		 rDWBWRE, xDWBWRE;
   assign 	 dwb_stb_o = rDWBSTB;
   assign 	 dwb_wre_o = rDWBWRE;
   always @(fLOD or fSKIP or fSTR or iwb_ack_i)
     if (fSKIP) begin
	xDWBSTB <= 1'h0;
	xDWBWRE <= 1'h0;
     end else begin
	xDWBSTB <= (fLOD | fSTR) & iwb_ack_i;
	xDWBWRE <= fSTR & iwb_ack_i;	
     end
   always @(posedge gclk)
     if (grst) begin
	rDWBSTB <= 1'h0;
	rDWBWRE <= 1'h0;
     end else if (fDACK) begin
	rDWBSTB <= #1 xDWBSTB;
	rDWBWRE <= #1 xDWBWRE;	
     end
   wire 	 fFACK = !(fsl_stb_o ^ fsl_ack_i);   
   reg 		 rFSLSTB, xFSLSTB;
   reg 		 rFSLWRE, xFSLWRE;
   assign 	 fsl_stb_o = rFSLSTB;
   assign 	 fsl_wre_o = rFSLWRE;   
   always @(fGET or fPUT or fSKIP or iwb_ack_i) 
     if (fSKIP) begin
	xFSLSTB <= 1'h0;
	xFSLWRE <= 1'h0;
     end else begin
	xFSLSTB <= (fPUT | fGET) & iwb_ack_i;
	xFSLWRE <= fPUT & iwb_ack_i;	
     end
   always @(posedge gclk)
     if (grst) begin
	rFSLSTB <= 1'h0;
	rFSLWRE <= 1'h0;
     end else if (fFACK) begin
	rFSLSTB <= #1 xFSLSTB;
	rFSLWRE <= #1 xFSLWRE;	
     end
   always @(posedge gclk)
     if (grst) begin
	rMXALT <= 2'h0;
	rMXALU <= 3'h0;
	rMXDST <= 2'h0;
	rMXSRC <= 2'h0;
	rMXTGT <= 2'h0;
	rRW <= 5'h0;
     end else if (gena) begin 
	rMXDST <= #1 xMXDST;
	rRW <= #1 xRW;
	rMXSRC <= #1 xMXSRC;
	rMXTGT <= #1 xMXTGT;
	rMXALT <= #1 xMXALT;	
	rMXALU <= #1 xMXALU;	
     end
endmodule
