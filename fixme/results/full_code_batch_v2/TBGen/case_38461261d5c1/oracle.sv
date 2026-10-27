`timescale 1ns/1ps
module oracle_ufifo(i_clk, i_rst, i_wr, i_data, o_empty_n, i_rd, o_data, o_status, o_err);
	parameter	BW=8;	
	parameter [3:0]	LGFLEN=4;
	parameter 	RXFIFO=1'b0;
	input	wire		i_clk, i_rst;
	input	wire		i_wr;
	input	wire [(BW-1):0]	i_data;
	output	wire		o_empty_n;	
	input	wire		i_rd;
	output	wire [(BW-1):0]	o_data;
	output	wire	[15:0]	o_status;
	output	wire		o_err;
	localparam	FLEN=(1<<LGFLEN);
	reg	[(BW-1):0]	fifo[0:(FLEN-1)];
	reg	[(LGFLEN-1):0]	r_first, r_last, r_next;
	wire	[(LGFLEN-1):0]	w_first_plus_one, w_first_plus_two,
				w_last_plus_one;
	assign	w_first_plus_two = r_first + {{(LGFLEN-2){1'b0}},2'b10};
	assign	w_first_plus_one = r_first + {{(LGFLEN-1){1'b0}},1'b1};
	assign	w_last_plus_one  = r_next; 
	reg	will_overflow;
	initial	will_overflow = 1'b0;
	always @(posedge i_clk)
		if (i_rst)
			will_overflow <= 1'b0;
		else if (i_rd)
			will_overflow <= (will_overflow)&&(i_wr);
		else if (i_wr)
			will_overflow <= (will_overflow)||(w_first_plus_two == r_last);
		else if (w_first_plus_one == r_last)
			will_overflow <= 1'b1;
	reg	r_ovfl;
	initial	r_first = 0;
	initial	r_ovfl  = 0;
	always @(posedge i_clk)
		if (i_rst)
		begin
			r_ovfl <= 1'b0;
			r_first <= { (LGFLEN){1'b0} };
		end else if (i_wr)
		begin 
			if ((i_rd)||(!will_overflow)) 
				r_first <= w_first_plus_one;
			else
				r_ovfl <= 1'b1;
		end
	always @(posedge i_clk)
		if (i_wr) 
			fifo[r_first] <= i_data;
	reg	will_underflow;
	initial	will_underflow = 1'b1;
	always @(posedge i_clk)
		if (i_rst)
			will_underflow <= 1'b1;
		else if (i_wr)
			will_underflow <= 1'b0;
		else if (i_rd)
			will_underflow <= (will_underflow)||(w_last_plus_one == r_first);
		else
			will_underflow <= (r_last == r_first);
	initial	r_last = 0;
	initial	r_next = { {(LGFLEN-1){1'b0}}, 1'b1 };
	always @(posedge i_clk)
		if (i_rst)
		begin
			r_last <= 0;
			r_next <= { {(LGFLEN-1){1'b0}}, 1'b1 };
		end else if (i_rd)
		begin
			if (!will_underflow) 
			begin
				r_last <= r_next;
				r_next <= r_last +{{(LGFLEN-2){1'b0}},2'b10};
			end
		end
	reg	[(BW-1):0]	fifo_here, fifo_next, r_data;
	always @(posedge i_clk)
		fifo_here <= fifo[r_last];
	always @(posedge i_clk)
		fifo_next <= fifo[r_next];
	always @(posedge i_clk)
		r_data <= i_data;
	reg	[1:0]	osrc;
	always @(posedge i_clk)
		if (will_underflow)
			osrc <= 2'b00;
		else if ((i_rd)&&(r_first == w_last_plus_one))
			osrc <= 2'b01;
		else if (i_rd)
			osrc <= 2'b11;
		else
			osrc <= 2'b10;
	assign o_data = (osrc[1]) ? ((osrc[0])?fifo_next:fifo_here) : r_data;
	reg	r_empty_n;
	initial	r_empty_n = 1'b0;
	always @(posedge i_clk)
		if (i_rst)
			r_empty_n <= 1'b0;
		else casez({i_wr, i_rd, will_underflow})
			3'b00?: r_empty_n <= (r_first != r_last);
			3'b010: r_empty_n <= (r_first != w_last_plus_one);
			3'b10?: r_empty_n <= 1'b1;
			3'b110: r_empty_n <= (r_first != r_last);
			3'b111: r_empty_n <= 1'b1;
			default: begin end
		endcase
	wire	w_full_n;
	assign	w_full_n = will_overflow;
	reg	[(LGFLEN-1):0]	r_fill;
	generate
	if (RXFIFO != 0)
		initial	r_fill = 0;
	else
		initial	r_fill = -1;
	endgenerate
	always @(posedge i_clk)
		if (RXFIFO!=0) begin
			if (i_rst)
				r_fill <= 0;
			else casez({(i_wr), (!will_overflow), (i_rd)&&(!will_underflow)})
			3'b0?1:   r_fill <= r_first - r_next;
			3'b110:   r_fill <= r_first - r_last + 1'b1;
			3'b1?1:   r_fill <= r_first - r_last;
			default: r_fill <= r_first - r_last;
			endcase
		end else begin
			if (i_rst)
				r_fill <= { (LGFLEN){1'b1} };
			else casez({i_wr, (!will_overflow), (i_rd)&&(!will_underflow)})
			3'b0?1:   r_fill <= r_fill + 1'b1;
			3'b110:   r_fill <= r_fill - 1'b1;
			default: r_fill  <= r_fill;
			endcase
		end
	assign o_err = (r_ovfl); 
	wire	[3:0]	lglen;
	assign lglen = LGFLEN;
	wire	w_half_full;
	wire	[9:0]	w_fill;
	assign	w_fill[(LGFLEN-1):0] = r_fill;
	generate if (LGFLEN < 10)
		assign w_fill[9:(LGFLEN)] = 0;
	endgenerate
	assign	w_half_full = r_fill[(LGFLEN-1)];
	assign	o_status = {
		lglen,
		w_fill,
		(RXFIFO!=0)?w_half_full:w_half_full,
		(RXFIFO!=0)?r_empty_n:!w_full_n
	};
	assign	o_empty_n = r_empty_n;
`ifdef	FORMAL
`ifdef	UFIFO
`define	ASSUME	assume
`else
`define	ASSUME	assert
`endif
	reg	f_past_valid, f_last_clk;
	initial	f_past_valid = 1'b0;
	always @(posedge i_clk)
		f_past_valid <= 1'b1;
	wire	[(LGFLEN-1):0]	f_fill, f_next, f_empty;
	assign	f_fill = r_first - r_last;
	assign	f_empty = {(LGFLEN){1'b1}} -f_fill;
	assign	f_next = r_last + 1'b1;
	always @(posedge i_clk)
	begin
		if (RXFIFO)
			assert(f_fill == r_fill);
		else
			assert(f_empty== r_fill);
		if (f_fill == 0)
		begin
			assert(will_underflow);
			assert(!o_empty_n);
		end else begin
			assert(!will_underflow);
			assert(o_empty_n);
		end
		if (f_fill == {(LGFLEN){1'b1}})
			assert(will_overflow);
		else
			assert(!will_overflow);
		assert(r_next == f_next);
	end
	always @(posedge i_clk)
	if (f_past_valid)
	begin
		if ($past(i_rst))
			assert(!o_err);
		else begin
			if (($past(i_wr))&&(!$past(i_rd))
					&&($past(will_overflow)))
				assert(o_err);
		end
	end
	always @(posedge i_clk)
	if (RXFIFO)
	begin
		assert(o_status[0] == (f_fill != 0));
		assert(o_status[1] == (f_fill[LGFLEN-1]));
	end
	always @(posedge i_clk)
	if (!RXFIFO) 
	begin
		assert(o_status[0] == (!w_full_n));
		assert(o_status[1] == (!f_fill[LGFLEN-1]));
	end
`endif
endmodule