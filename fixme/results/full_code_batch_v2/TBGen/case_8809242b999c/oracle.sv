`timescale 1ns/1ps
module oracle_z80memio (
	input clk,
	output [15:0] a,
	output [7:0] d,
	output mreq_n,
	output iorq_n,
	output wr_n,
	output rfsh_n
	);
	reg rmreq = 1;
	reg riorq = 1;
	reg rwr = 1;
	reg rrfsh = 1;
	assign mreq_n = rmreq;
	assign iorq_n = riorq;
	assign wr_n = rwr;
	assign rfsh_n = rrfsh;
	reg [1:0] estado = 0;
	reg [5:0] memioseq = 6'b011001;
	reg [5:0] io2seq =   5'b011000;
	reg [4:0] hiloseq =  5'b01010;
	wire memio = memioseq[0];  
	wire hilo = hiloseq[0];   
	wire iohi = io2seq[0];    
	reg [15:0] ra;
	assign a = ra;
	reg [7:0] rd;
	assign d = rd;
	reg [7:0] iodata = 0;
	reg [7:0] memdata = 0;
	reg [15:0] memaddr = 16384;
	always @(posedge clk) begin
		if (estado==2 && !memio) begin
			estado <= 0;
			memioseq <= { memioseq[0], memioseq[5:1] };
			hiloseq <= { hiloseq[0], hiloseq[4:1] };
			io2seq <= { io2seq[0], io2seq[5:1] };
			memdata <= memdata + 1;
			if (memaddr == 23295)
				memaddr <= 16384;
			else
				memaddr <= memaddr + 1;
		end
		else if (estado==3 && memio) begin
			estado <= 0;
			memioseq <= { memioseq[0], memioseq[5:1] };
			hiloseq <= { hiloseq[0], hiloseq[4:1] };
			io2seq <= { io2seq[0], io2seq[5:1] };
			iodata <= iodata + 1;
		end
		else
			estado <= estado + 1;
	end
	always @(*) begin
		if (memio) begin 
			case ({estado,clk})
				3'b001 : begin
								{rmreq,riorq,rwr} = 3'b111;
								ra = {1'b0, iohi, 13'b0000001111111, hilo};
								rd = 8'bzzzzzzzz;
							end
				3'b000 : begin
								{rmreq,riorq,rwr} = 3'b111;
								ra = {1'b0, iohi, 13'b0000001111111, hilo};
								rd = iodata;
							end
				3'b011,3'b010,3'b101,3'b100,3'b111 : 
				         begin
								{rmreq,riorq,rwr} = 3'b100;
								ra = {1'b0, iohi, 13'b0000001111111, hilo};
								rd = iodata;
							end
				3'b110 : begin
								{rmreq,riorq,rwr} = 3'b111;
								ra = {1'b0, iohi, 13'b0000001111111, hilo};
								rd = iodata;
							end
			endcase
		end
		else begin	
			case ({estado,clk})
				3'b001 : begin
								{rmreq,riorq,rwr} = 3'b111;
								ra = {hilo,memaddr[14:0]};
								rd = 8'bzzzzzzzz;
							end
				3'b000,3'b011 :
				         begin
								{rmreq,riorq,rwr} = 3'b011;
								ra = {hilo,memaddr[14:0]};
								rd = memdata;
							end
				3'b010,3'b101 :
				         begin
								{rmreq,riorq,rwr} = 3'b010;
								ra = {hilo,memaddr[14:0]};
								rd = memdata;
							end
				3'b100 : begin
								{rmreq,riorq,rwr} = 3'b111;
								ra = {hilo,memaddr[14:0]};
								rd = memdata;
							end
			endcase
		end
	end
endmodule