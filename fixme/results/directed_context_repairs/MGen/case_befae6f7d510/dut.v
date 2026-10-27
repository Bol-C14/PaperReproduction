`timescale 1ns/1ps

module top(i_data_clk, i_ce, i_trigger, i_data,
	i_wb_clk, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data,
	o_wb_ack, o_wb_stall, o_wb_data,
	o_interrupt);
	parameter [4:0]			LGMEM = 5'd10;
	parameter			BUSW = 32, NELM=(BUSW-1);
	parameter [0:0]			SYNCHRONOUS=1;
	parameter			HOLDOFFBITS=20;
	parameter [(HOLDOFFBITS-1):0]	DEFAULT_HOLDOFF = ((1<<(LGMEM-1))-4);
	parameter			STEP_BITS=BUSW-1;
	parameter [(STEP_BITS-1):0]	MAX_STEP= {(STEP_BITS){1'b1}};
	input	wire			i_data_clk, i_ce, i_trigger;
	input	wire	[(NELM-1):0]	i_data;
	input	wire			i_wb_clk, i_wb_cyc, i_wb_stb, i_wb_we;
	input	wire			i_wb_addr; 
	input	wire	[(BUSW-1):0]	i_wb_data;
	output	wire			o_wb_ack, o_wb_stall;
	output	reg	[(BUSW-1):0]	o_wb_data;
	output	wire			o_interrupt;
	reg	[(LGMEM-1):0]	raddr;
	reg	[(BUSW-1):0]	mem[0:((1<<LGMEM)-1)];
	wire		bw_reset_request, bw_manual_trigger,
			bw_disable_trigger, bw_reset_complete;
	reg	[2:0]	br_config;
	reg	[(HOLDOFFBITS-1):0]	br_holdoff;
	initial	br_config = 3'b0;
	initial	br_holdoff = DEFAULT_HOLDOFF;
	always @(posedge i_wb_clk)
		if ((i_wb_stb)&&(!i_wb_addr))
		begin
			if (i_wb_we)
			begin
				br_config <= { i_wb_data[31],
					i_wb_data[27],
					i_wb_data[26] };
				br_holdoff <= i_wb_data[(HOLDOFFBITS-1):0];
			end
		end else if (bw_reset_complete)
			br_config[2] <= 1'b1;
	assign	bw_reset_request   = (!br_config[2]);
	assign	bw_manual_trigger  = (br_config[1]);
	assign	bw_disable_trigger = (br_config[0]);
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
		(* ASYNC_REG = "TRUE" *) reg	[2:0]	q_iflags;
		reg	[2:0]	r_iflags;
		initial	q_iflags = 3'b000;
		initial	r_reset_complete = 1'b0;
		always @(posedge i_data_clk)
		begin
			q_iflags <= { bw_reset_request, bw_manual_trigger, bw_disable_trigger };
			r_iflags <= q_iflags;
			r_reset_complete <= (dw_reset);
		end
		assign	dw_reset = r_iflags[2];
		assign	dw_manual_trigger = r_iflags[1];
		assign	dw_disable_trigger = r_iflags[0];
		(* ASYNC_REG = "TRUE" *) reg	q_reset_complete;
		reg	qq_reset_complete;
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
				((i_trigger)&&(!dw_disable_trigger))
				||(dw_manual_trigger));
	initial	dr_triggered = 1'b0;
	always @(posedge i_data_clk)
		if (dw_reset)
			dr_triggered <= 1'b0;
		else if ((i_ce)&&(dw_trigger))
			dr_triggered <= 1'b1;
	(* ASYNC_REG="TRUE" *) reg	[(HOLDOFFBITS-1):0]	holdoff_counter;
	reg		dr_stopped;
	initial	dr_stopped = 1'b0;
	initial	holdoff_counter = 0;
	always @(posedge i_data_clk)
		if (dw_reset)
			holdoff_counter <= 0;
		else if ((i_ce)&&(dr_triggered)&&(!dr_stopped))
		begin
			holdoff_counter <= holdoff_counter + 1'b1;
		end
	always @(posedge i_data_clk)
		if ((!dr_triggered)||(dw_reset))
			dr_stopped <= 1'b0;
		else if ((i_ce)&&(!dr_stopped))
		begin
			if (HOLDOFFBITS > 1) 
				dr_stopped <= (holdoff_counter >= br_holdoff);
			else if (HOLDOFFBITS <= 1)
				dr_stopped <= ((i_ce)&&(dw_trigger));
		end
	localparam	DLYSTOP=5;
	reg	[(DLYSTOP-1):0]	dr_stop_pipe;
	always @(posedge i_data_clk)
		if (dw_reset)
			dr_stop_pipe <= 0;
		else if (i_ce)
			dr_stop_pipe <= { dr_stop_pipe[(DLYSTOP-2):0], dr_stopped };
	wire	dw_final_stop;
	assign	dw_final_stop = dr_stop_pipe[(DLYSTOP-1)];
	reg	[(STEP_BITS-1):0]	ck_addr;
	reg	[(NELM-1):0]		qd_data;
	reg				dr_force_write, dr_run_timeout,
					new_data;
	reg		dr_force_inhibit;
	initial	ck_addr = 0;
	initial	dr_force_write = 1'b0;
	always @(posedge i_data_clk)
		if (dw_reset)
		begin
			dr_force_write    <= 1'b1;
			dr_force_inhibit  <= 1'b0;
		end else if (i_ce)
		begin
			dr_force_inhibit <= (dr_force_write);
			if ((dr_run_timeout)&&(!dr_force_write)&&(!dr_force_inhibit))
				dr_force_write <= 1'b1;
			else if (((dw_trigger)&&(!dr_triggered))||(!dr_primed))
				dr_force_write <= 1'b1;
			else
				dr_force_write <= 1'b0;
		end
	always @(posedge i_data_clk)
		if (dw_reset)
			ck_addr <= 0;
		else if (i_ce)
		begin
			if ((dr_force_write)||(new_data)||(dr_stopped))
				ck_addr <= 0;
			else
				ck_addr <= ck_addr + 1'b1;
		end
	always @(posedge i_data_clk)
		if (dw_reset)
			dr_run_timeout <= 1'b1;
		else if (i_ce)
			dr_run_timeout <= (ck_addr >= MAX_STEP-1'b1);
	always @(posedge i_data_clk)
		if (dw_reset)
			new_data <= 1'b1;
		else if (i_ce)
			new_data <= (i_data != qd_data);
	always @(posedge i_data_clk)
		if (i_ce)
			qd_data <= i_data;
	wire	[(BUSW-2):0]	w_data;
	generate
	if (NELM == BUSW-1)
		assign w_data = qd_data;
	else
		assign w_data = { {(BUSW-NELM-1){1'b0}}, qd_data };
	endgenerate
	reg	imm_adr, lst_adr; 
	reg	[(BUSW-2):0]	lst_val, 
				imm_val; 
	initial	lst_adr = 1'b1;
	initial	imm_adr = 1'b1;
	always @(posedge i_data_clk)
		if (dw_reset)
		begin
			imm_val <= 31'h0;
			imm_adr <= 1'b1;
			lst_val <= 31'h0;
			lst_adr <= 1'b1;
		end else if (i_ce)
		begin
			if ((new_data)||(dr_force_write)||(dr_stopped))
			begin
				imm_val <= w_data;
				imm_adr <= 1'b0; 
				lst_val <= imm_val;
				lst_adr <= imm_adr;
			end else begin
				imm_val <= ck_addr; 
				imm_adr <= 1'b1; 
				lst_val <= imm_val;
				lst_adr <= imm_adr;
			end
		end
	reg			record_ce;
	reg	[(BUSW-1):0]	r_data;
	initial			record_ce = 1'b0;
	always @(posedge i_data_clk)
		record_ce <= (i_ce)&&((!lst_adr)||(!imm_adr))&&(!dr_stop_pipe[2]);
	always @(posedge i_data_clk)
		r_data <= ((!lst_adr)||(!imm_adr))
			? { lst_adr, lst_val }
			: { {(32 - NELM){1'b0}}, qd_data };
	reg	[(LGMEM-1):0]	waddr;
	initial	waddr = {(LGMEM){1'b0}};
	initial	dr_primed = 1'b0;
	always @(posedge i_data_clk)
		if (dw_reset) 
		begin
			waddr <= 0; 
			dr_primed <= 1'b0;
		end else if (record_ce)
		begin
			waddr <= waddr + {{(LGMEM-1){1'b0}},1'b1};
			dr_primed <= (dr_primed)||(&waddr);
		end
	always @(posedge i_data_clk)
		if (record_ce)
			mem[waddr] <= r_data;
	wire	bw_stopped, bw_triggered, bw_primed;
	generate
	if (SYNCHRONOUS > 0)
	begin
		assign	bw_stopped   = dw_final_stop;
		assign	bw_triggered = dr_triggered;
		assign	bw_primed    = dr_primed;
	end else begin
		(* ASYNC_REG = "TRUE" *) reg	[2:0]	q_oflags;
		reg	[2:0]	r_oflags;
		initial	q_oflags = 3'h0;
		initial	r_oflags = 3'h0;
		always @(posedge i_wb_clk)
			if (bw_reset_request)
			begin
				q_oflags <= 3'h0;
				r_oflags <= 3'h0;
			end else begin
				q_oflags <= { dw_final_stop, dr_triggered, dr_primed };
				r_oflags <= q_oflags;
			end
		assign	bw_stopped   = r_oflags[2];
		assign	bw_triggered = r_oflags[1];
		assign	bw_primed    = r_oflags[0];
	end endgenerate
	reg	br_wb_ack, br_pre_wb_ack;
	initial	br_wb_ack = 1'b0;
	wire	bw_cyc_stb;
	assign	bw_cyc_stb = (i_wb_stb);
	initial	br_pre_wb_ack = 1'b0;
	initial	br_wb_ack = 1'b0;
	always @(posedge i_wb_clk)
	begin
		if ((bw_reset_request)
			||((bw_cyc_stb)&&(i_wb_addr)&&(i_wb_we)))
			raddr <= 0;
		else if ((bw_cyc_stb)&&(i_wb_addr)&&(!i_wb_we)&&(bw_stopped))
			raddr <= raddr + 1'b1; 
		br_pre_wb_ack <= bw_cyc_stb;
		br_wb_ack <= (br_pre_wb_ack)&&(i_wb_cyc);
	end
	reg	[(LGMEM-1):0]	this_addr;
	always @(posedge i_wb_clk)
		if ((bw_cyc_stb)&&(i_wb_addr)&&(!i_wb_we))
			this_addr <= raddr + waddr + 1'b1;
		else
			this_addr <= raddr + waddr;
	reg	[31:0]	nxt_mem;
	always @(posedge i_wb_clk)
		nxt_mem <= mem[this_addr];
	wire	[19:0]	full_holdoff;
	assign full_holdoff[(HOLDOFFBITS-1):0] = br_holdoff;
	generate if (HOLDOFFBITS < 20)
		assign full_holdoff[19:(HOLDOFFBITS)] = 0;
	endgenerate
	wire	[4:0]	bw_lgmem;
	assign		bw_lgmem = LGMEM;
	always @(posedge i_wb_clk)
		if (!i_wb_addr) 
			o_wb_data <= { bw_reset_request,
					bw_stopped,
					bw_triggered,
					bw_primed,
					bw_manual_trigger,
					bw_disable_trigger,
					(raddr == {(LGMEM){1'b0}}),
					bw_lgmem,
					full_holdoff  };
		else if (!bw_stopped) 
			o_wb_data <= {1'b0, w_data };
		else 
			o_wb_data <= nxt_mem; 
	assign	o_wb_stall = 1'b0;
	assign	o_wb_ack = (i_wb_cyc)&&(br_wb_ack);
	reg	br_level_interrupt;
	initial	br_level_interrupt = 1'b0;
	assign	o_interrupt = (bw_stopped)&&(!bw_disable_trigger)
					&&(!br_level_interrupt);
	always @(posedge i_wb_clk)
	if ((bw_reset_complete)||(bw_reset_request))
		br_level_interrupt<= 1'b0;
	else
		br_level_interrupt<= (bw_stopped)&&(!bw_disable_trigger);
	wire	[3+6+(20-HOLDOFFBITS)-1:0] unused;
	assign	unused = { i_wb_data[30:28], i_wb_data[25:HOLDOFFBITS] };
endmodule

