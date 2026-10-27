`timescale 1ns/1ps
module oracle_pipemem(i_clk, i_rst, i_pipe_stb, i_lock,
		i_op, i_addr, i_data, i_oreg,
			o_busy, o_pipe_stalled, o_valid, o_err, o_wreg, o_result,
		o_wb_cyc_gbl, o_wb_cyc_lcl,
			o_wb_stb_gbl, o_wb_stb_lcl,
			o_wb_we, o_wb_addr, o_wb_data,
		i_wb_ack, i_wb_stall, i_wb_err, i_wb_data);
	parameter	ADDRESS_WIDTH=32, IMPLEMENT_LOCK=0;
	localparam	AW=ADDRESS_WIDTH;
	input			i_clk, i_rst;
	input			i_pipe_stb, i_lock;
	input			i_op;
	input		[31:0]	i_addr;
	input		[31:0]	i_data;
	input		[4:0]	i_oreg;
	output	wire		o_busy;
	output	wire		o_pipe_stalled;
	output	reg		o_valid;
	output	reg		o_err;
	output	reg	[4:0]	o_wreg;
	output	reg	[31:0]	o_result;
	output	wire		o_wb_cyc_gbl;
	output	reg		o_wb_stb_gbl;
	output	wire		o_wb_cyc_lcl;
	output	reg		o_wb_stb_lcl, o_wb_we;
	output	reg	[(AW-1):0]	o_wb_addr;
	output	reg	[31:0]	o_wb_data;
	input			i_wb_ack, i_wb_stall, i_wb_err;
	input		[31:0]	i_wb_data;
	reg	cyc;
	reg			r_wb_cyc_gbl, r_wb_cyc_lcl;
	reg	[3:0]		rdaddr, wraddr;
	wire	[3:0]		nxt_rdaddr;
	reg	[(5-1):0]	fifo_oreg [0:15];
	initial	rdaddr = 0;
	initial	wraddr = 0;
	always @(posedge i_clk)
		fifo_oreg[wraddr] <= i_oreg;
	always @(posedge i_clk)
		if ((i_rst)||(i_wb_err))
			wraddr <= 0;
		else if (i_pipe_stb)
			wraddr <= wraddr + 4'h1;
	always @(posedge i_clk)
		if ((i_rst)||(i_wb_err))
			rdaddr <= 0;
		else if ((i_wb_ack)&&(cyc))
			rdaddr <= rdaddr + 4'h1;
	assign	nxt_rdaddr = rdaddr + 4'h1;
	wire	gbl_stb, lcl_stb;
	assign	lcl_stb = (i_addr[31:8]==24'hc00000)&&(i_addr[7:5]==3'h0);
	assign	gbl_stb = (~lcl_stb);
	initial	cyc = 0;
	initial	r_wb_cyc_lcl = 0;
	initial	r_wb_cyc_gbl = 0;
	always @(posedge i_clk)
		if (i_rst)
		begin
			r_wb_cyc_gbl <= 1'b0;
			r_wb_cyc_lcl <= 1'b0;
			o_wb_stb_gbl <= 1'b0;
			o_wb_stb_lcl <= 1'b0;
			cyc <= 1'b0;
		end else if (cyc)
		begin
			if ((~i_wb_stall)&&(~i_pipe_stb))
			begin
				o_wb_stb_gbl <= 1'b0;
				o_wb_stb_lcl <= 1'b0;
			end
			if (((i_wb_ack)&&(nxt_rdaddr == wraddr))||(i_wb_err))
			begin
				r_wb_cyc_gbl <= 1'b0;
				r_wb_cyc_lcl <= 1'b0;
				cyc <= 1'b0;
			end
		end else if (i_pipe_stb) 
		begin 
			r_wb_cyc_lcl <= lcl_stb;
			r_wb_cyc_gbl <= gbl_stb;
			o_wb_stb_lcl <= lcl_stb;
			o_wb_stb_gbl <= gbl_stb;
			cyc <= 1'b1;
		end
	always @(posedge i_clk)
		if ((cyc)&&(i_pipe_stb)&&(~i_wb_stall))
		begin
			o_wb_addr <= i_addr[(AW-1):0];
			o_wb_data <= i_data;
		end else if ((~cyc)&&(i_pipe_stb))
		begin
			o_wb_addr <= i_addr[(AW-1):0];
			o_wb_data <= i_data;
		end
	always @(posedge i_clk)
		if ((i_pipe_stb)&&(~cyc))
			o_wb_we   <= i_op;
	initial	o_valid = 1'b0;
	always @(posedge i_clk)
		o_valid <= (cyc)&&(i_wb_ack)&&(~o_wb_we);
	initial	o_err = 1'b0;
	always @(posedge i_clk)
		o_err <= (cyc)&&(i_wb_err);
	assign	o_busy = cyc;
	always @(posedge i_clk)
		o_wreg <= fifo_oreg[rdaddr];
	always @(posedge i_clk)
		o_result <= i_wb_data;
	assign	o_pipe_stalled = (cyc)
			&&((i_wb_stall)||((~o_wb_stb_lcl)&&(~o_wb_stb_gbl)));
	generate
	if (IMPLEMENT_LOCK != 0)
	begin
		reg	lock_gbl, lock_lcl;
		initial	lock_gbl = 1'b0;
		initial	lock_lcl = 1'b0;
		always @(posedge i_clk)
		begin
			lock_gbl <= (i_lock)&&((r_wb_cyc_gbl)||(lock_gbl));
			lock_lcl <= (i_lock)&&((r_wb_cyc_lcl)||(lock_gbl));
		end
		assign	o_wb_cyc_gbl = (r_wb_cyc_gbl)||(lock_gbl);
		assign	o_wb_cyc_lcl = (r_wb_cyc_lcl)||(lock_lcl);
	end else begin
		assign	o_wb_cyc_gbl = (r_wb_cyc_gbl);
		assign	o_wb_cyc_lcl = (r_wb_cyc_lcl);
	end endgenerate
endmodule