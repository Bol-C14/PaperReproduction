`timescale 1ns/1ps
 

module	prefetch_ref(i_clk, i_rst, i_ce, i_stalled_n, i_pc, i_aux,
			o_i_ref, o_pc_ref, o_aux_ref, o_valid_ref, o_illegal_ref,
		o_wb_cyc_ref, o_wb_stb_ref, o_wb_we_ref, o_wb_addr_ref, o_wb_data_ref,
			i_wb_ack, i_wb_stall, i_wb_err, i_wb_data);
	parameter		ADDRESS_WIDTH=32, AUX_WIDTH = 1, AW=ADDRESS_WIDTH;
	input				i_clk, i_rst, i_ce, i_stalled_n;
	input		[(AW-1):0]	i_pc;
	input	[(AUX_WIDTH-1):0]	i_aux;
	output	reg	[31:0]		o_i_ref;
	output	reg	[(AW-1):0]	o_pc_ref;
	output	reg [(AUX_WIDTH-1):0]	o_aux_ref;
	output	reg			o_valid_ref, o_illegal_ref;
	output	reg			o_wb_cyc_ref, o_wb_stb_ref;
	output	wire			o_wb_we_ref;
	output	reg	[(AW-1):0]	o_wb_addr_ref;
	output	wire	[31:0]		o_wb_data_ref;
	input			i_wb_ack, i_wb_stall, i_wb_err;
	input		[31:0]	i_wb_data;
	assign	o_wb_we_ref = 1'b0;
	assign	o_wb_data_ref = 32'h0000;
	initial	o_wb_cyc_ref = 1'b0;
	initial	o_wb_stb_ref = 1'b0;
	initial	o_wb_addr_ref= 0;
	always @(posedge i_clk)
		if ((i_rst)||(i_wb_ack))
		begin
			o_wb_cyc_ref <= 1'b0;
			o_wb_stb_ref <= 1'b0;
		end else if ((i_ce)&&(~o_wb_cyc_ref)) 
		begin
			o_wb_cyc_ref <= 1'b1;
			o_wb_stb_ref <= 1'b1;
		end else if (o_wb_cyc_ref) 
		begin
			if ((o_wb_cyc_ref)&&(o_wb_stb_ref)&&(~i_wb_stall))
				o_wb_stb_ref <= 1'b0;
			if (i_wb_ack)
				o_wb_cyc_ref <= 1'b0;
		end
	always @(posedge i_clk)
		if (i_rst) 
			o_wb_addr_ref <= {(AW){1'b1}};
		else if ((i_ce)&&(~o_wb_cyc_ref))
			o_wb_addr_ref <= i_pc;
	always @(posedge i_clk)
		if ((o_wb_cyc_ref)&&(i_wb_ack))
			o_aux_ref <= i_aux;
	always @(posedge i_clk)
		if ((o_wb_cyc_ref)&&(i_wb_ack))
			o_i_ref <= i_wb_data;
	always @(posedge i_clk)
		if ((o_wb_cyc_ref)&&(i_wb_ack))
			o_pc_ref <= o_wb_addr_ref;
	initial o_valid_ref   = 1'b0;
	initial o_illegal_ref = 1'b0;
	always @(posedge i_clk)
		if ((o_wb_cyc_ref)&&(i_wb_ack))
		begin
			o_valid_ref <= (i_pc == o_wb_addr_ref)&&(~i_wb_err);
			o_illegal_ref <= i_wb_err;
		end else if (i_stalled_n)
		begin
			o_valid_ref <= 1'b0;
			o_illegal_ref <= 1'b0;
		end
endmodule

