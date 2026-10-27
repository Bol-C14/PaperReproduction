`timescale 1ns/1ps

module PIC_8259(
    input CS,
	 input WR,
	 input [7:0]din,
	 output OE,
	 output wire [7:0]dout,
	 output reg [7:0]ivect,
	 input clk,		
	 output reg INT = 0,
	 input IACK,
	 input [3:0]I	
    );
	reg [3:0]ss_I = 0;
	reg [3:0]s_I = 0;
	reg [3:0]IMR = 4'b1111;
	reg [3:0]IRR = 0;
	assign dout = ~({3'b000, IMR[3:2], 1'b0, IMR[1:0]});
	assign OE = CS & ~WR;
	always @ (posedge clk) begin
		ss_I <= I;
		s_I <= ss_I;
		IRR <= (IRR | (~s_I & ss_I)) & ~IMR;	
		if(~INT) begin
			if(IRR[0]) begin 
				INT <= 1; 
				ivect <= 8'h08;
				IRR[0] <= 0;
			end else if(IRR[1]) begin  
				INT <= 1; 
				ivect <= 8'h09; 
				IRR[1] <= 0;
			end else if(IRR[2]) begin  
				INT <= 1; 
				ivect <= 8'h70; 
				IRR[2] <= 0;
			end else if(IRR[3]) begin 
				INT <= 1; 
				ivect <= 8'h74; 
				IRR[3] <= 0;
			end	
		end else if(IACK) INT <= 0;	
		if(CS & WR) IMR <= {din[4:3], din[1:0]};
	end
always @* assert((dout) == ({3'b000, IMR[3:2], 1'b0, IMR[1:0]}));
endmodule
