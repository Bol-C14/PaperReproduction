 `timescale 1ns/1ns
 
module FSM_ref (
	input clk,
	input rst_n,
	input [3:0] in_m,
	output reg goods_ref,
	output reg [3:0] out_m_ref
);
 
reg [4:0] CS, NS;
 
parameter [4:0]
	IDLE = 'b00001,
	S0   = 'b00010,
	S1   = 'b00100,
	S2   = 'b01000,
	S3   = 'b10000;
//第一always块，同步时序逻辑
always @ (posedge clk or negedge rst_n) begin
	if (!rst_n)
		CS <= IDLE;
	else
		CS <= NS;
end
//第二always块，组合逻辑
always @ (*) begin
	case (CS)
		IDLE:
			if (in_m == 4'd1)		NS = S0;
			else if (in_m == 4'd2)	NS = S1;
			else if (in_m == 4'd5)	NS = IDLE;
			else					NS = IDLE;
		
		S0:
			if (in_m == 4'd1)		NS = S1;
			else if (in_m == 4'd2)	NS = S2;
			else if (in_m == 4'd5)	NS = IDLE;
			else					NS = S0;
		
		S1:
			if (in_m == 4'd1)		NS = S2;
			else if (in_m == 4'd2)	NS = S3;
			else if (in_m == 4'd5)	NS = IDLE;
			else					NS = S1;
		
		S2:
			if (in_m == 4'd1)		NS = S3;
			else if (in_m == 4'd2)	NS = IDLE;
			else if (in_m == 4'd5)	NS = IDLE;
			else					NS = S2;
		
		S3:
			if (in_m == 4'd1)		NS = IDLE;
			else if (in_m == 4'd2)	NS = IDLE;
			else if (in_m == 4'd5)	NS = IDLE;
			else					NS = S3;
	
		default:
			NS = IDLE;
	endcase
end
 
//第三always块，同步时序逻辑
always @ (posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		out_m_ref <= 'd0;
		goods_ref <= 'd0;
	end
	else begin
		case (CS)
			IDLE: begin
				out_m_ref <= 'd0;
				if (in_m == 'd5)    goods_ref <= 'd1;
				else                goods_ref<= 'd0;
			end
			
			S0: begin
				out_m_ref <= 'd0;
				if (in_m == 'd1 || in_m == 'd2) begin
					goods_ref <= 'd0;
					out_m_ref <= 'd0;
				end
				else begin
					goods_ref <= 'd1;
					out_m_ref <= 'd1;
				end
			end
			
			S1: begin
				out_m_ref <= 'd0;
				if (in_m == 'd1 || in_m == 'd2) begin
					goods_ref <= 'd0;
					out_m_ref <= 'd0;
				end
				else begin
					goods_ref <= 'd1;
					out_m_ref <= 'd2;
				end
			end
				
			S2: begin
				out_m_ref <= 'd0;
				if (in_m == 'd1) begin
					goods_ref <= 'd0;
					out_m_ref <= 'd0;
				end
				else if (in_m == 'd2) begin
					goods_ref <= 'd1;
					out_m_ref <= 'd0;
				end
				else begin
					goods_ref <= 'd1;
					out_m_ref <= 'd3;
				end
			end
			
			S3: begin
				goods_ref <= 'd1;
				if (in_m == 'd1)		out_m_ref <= 'd0;
				else if (in_m == 'd2)	out_m_ref <= 'd1;
				else					out_m_ref <= 'd4;
			end
			
			default: begin
				goods_ref <= 'd1;
				out_m_ref <= 'd0;
			end
		endcase
	end
end
endmodule
