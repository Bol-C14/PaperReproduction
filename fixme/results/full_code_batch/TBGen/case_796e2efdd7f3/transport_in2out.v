`timescale 1ns/1ps

module transport_in2out
(
input clk, 
input reset, 
input S_Ready, 
output reg RE,WE,  
output reg [7:0] RdAdd,WrAdd,
output reg Wr_done
);
reg cnt;
reg state;  
always@(posedge clk or posedge reset)
begin
	if(reset)
		begin
			WE<=0;
			RE<=0;
			RdAdd<=0;
			WrAdd<=0;
			Wr_done<=0;
			state<=0;
			cnt<=0;
		end
	else
		begin
			case(state)
			1:begin    
				cnt<=~cnt;
				if(cnt)
					begin
						WrAdd<=WrAdd+1;
						if(WrAdd == 186)
							begin
								state<=0;
								Wr_done<=1;
							end
					end
				else
					begin
						RdAdd<=RdAdd-1;
					end
			end
			default:begin    
				Wr_done<=0;
				if(S_Ready)
					begin
						state<=1;
						RE<=~RE;
						WE<=~WE;
						RdAdd<= 204;
						WrAdd<= 255;
						cnt<=0;
					end
			end
			endcase
		end
end
endmodule
