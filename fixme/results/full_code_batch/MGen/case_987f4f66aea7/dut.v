`timescale 1ns/1ps
 
module top(i_clk, i_ce, i_trigger, i_data,
	i_wb_clk, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data,
	o_wb_ack, o_wb_stall, o_wb_data,
	o_interrupt);
	parameter	LGMEM = 5'd10, BUSW = 32, SYNCHRONOUS=1;
	input				i_clk, i_ce, i_trigger;
	input		[(BUSW-1):0]	i_data;
	input				i_wb_clk, i_wb_cyc, i_wb_stb, i_wb_we;
	input				i_wb_addr; 
	input		[(BUSW-1):0]	i_wb_data;
	output	wire			o_wb_ack, o_wb_stall;
	output	reg	[(BUSW-1):0]	o_wb_data;
	output	wire			o_interrupt;
	reg	[(LGMEM-1):0]	raddr;
	reg	[(BUSW-1):0]	mem[0:((1<<LGMEM)-1)];
	wire		bw_reset_request, bw_manual_trigger,
			bw_disable_trigger, bw_reset_complete;
	reg	[22:0]	br_config;
	wire	[19:0]	bw_holdoff;
	initial	br_config = ((1<<(LGMEM-1))-4);
	always @(posedge i_wb_clk)
		if ((i_wb_stb)&&(~i_wb_addr))
		begin
			if (i_wb_we)
				br_config <= { i_wb_data[31],
					(i_wb_data[27]), 
					i_wb_data[26],
					i_wb_data[19:0] };
		end else if (bw_reset_complete)
			br_config[22] <= 1'b1;
	assign	bw_reset_request   = (~br_config[22]);
	assign	bw_manual_trigger  = (br_config[21]);
	assign	bw_disable_trigger = (br_config[20]);
	assign	bw_holdoff         = br_config[19:0];
	wire	dw_reset, dw_manual_trigger, dw_disable_trigger;
	generate
	if (SYNCHRONOUS > 0)
	begin
		assign	dw_reset = bw_reset_request;
		assign	dw_manual_trigger = bw_manual_trigger;
		assign	dw_disable_trigger = bw_disable_trigger;
		assign	bw_reset_complete = bw_reset_request;
	end else begin
		reg		r_reset_complete;
		reg	[2:0]	r_iflags, q_iflags;
		initial	q_iflags = 3'b000;
		initial	r_reset_complete = 1'b0;
		always @(posedge i_clk)
		begin
			q_iflags <= { bw_reset_request, bw_manual_trigger, bw_disable_trigger };
			r_iflags <= q_iflags;
			r_reset_complete <= (dw_reset);
		end
		assign	dw_reset = r_iflags[2];
		assign	dw_manual_trigger = r_iflags[1];
		assign	dw_disable_trigger = r_iflags[0];
		reg	q_reset_complete, qq_reset_complete;
		initial	q_reset_complete = 1'b0;
		initial	qq_reset_complete = 1'b0;
		always @(posedge i_wb_clk)
		begin
			q_reset_complete  <= r_reset_complete;
			qq_reset_complete <= q_reset_complete;
		end
		assign bw_reset_complete = qq_reset_complete;
	end endgenerate
	reg	dr_triggered, dr_primed;
	wire	dw_trigger;
	assign	dw_trigger = (dr_primed)&&(
				((i_trigger)&&(~dw_disable_trigger))
				||(dr_triggered)
				||(dw_manual_trigger));
	initial	dr_triggered = 1'b0;
	always @(posedge i_clk)
		if (dw_reset)
			dr_triggered <= 1'b0;
		else if ((i_ce)&&(dw_trigger))
			dr_triggered <= 1'b1;
	reg		dr_stopped;
	reg	[19:0]	counter;	
	initial	dr_stopped = 1'b0;
	initial	counter = 20'h0000;
	always @(posedge i_clk)
		if (dw_reset)
			counter <= 0;
		else if ((i_ce)&&(dr_triggered)&&(~dr_stopped))
		begin 
			counter <= counter + 20'h01;
		end
	always @(posedge i_clk)
		if ((~dr_triggered)||(dw_reset))
			dr_stopped <= 1'b0;
		else if (i_ce)
			dr_stopped <= (counter+20'd1 >= bw_holdoff);
		else
			dr_stopped <= (counter >= bw_holdoff);
	reg	[(LGMEM-1):0]	waddr;
	initial	waddr = {(LGMEM){1'b0}};
	initial	dr_primed = 1'b0;
	always @(posedge i_clk)
		if (dw_reset) 
		begin
			waddr <= 0; 
			dr_primed <= 1'b0;
		end else if ((i_ce)&&((~dr_triggered)||(~dr_stopped)))
		begin
			waddr <= waddr + {{(LGMEM-1){1'b0}},1'b1};
			dr_primed <= (dr_primed)||(&waddr);
		end
	always @(posedge i_clk)
		if ((i_ce)&&((~dr_triggered)||(~dr_stopped)))
			mem[waddr] <= i_data;
	wire	bw_stopped, bw_triggered, bw_primed;
	generate
	if (SYNCHRONOUS > 0)
	begin
		assign	bw_stopped   = dr_stopped;
		assign	bw_triggered = dr_triggered;
		assign	bw_primed    = dr_primed;
	end else begin
		reg	[2:0]	q_oflags, r_oflags;
		initial	q_oflags = 3'h0;
		initial	r_oflags = 3'h0;
		always @(posedge i_wb_clk)
			if (bw_reset_request)
			begin
				q_oflags <= 3'h0;
				r_oflags <= 3'h0;
			end else begin
				q_oflags <= { dr_stopped, dr_triggered, dr_primed };
				r_oflags <= q_oflags;
			end
		assign	bw_stopped   = r_oflags[2];
		assign	bw_triggered = r_oflags[1];
		assign	bw_primed    = r_oflags[0];
	end endgenerate
	reg	br_wb_ack;
	initial	br_wb_ack = 1'b0;
	wire	bw_cyc_stb;
	assign	bw_cyc_stb = (i_wb_stb);
	always @(posedge i_wb_clk)
	begin
		if ((bw_reset_request)
			||((bw_cyc_stb)&&(i_wb_addr)&&(i_wb_we)))
			raddr <= 0;
		else if ((bw_cyc_stb)&&(i_wb_addr)&&(~i_wb_we)&&(bw_stopped))
			raddr <= raddr + {{(LGMEM-1){1'b0}},1'b1}; 
		if ((bw_cyc_stb)&&(~i_wb_we))
		begin 
			br_wb_ack <= 1'b1;
		end else if ((bw_cyc_stb)&&(i_wb_we))
			br_wb_ack <= 1'b1;
		else 
			br_wb_ack <= 1'b0;
	end
	reg	[31:0]	nxt_mem;
	always @(posedge i_wb_clk)
		nxt_mem <= mem[raddr+waddr+
			(((bw_cyc_stb)&&(i_wb_addr)&&(~i_wb_we)) ?
				{{(LGMEM-1){1'b0}},1'b1} : { (LGMEM){1'b0}} )];
	wire	[4:0]	bw_lgmem;
	assign		bw_lgmem = LGMEM;
	always @(posedge i_wb_clk)
		if (~i_wb_addr) 
			o_wb_data <= { bw_reset_request,
					bw_stopped,
					bw_triggered,
					bw_primed,
					bw_manual_trigger,
					bw_disable_trigger,
					(raddr == {(LGMEM){1'b0}}),
					bw_lgmem,
					bw_holdoff  };
		else if (~bw_stopped) 
			o_wb_data <= i_data;
		else 
			o_wb_data <= nxt_mem; 
	assign	o_wb_stall = 1'b0;
	assign	o_wb_ack = (i_wb_cyc)&&(br_wb_ack);
	reg	br_level_interrupt;
	initial	br_level_interrupt = 1'b0;
	assign	o_interrupt = (bw_stopped)&&(~bw_disable_trigger)
					&&(~br_level_interrupt);
	always @(posedge i_wb_clk)
		if ((bw_reset_complete)||(bw_reset_request))
			br_level_interrupt<= 1'b0;
		else
			br_level_interrupt<= (bw_stopped)&&(~bw_disable_trigger);
endmodule

