`timescale 1ns/1ps
 

module top(clk, srst, vdat_buffer_di, ColorDepth, PseudoColor, 
	vdat_buffer_empty, vdat_buffer_rreq, rgb_fifo_full,
	rgb_fifo_wreq, r, g, b,
	clut_req, clut_ack, clut_offs, clut_q
	);
	input clk;                    
	input srst;                   
	input [31:0] vdat_buffer_di;  
	input [1:0] ColorDepth;       
	input       PseudoColor;      
	input  vdat_buffer_empty;
	output vdat_buffer_rreq;      
	reg    vdat_buffer_rreq;
	input  rgb_fifo_full;
	output rgb_fifo_wreq;
	reg    rgb_fifo_wreq;
	output [7:0] r, g, b;         
	reg    [7:0] r, g, b;
	output        clut_req;       
	reg clut_req;
	input         clut_ack;       
	output [ 7:0] clut_offs;      
	reg [7:0] clut_offs;
	input  [23:0] clut_q;         
	reg [31:0] DataBuffer;
	reg [7:0] Ra, Ga, Ba;
	reg [1:0] colcnt;
	reg RGBbuf_wreq;
	always @(posedge clk)
		if (vdat_buffer_rreq)
			DataBuffer <= #1 vdat_buffer_di;
	parameter idle        = 7'b000_0000, 
	          fill_buf    = 7'b000_0001,
	          bw_8bpp     = 7'b000_0010,
	          col_8bpp    = 7'b000_0100,
	          col_16bpp_a = 7'b000_1000,
	          col_16bpp_b = 7'b001_0000,
	          col_24bpp   = 7'b010_0000,
	          col_32bpp   = 7'b100_0000;
	reg [6:0] c_state;   
	reg [6:0] nxt_state; 
	always @(c_state or vdat_buffer_empty or ColorDepth or PseudoColor or rgb_fifo_full or colcnt or clut_ack)
	begin : nxt_state_decoder
		nxt_state = c_state;
		case (c_state) 
			idle:
				if (!vdat_buffer_empty && !rgb_fifo_full)
					nxt_state = fill_buf;
			fill_buf:
				case (ColorDepth) 
					2'b00: 
						if (PseudoColor)
							nxt_state = col_8bpp;
						else
							nxt_state = bw_8bpp;
					2'b01:
						nxt_state = col_16bpp_a;
					2'b10:
						nxt_state = col_24bpp;
					2'b11:
						nxt_state = col_32bpp;
				endcase
			bw_8bpp:
				if (!rgb_fifo_full && !(|colcnt) )
					if (!vdat_buffer_empty)
						nxt_state = fill_buf;
					else
						nxt_state = idle;
			col_8bpp:
				if (!(|colcnt))
					if (!vdat_buffer_empty && !rgb_fifo_full)
						nxt_state = fill_buf;
					else
						nxt_state = idle;
			col_16bpp_a:
				if (!rgb_fifo_full)
					nxt_state = col_16bpp_b;
			col_16bpp_b:
				if (!rgb_fifo_full)
					if (!vdat_buffer_empty)
						nxt_state = fill_buf;
					else
						nxt_state = idle;
			col_24bpp:
				if (!rgb_fifo_full)
					if (colcnt == 2'h1) 
						nxt_state = col_24bpp; 
					else if (!vdat_buffer_empty)
						nxt_state = fill_buf;
					else
						nxt_state = idle;
			col_32bpp:
				if (!rgb_fifo_full)
					if (!vdat_buffer_empty)
						nxt_state = fill_buf;
					else
						nxt_state = idle;
		endcase
	end 
	always @(posedge clk)
			if (srst)
				c_state <= #1 idle;
			else
				c_state <= #1 nxt_state;
	reg iclut_req;
	reg ivdat_buf_rreq;
	reg [7:0] iR, iG, iB, iRa, iGa, iBa;
	always @(c_state or vdat_buffer_empty or colcnt or DataBuffer or rgb_fifo_full or clut_ack or clut_q or Ba or Ga or Ra)
	begin : output_decoder
		ivdat_buf_rreq = 1'b0;
		RGBbuf_wreq = 1'b0;
		iclut_req = 1'b0;
		iR  = 'h0;
		iG  = 'h0;
		iB  = 'h0;
		iRa = 'h0;
		iGa = 'h0;
		iBa = 'h0;
		case (c_state) 
			idle:
				begin
					if (!rgb_fifo_full)
						if (!vdat_buffer_empty)
							ivdat_buf_rreq = 1'b1;
					RGBbuf_wreq = clut_ack;
					iR = clut_q[23:16];
					iG = clut_q[15: 8];
					iB = clut_q[ 7: 0];
				end
			fill_buf:
				begin
					RGBbuf_wreq = clut_ack;
					iR = clut_q[23:16];
					iG = clut_q[15: 8];
					iB = clut_q[ 7: 0];
				end
			bw_8bpp:
			begin
				if (!rgb_fifo_full)
					begin
						RGBbuf_wreq = 1'b1;
						if ( (!vdat_buffer_empty) && !(|colcnt) )
							ivdat_buf_rreq = 1'b1;
					end
				case (colcnt) 
					2'b11:
					begin
						iR = DataBuffer[31:24];
						iG = DataBuffer[31:24];
						iB = DataBuffer[31:24];
					end
					2'b10:
					begin
						iR = DataBuffer[23:16];
						iG = DataBuffer[23:16];
						iB = DataBuffer[23:16];
					end
					2'b01:
					begin
						iR = DataBuffer[15:8];
						iG = DataBuffer[15:8];
						iB = DataBuffer[15:8];
					end
					default:
					begin
						iR = DataBuffer[7:0];
						iG = DataBuffer[7:0];
						iB = DataBuffer[7:0];
					end
				endcase
			end
			col_8bpp:
			begin
				if (!(|colcnt))
					if (!vdat_buffer_empty && !rgb_fifo_full)
						ivdat_buf_rreq = 1'b1;
				RGBbuf_wreq = clut_ack;
				iR = clut_q[23:16];
				iG = clut_q[15: 8];
				iB = clut_q[ 7: 0];
				iclut_req = !rgb_fifo_full || (colcnt[1] ^ colcnt[0]);
			end
			col_16bpp_a:
			begin
				if (!rgb_fifo_full)
					RGBbuf_wreq = 1'b1;
				iR[7:3] = DataBuffer[31:27];
				iG[7:2] = DataBuffer[26:21];
				iB[7:3] = DataBuffer[20:16];
			end
			col_16bpp_b:
			begin
				if (!rgb_fifo_full)
					begin
						RGBbuf_wreq = 1'b1;
						if (!vdat_buffer_empty)
							ivdat_buf_rreq = 1'b1;
					end
				iR[7:3] = DataBuffer[15:11];
				iG[7:2] = DataBuffer[10: 5];
				iB[7:3] = DataBuffer[ 4: 0];
			end
			col_24bpp:
			begin
				if (!rgb_fifo_full)
					begin
						RGBbuf_wreq = 1'b1;
						if ( (colcnt != 2'h1) && !vdat_buffer_empty)
							ivdat_buf_rreq = 1'b1;
					end
				case (colcnt) 
					2'b11:
					begin
						iR  = DataBuffer[31:24];
						iG  = DataBuffer[23:16];
						iB  = DataBuffer[15: 8];
						iRa = DataBuffer[ 7: 0];
					end
					2'b10:
					begin
						iR  = Ra;
						iG  = DataBuffer[31:24];
						iB  = DataBuffer[23:16];
						iRa = DataBuffer[15: 8];
						iGa = DataBuffer[ 7: 0];
					end
					2'b01:
					begin
						iR  = Ra;
						iG  = Ga;
						iB  = DataBuffer[31:24];
						iRa = DataBuffer[23:16];
						iGa = DataBuffer[15: 8];
						iBa = DataBuffer[ 7: 0];
					end
					default:
					begin
						iR = Ra;
						iG = Ga;
						iB = Ba;
					end
				endcase
			end
			col_32bpp:
			begin
				if (!rgb_fifo_full)
					begin
						RGBbuf_wreq = 1'b1;
						if (!vdat_buffer_empty)
							ivdat_buf_rreq = 1'b1;
					end
				iR[7:0] = DataBuffer[23:16];
				iG[7:0] = DataBuffer[15:8];
				iB[7:0] = DataBuffer[7:0];
			end
		endcase
	end 
	always @(posedge clk)
		begin
			r  <= #1 iR;
			g  <= #1 iG;
			b  <= #1 iB;
			if (RGBbuf_wreq)
				begin
					Ra <= #1 iRa;
					Ba <= #1 iBa;
					Ga <= #1 iGa;
				end
			if (srst)
				begin
					vdat_buffer_rreq <= #1 1'b0;
					rgb_fifo_wreq <= #1 1'b0;
					clut_req <= #1 1'b0;
				end
			else
				begin
					vdat_buffer_rreq <= #1 ivdat_buf_rreq;
					rgb_fifo_wreq <= #1 RGBbuf_wreq;
					clut_req <= #1 iclut_req;
				end
	end
	always @(colcnt or DataBuffer)
	  case (colcnt) 
	      2'b11: clut_offs = DataBuffer[31:24];
	      2'b10: clut_offs = DataBuffer[23:16];
	      2'b01: clut_offs = DataBuffer[15: 8];
	      2'b00: clut_offs = DataBuffer[ 7: 0];
	  endcase
	always @(posedge clk)
	  if (srst)
	    colcnt <= #1 2'b11;
	  else if (RGBbuf_wreq)
	    colcnt <= #1 colcnt -2'h1;
endmodule
