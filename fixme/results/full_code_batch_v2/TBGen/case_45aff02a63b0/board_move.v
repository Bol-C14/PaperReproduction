`timescale 1ns/1ps

module board_move(clk, B, R, X, Y, player, MB, MR, RST);
input [63:0] R;
input [63:0] B;
input clk;
input RST;
input [2:0]  X;
input [2:0]  Y;
input player;
output [63:0] MB;
output [63:0] MR;
reg [63:0] oponent_ff_d;
reg [63:0] current_ff_d;
reg [63:0] oponent_ff_q;
reg [63:0] current_ff_q;
reg [2:0] countx_ff_d;
reg [2:0] countx_ff_q;
reg [2:0] county_ff_d;
reg [2:0] county_ff_q;
reg [2:0] count2x_ff_d;
reg [2:0] count2x_ff_q;
reg [2:0] count2y_ff_d;
reg [2:0] count2y_ff_q;
reg [1:0] state_ff_q;
reg [1:0] state_ff_d;
reg [1:0] state2_ff_q;
reg [1:0] state2_ff_d;
parameter RESET  = 2'b00;
parameter FLIP   = 2'b01;
parameter WRONG  = 2'b10;
parameter FINISH = 2'b11;
parameter DISC_ON  = 1'b1;
parameter DISC_OFF = 1'b0;
parameter LIMIT    = 3'd7;
parameter NO_DISC  = 1'b0;
parameter RED		 = 1'b1;
always @(state_ff_q or countx_ff_q or county_ff_q)
   begin
		oponent_ff_d = oponent_ff_q;
		current_ff_d = current_ff_q;
		case (state_ff_q)			
			FLIP: begin
						oponent_ff_d[county_ff_q*8 + countx_ff_q] = DISC_OFF;
						current_ff_d[county_ff_q*8 + countx_ff_q] = DISC_ON;
					end
			WRONG: begin
						oponent_ff_d[county_ff_q*8 + countx_ff_q] = DISC_ON;
						current_ff_d[county_ff_q*8 + countx_ff_q] = DISC_OFF;
					 end
			default: begin
							oponent_ff_d = oponent_ff_q;
							current_ff_d = current_ff_q;
						end
		endcase
		case (state2_ff_q)			
			FLIP: begin
						oponent_ff_d[count2y_ff_q*8 + count2x_ff_q] = DISC_OFF;
						current_ff_d[count2y_ff_q*8 + count2x_ff_q] = DISC_ON;
					end
			WRONG: begin
						oponent_ff_d[count2y_ff_q*8 + count2x_ff_q] = DISC_ON;
						current_ff_d[count2y_ff_q*8 + count2x_ff_q] = DISC_OFF;
					 end
			default: begin
							oponent_ff_d = oponent_ff_q;
							current_ff_d = current_ff_q;
						end
		endcase
	end
always @(state_ff_q or countx_ff_q or county_ff_q)
begin
case (state_ff_q)
	 RESET: begin
			     if ( (oponent_ff_q[county_ff_q*8 + countx_ff_q] | current_ff_q[county_ff_q*8 + countx_ff_q]) == NO_DISC )
				  begin
						if ( countx_ff_q == LIMIT )
						begin	
							state_ff_d = FINISH;
							countx_ff_d = countx_ff_q;
							county_ff_d = county_ff_q;
						end
						else begin
							if ( oponent_ff_q[county_ff_q*8 + countx_ff_q + 1] == DISC_ON )
							begin
								state_ff_d = FLIP;	
								countx_ff_d = countx_ff_q + 1;
								county_ff_d = county_ff_q;								
							end
							else begin
								state_ff_d = FINISH;
								countx_ff_d = countx_ff_q;
								county_ff_d = county_ff_q;
							end
						end
				  end
				  else begin
						state_ff_d = RESET;
						countx_ff_d = countx_ff_q;
						county_ff_d = county_ff_q;
				  end
			  end
    FLIP: begin
				 if (countx_ff_q == LIMIT) begin
							state_ff_d = WRONG;
							countx_ff_d = countx_ff_q;
							county_ff_d = county_ff_q;
				 end
             else begin
	 				if ( oponent_ff_q[county_ff_q*8 + countx_ff_q + 1] == DISC_ON ) 
					begin
						state_ff_d = state_ff_q;						
						countx_ff_d = countx_ff_q + 1;
						county_ff_d = county_ff_q;						
					end
					else begin
						if ( current_ff_q[county_ff_q*8 + countx_ff_q + 1] == DISC_ON )
						begin
							state_ff_d = FINISH;
							countx_ff_d = countx_ff_q;
							county_ff_d = county_ff_q;							
						end
						else begin
							state_ff_d = WRONG;
							countx_ff_d = countx_ff_q;
							county_ff_d = county_ff_q;							
						end
					end
				 end	
			  end
	 WRONG:
			 begin
				if (countx_ff_q - 1  == X)
				begin
					state_ff_d = FINISH;
					countx_ff_d = countx_ff_q;
					county_ff_d = county_ff_q;					
				end
				else begin
				   state_ff_d = WRONG;
					countx_ff_d = countx_ff_q - 1;
					county_ff_d = county_ff_q;					
				end
			 end
	 default:
	     begin
			state_ff_d = state_ff_q;
			countx_ff_d = countx_ff_q;
			county_ff_d = county_ff_q;
		  end
endcase
end
always @(state2_ff_q or count2x_ff_q or count2y_ff_q)
begin
case (state2_ff_q)
	 RESET: begin
			     if ( (oponent_ff_q[count2y_ff_q*8 + count2x_ff_q] | current_ff_q[count2y_ff_q*8 + count2x_ff_q]) == NO_DISC )
				  begin
						if ( count2x_ff_q == LIMIT )
						begin	
							state2_ff_d = FINISH;
							count2x_ff_d = count2x_ff_q;
							count2y_ff_d = count2y_ff_q;
						end
						else begin
							if ( oponent_ff_q[count2y_ff_q*8 + count2x_ff_q - 1] == DISC_ON )
							begin
								state2_ff_d = FLIP;	
								count2x_ff_d = count2x_ff_q - 1;
								count2y_ff_d = count2y_ff_q;								
							end
							else begin
								state2_ff_d = FINISH;
								count2x_ff_d = count2x_ff_q;
								count2y_ff_d = count2y_ff_q;
							end
						end
				  end
				  else begin
						state2_ff_d = RESET;
						count2x_ff_d = count2x_ff_q;
						count2y_ff_d = count2y_ff_q;
				  end
			  end
    FLIP: begin
				 if (count2x_ff_q == 3'b0) begin
							state2_ff_d = WRONG;
							count2x_ff_d = count2x_ff_q;
							count2y_ff_d = count2y_ff_q;
				 end
             else begin
	 				if ( oponent_ff_q[count2y_ff_q*8 + count2x_ff_q - 1] == DISC_ON ) 
					begin
						state2_ff_d = state2_ff_q;						
						count2x_ff_d = count2x_ff_q + 1;
						count2y_ff_d = count2y_ff_q;						
					end
					else begin
						if ( current_ff_q[count2y_ff_q*8 + count2x_ff_q - 1] == DISC_ON )
						begin
							state2_ff_d = FINISH;
							count2x_ff_d = count2x_ff_q;
							count2y_ff_d = count2y_ff_q;							
						end
						else begin
							state2_ff_d = WRONG;
							count2x_ff_d = count2x_ff_q;
							count2y_ff_d = count2y_ff_q;							
						end
					end
				 end	
			  end
	 WRONG:
			 begin
				if (count2x_ff_q + 1  == X)
				begin
					state2_ff_d = FINISH;
					count2x_ff_d = count2x_ff_q;
					count2y_ff_d = count2y_ff_q;					
				end
				else begin
				   state2_ff_d = WRONG;
					count2x_ff_d = count2x_ff_q + 1;
					count2y_ff_d = count2y_ff_q;					
				end
			 end
	 default:
	     begin
			state2_ff_d = state2_ff_q;
			count2x_ff_d = count2x_ff_q;
			count2y_ff_d = count2y_ff_q;
		  end
endcase
end
always @(posedge clk)
begin
	if (RST)
	begin
 		 state_ff_q <= RESET;
		 state2_ff_q <= RESET;
		 current_ff_q <= B;
		 oponent_ff_q <= R;
		 if ( player == RED ) begin
			 current_ff_q <= R;
			 oponent_ff_q <= B;
		 end
		countx_ff_q <= X;
		county_ff_q <= Y;		
		count2x_ff_q <= X;
		count2y_ff_q <= Y;		
	end
	else begin
		state_ff_q  <= state_ff_d;
		countx_ff_q <= countx_ff_d;
		county_ff_q <= county_ff_d;		
		state2_ff_q  <= state2_ff_d;
		count2x_ff_q <= count2x_ff_d;
		count2y_ff_q <= count2y_ff_d;		
		oponent_ff_q <= oponent_ff_d;
		current_ff_q <= current_ff_d;
	end
end
assign MB = current_ff_q;
assign MR = oponent_ff_q;
endmodule
