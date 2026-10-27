`timescale 1ns/1ps
 
module	div_ref(i_clk, i_rst, i_wr, i_signed, i_numerator, i_denominator,
		o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);
	parameter		BW=32, LGBW = 5;
	input			i_clk, i_rst;
	input			i_wr, i_signed;
	input	[(BW-1):0]	i_numerator, i_denominator;
	output	reg		o_busy_ref, o_valid_ref, o_err_ref;
	output	reg [(BW-1):0]	o_quotient_ref;
	output	wire	[3:0]	o_flags_ref;
	reg			r_busy;
	reg	[(2*BW-2):0]	r_divisor;
	reg	[(BW-1):0]	r_dividend;
	wire	[(BW):0]	diff; 
	assign	diff = r_dividend - r_divisor[(BW-1):0];
	reg		r_sign, pre_sign, r_z, r_c, last_bit;
	reg	[(LGBW-1):0]	r_bit;
	reg	zero_divisor;
	initial	zero_divisor = 1'b0;
	always @(posedge i_clk)
		zero_divisor <= (r_divisor == 0)&&(r_busy);
	initial	r_busy = 1'b0;
	always @(posedge i_clk)
		if (i_rst)
			r_busy <= 1'b0;
		else if (i_wr)
			r_busy <= 1'b1;
		else if ((last_bit)||(zero_divisor))
			r_busy <= 1'b0;
	initial	o_busy_ref = 1'b0;
	always @(posedge i_clk)
		if (i_rst)
			o_busy_ref <= 1'b0;
		else if (i_wr)
			o_busy_ref <= 1'b1;
		else if (((last_bit)&&(~r_sign))||(zero_divisor))
			o_busy_ref <= 1'b0;
		else if (~r_busy)
			o_busy_ref <= 1'b0;
	always @(posedge i_clk)
		if ((i_rst)||(i_wr))
			o_valid_ref <= 1'b0;
		else if (r_busy)
		begin
			if ((last_bit)||(zero_divisor))
				o_valid_ref <= (zero_divisor)||(~r_sign);
		end else if (r_sign)
		begin
			o_valid_ref <= (~zero_divisor); 
		end else
			o_valid_ref <= 1'b0;
	initial	o_err_ref = 1'b0;
	always @(posedge i_clk)
		if((i_rst)||(o_valid_ref))
			o_err_ref <= 1'b0;
		else if (((r_busy)||(r_sign))&&(zero_divisor))
			o_err_ref <= 1'b1;
		else
			o_err_ref <= 1'b0;
	initial	last_bit = 1'b0;
	always @(posedge i_clk)
		if ((i_wr)||(pre_sign)||(i_rst))
			last_bit <= 1'b0;
		else if (r_busy)
			last_bit <= (r_bit == {{(LGBW-1){1'b0}},1'b1});
	always @(posedge i_clk)
		if (i_wr)
		begin
			o_quotient_ref <= 0;
			r_bit <= {(LGBW){1'b1}};
			r_divisor <= {  i_denominator, {(BW-1){1'b0}} };
			r_dividend <=  i_numerator;
			r_sign <= 1'b0;
			pre_sign <= i_signed;
			r_z <= 1'b1;
		end else if (pre_sign)
		begin
			r_sign <= ((r_divisor[(2*BW-2)])^(r_dividend[(BW-1)]));
			if (r_dividend[BW-1])
				r_dividend <= -r_dividend;
			if (r_divisor[(2*BW-2)])
				r_divisor[(2*BW-2):(BW-1)] <= -r_divisor[(2*BW-2):(BW-1)];
			pre_sign <= 1'b0;
		end else if (r_busy)
		begin
			r_bit <= r_bit + {(LGBW){1'b1}}; 
			r_divisor <= { 1'b0, r_divisor[(2*BW-2):1] };
			if (|r_divisor[(2*BW-2):(BW)])
			begin
			end else if (diff[BW])
			begin
			end else begin
				r_dividend <= diff[(BW-1):0];
				o_quotient_ref[r_bit[(LGBW-1):0]] <= 1'b1;
				r_z <= 1'b0;
			end
			r_sign <= (r_sign)&&(~zero_divisor);
		end else if (r_sign)
		begin
			r_sign <= 1'b0;
			o_quotient_ref <= -o_quotient_ref;
		end
	wire	w_n;
	always @(posedge i_clk)
		r_c <= (r_busy)&&((diff == 0)||(r_dividend == 0));
	assign w_n = o_quotient_ref[(BW-1)];
	assign o_flags_ref = { 1'b0, w_n, r_c, r_z };
endmodule

