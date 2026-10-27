`timescale 1ns/1ps

module rtcdate(i_clk, i_ppd, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_data,
		o_wb_ack, o_wb_stall, o_wb_data);
	input	i_clk;
	input	i_ppd;
	input	i_wb_cyc, i_wb_stb, i_wb_we;
	input	[31:0]	i_wb_data;
	output	reg	o_wb_ack;
	output	wire	o_wb_stall;
	output	wire	[31:0]	o_wb_data;
	reg	[5:0]	r_day;
	reg	[4:0]	r_mon;
	reg	[13:0]	r_year;
	reg	last_day_of_month, last_day_of_year, is_leap_year;
	always @(posedge i_clk)
		last_day_of_year <= (last_day_of_month) && (r_mon == 5'h12);
	always @(posedge i_clk)
	begin
		case(r_mon)
		5'h01: last_day_of_month <= (r_day >= 6'h31); 
		5'h02: last_day_of_month <= (r_day >= 6'h29)
				||((~is_leap_year)&&(r_day == 6'h28));
		5'h03: last_day_of_month <= (r_day >= 6'h31); 
		5'h04: last_day_of_month <= (r_day >= 6'h30); 
		5'h05: last_day_of_month <= (r_day >= 6'h31); 
		5'h06: last_day_of_month <= (r_day >= 6'h30); 
		5'h07: last_day_of_month <= (r_day >= 6'h31); 
		5'h08: last_day_of_month <= (r_day >= 6'h31); 
		5'h09: last_day_of_month <= (r_day >= 6'h30); 
		5'h10: last_day_of_month <= (r_day >= 6'h31); 
		5'h11: last_day_of_month <= (r_day >= 6'h30); 
		5'h12: last_day_of_month <= (r_day >= 6'h31); 
		default: last_day_of_month <= 1'b0;
		endcase
	end
	reg	year_divisible_by_four, century_year, four_century_year;
	always @(posedge i_clk)
		year_divisible_by_four<= ((~r_year[0])&&(r_year[4]==r_year[1]));
	always @(posedge i_clk)
		century_year <= (r_year[7:0] == 8'h00);
	always @(posedge i_clk)
		four_century_year <= ((~r_year[8])&&((r_year[12]==r_year[9])));
	always @(posedge i_clk)
		is_leap_year <= (year_divisible_by_four)&&((~century_year)
			||((century_year)&&(four_century_year)));
	initial	r_day = 6'h01;
	always @(posedge i_clk)
	begin
		if ((r_day == 0)||(r_day > 6'h31)||(r_day[3:0] > 4'h9))
			r_day <= 6'h01;
		else if ((i_ppd)&&(last_day_of_month))
			r_day <= 6'h01;
		else if ((i_ppd)&&(r_day[3:0] != 4'h9))
			r_day[3:0] <= r_day[3:0] + 4'h1;
		else if (i_ppd)
		begin
			r_day[3:0] <= 4'h0;
			r_day[5:4] <= r_day[5:4] + 2'h1;
		end
		if ((i_wb_cyc)&&(i_wb_stb)&&(i_wb_we)&&(i_wb_data[7:0]!=8'hff))
			r_day <= i_wb_data[5:0];
	end
	initial	r_mon = 5'h01;
	always @(posedge i_clk)
	begin
		if ((r_mon == 0)||(r_mon > 5'h12)||(r_mon[3:0] > 4'h9))
			r_mon <= 5'h01;
		else if ((i_ppd)&&(last_day_of_year))
			r_mon <= 5'h01;
		else if ((i_ppd)&&(last_day_of_month)&&(r_mon[3:0] != 4'h9))
			r_mon[3:0] <= r_mon[3:0] + 4'h1;
		else if ((i_ppd)&&(last_day_of_month))
		begin
			r_mon[3:0] <= 4'h0;
			r_mon[4] <= 1;
		end
		if ((i_wb_cyc)&&(i_wb_stb)&&(i_wb_we)&&(i_wb_data[15:8]!=8'hff))
			r_mon <= i_wb_data[12:8];
	end
	initial	r_year = 14'h2000;
	always @(posedge i_clk)
	begin
		if (r_year[3:0] > 4'h9)
			r_year[3:0] <= 4'h0;
		if (r_year[7:4] > 4'h9)
			r_year[7:4] <= 4'h0;
		if (r_year[11:8] > 4'h9)
			r_year[11:8] <= 4'h0;
		if ((i_ppd)&&(last_day_of_year))
		begin
			if (r_year[3:0] != 4'h9)
				r_year[3:0] <= r_year[3:0] + 4'h1;
			else begin
				r_year[3:0] <= 4'h0;
				if (r_year[7:4] != 4'h9)
					r_year[7:4] <= r_year[7:4] + 4'h1;
				else begin
					r_year[7:4] <= 4'h0;
					if (r_year[11:8] != 4'h9)
						r_year[11:8] <= r_year[11:8]+4'h1;
					else begin
						r_year[11:8] <= 4'h0;
						r_year[13:12] <= r_year[13:12]+2'h1;
					end
				end
			end
		end
		if ((i_wb_cyc)&&(i_wb_stb)&&(i_wb_we)&&(i_wb_data[31:16]!=16'hffff))
			r_year <= i_wb_data[29:16];
	end
	always @(posedge i_clk)
		o_wb_ack <= ((i_wb_cyc)&&(i_wb_stb));
	assign	o_wb_stall = 1'b0;
	assign	o_wb_data = { 2'h0, r_year, 3'h0, r_mon, 2'h0, r_day };
endmodule
