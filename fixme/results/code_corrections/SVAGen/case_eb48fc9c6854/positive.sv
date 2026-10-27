`timescale 1ns/1ps
module	pfcache(i_clk, i_rst, i_new_pc, i_clear_cache,
			i_stall_n, i_pc, o_i, o_pc, o_v,
		o_wb_cyc, o_wb_stb, o_wb_we, o_wb_addr, o_wb_data,
			i_wb_ack, i_wb_stall, i_wb_err, i_wb_data,
			o_illegal);
	parameter	LGCACHELEN = 8, ADDRESS_WIDTH=24,
			LGLINES=5; 
	localparam	CACHELEN=(1<<LGCACHELEN); 
	localparam	CW=LGCACHELEN;	
	localparam	PW=LGCACHELEN-LGLINES; 
	localparam	BUSW = 32;	
	localparam	AW=ADDRESS_WIDTH; 
	input				i_clk, i_rst, i_new_pc;
	input				i_clear_cache;
	input				i_stall_n;
	input		[(AW-1):0]	i_pc;
	output	wire	[(BUSW-1):0]	o_i;
	output	wire	[(AW-1):0]	o_pc;
	output	wire			o_v;
	output	reg		o_wb_cyc, o_wb_stb;
	output	wire		o_wb_we;
	output	reg	[(AW-1):0]	o_wb_addr;
	output	wire	[(BUSW-1):0]	o_wb_data;
	input				i_wb_ack, i_wb_stall, i_wb_err;
	input		[(BUSW-1):0]	i_wb_data;
	output	reg			o_illegal;
	assign	o_wb_we = 1'b0;
	assign	o_wb_data = 0;
	wire			r_v;
	reg	[(BUSW-1):0]	cache	[0:((1<<CW)-1)];
	reg	[(AW-CW-1):0]	tags	[0:((1<<(LGLINES))-1)];
	reg	[((1<<(LGLINES))-1):0]	vmask;
	reg	[(AW-1):0]	lastpc;
	reg	[(CW-1):0]	rdaddr;
	reg	[(AW-1):CW]	tagvalipc, tagvallst;
	wire	[(AW-1):CW]	tagval;
	wire	[(AW-1):PW]	lasttag;
	reg			illegal_valid;
	reg	[(AW-1):PW]	illegal_cache;
	reg	[(BUSW-1):0]	r_pc_cache, r_last_cache;
	reg	[(AW-1):0]	r_pc, r_lastpc;
	reg	isrc;
	always @(posedge i_clk)
	begin
		isrc <= ((r_v)&&(i_stall_n))||(i_new_pc);
		r_pc_cache <= cache[i_pc[(CW-1):0]];
		r_last_cache <= cache[lastpc[(CW-1):0]];
		r_pc <= i_pc;
		r_lastpc <= lastpc;
	end
	assign	o_pc = (isrc) ? r_pc : r_lastpc;
	assign	o_i  = (isrc) ? r_pc_cache : r_last_cache;
	reg	tagsrc;
	always @(posedge i_clk)
		if (((r_v)&&(i_stall_n))||(i_clear_cache)||(i_new_pc))
			tagsrc <= 1'b1;
		else
			tagsrc <= 1'b0;
	initial	tagvalipc = 0;
	always @(posedge i_clk)
		tagvalipc <= tags[i_pc[(CW-1):PW]];
	initial	tagvallst = 0;
	always @(posedge i_clk)
		tagvallst <= tags[lastpc[(CW-1):PW]];
	assign	tagval = (tagsrc)?tagvalipc : tagvallst;
	initial	lastpc = 0;
	always @(posedge i_clk)
		if (((r_v)&&(i_stall_n))||(i_clear_cache)||(i_new_pc))
			lastpc <= i_pc;
	assign	lasttag = lastpc[(AW-1):PW];
	wire	w_v_from_pc, w_v_from_last;
	assign	w_v_from_pc = ((i_pc[(AW-1):PW] == lasttag)
				&&(tagvalipc == i_pc[(AW-1):CW])
				&&(vmask[i_pc[(CW-1):PW]]));
	assign	w_v_from_last = (
				(tagval == lastpc[(AW-1):CW])
				&&(vmask[lastpc[(CW-1):PW]]));
	reg	[1:0]	delay;
	initial	delay = 2'h3;
	reg	rvsrc;
	always @(posedge i_clk)
		if ((i_rst)||(i_clear_cache)||(i_new_pc)||((r_v)&&(i_stall_n)))
		begin
			rvsrc <= 1'b1;
			delay <= 2'h2;
		end else if (~r_v) begin 
			rvsrc <= 1'b0;
			if (o_wb_cyc)
				delay <= 2'h2;
			else if (delay != 0)
				delay <= delay + 2'b11; 
		end
	reg	r_v_from_pc, r_v_from_last;
	always @(posedge i_clk)
		r_v_from_pc <= w_v_from_pc;
	always @(posedge i_clk)
		r_v_from_last <= w_v_from_last;
	assign	r_v = ((rvsrc)?(r_v_from_pc):(r_v_from_last));
	assign	o_v = (((rvsrc)?(r_v_from_pc):(r_v_from_last))
				||((o_illegal)&&(~o_wb_cyc)))
			&&(~i_new_pc)&&(~i_rst);
	reg	last_ack;
	initial	last_ack = 1'b0;
	always @(posedge i_clk)
		last_ack <= (o_wb_cyc)&&(
				(rdaddr[(PW-1):1]=={(PW-1){1'b1}})
				&&((rdaddr[0])||(i_wb_ack)));
	reg	needload;
	initial	needload = 1'b0;
	always @(posedge i_clk)
		needload <= ((~r_v)&&(delay==0)
			&&((tagvallst != lastpc[(AW-1):CW])
				||(~vmask[lastpc[(CW-1):PW]]))
			&&((~illegal_valid)
				||(lastpc[(AW-1):PW] != illegal_cache)));
	reg	last_addr;
	initial	last_addr = 1'b0;
	always @(posedge i_clk)
		last_addr <= (o_wb_cyc)&&(o_wb_addr[(PW-1):1] == {(PW-1){1'b1}})
				&&((~i_wb_stall)|(o_wb_addr[0]));
	initial	o_wb_cyc  = 1'b0;
	initial	o_wb_stb  = 1'b0;
	initial	o_wb_addr = {(AW){1'b0}};
	initial	rdaddr    = 0;
	always @(posedge i_clk)
		if ((i_rst)||(i_clear_cache))
		begin
			o_wb_cyc <= 1'b0;
			o_wb_stb <= 1'b0;
		end else if (o_wb_cyc)
		begin
			if (i_wb_err)
				o_wb_stb <= 1'b0;
			else if ((o_wb_stb)&&(~i_wb_stall)&&(last_addr))
				o_wb_stb <= 1'b0;
			if (((i_wb_ack)&&(last_ack))||(i_wb_err))
				o_wb_cyc <= 1'b0;
		end else if (needload)
		begin
			o_wb_cyc  <= 1'b1;
			o_wb_stb  <= 1'b1;
		end
	always @(posedge i_clk)
		if (o_wb_cyc) 
			tags[o_wb_addr[(CW-1):PW]] <= o_wb_addr[(AW-1):CW];
	always @(posedge i_clk)
		if ((o_wb_cyc)&&(i_wb_ack))
			rdaddr <= rdaddr + 1;
		else if (~o_wb_cyc)
			rdaddr <= { lastpc[(CW-1):PW], {(PW){1'b0}} };
	always @(posedge i_clk)
		if ((o_wb_stb)&&(~i_wb_stall)&&(~last_addr))
			o_wb_addr[(PW-1):0] <= o_wb_addr[(PW-1):0]+1;
		else if (~o_wb_cyc)
			o_wb_addr <= { lastpc[(AW-1):PW], {(PW){1'b0}} };
	always @(posedge i_clk)
		if (o_wb_cyc) 
			cache[rdaddr] <= i_wb_data;
	reg	svmask;
	initial	vmask = 0;
	initial	svmask = 1'b0;
	reg	[(LGLINES-1):0]	saddr;
	always @(posedge i_clk)
		if ((i_rst)||(i_clear_cache))
		begin
			vmask <= 0;
			svmask<= 1'b0;
		end
		else begin
			svmask <= ((o_wb_cyc)&&(i_wb_ack)&&(last_ack));
			if (svmask)
				vmask[saddr] <= 1'b1;
			if ((~o_wb_cyc)&&(needload))
				vmask[lastpc[(CW-1):PW]] <= 1'b0;
		end
	always @(posedge i_clk)
		if ((o_wb_cyc)&&(i_wb_ack))
			saddr <= rdaddr[(CW-1):PW];
	initial	illegal_cache = 0;
	initial	illegal_valid = 0;
	always @(posedge i_clk)
		if ((i_rst)||(i_clear_cache))
		begin
			illegal_cache <= 0;
			illegal_valid <= 0;
		end else if ((o_wb_cyc)&&(i_wb_err))
		begin
			illegal_cache <= o_wb_addr[(AW-1):PW];
			illegal_valid <= 1'b1;
		end
	initial o_illegal = 1'b0;
	always @(posedge i_clk)
		if ((i_rst)||(i_clear_cache)||(o_wb_cyc))
			o_illegal <= 1'b0;
		else
			o_illegal <= (illegal_valid)
				&&(illegal_cache == i_pc[(AW-1):PW]);
always @* assert((o_wb_we) == 1'(1'b0));
endmodule