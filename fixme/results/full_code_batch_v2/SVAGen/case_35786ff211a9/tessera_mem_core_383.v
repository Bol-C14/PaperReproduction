`timescale 1ns/1ps
module tessera_mem_core (
	rst,
	clk,
	write_req,
	write_byte,
	write_address,
	write_data,
	write_ack,
	read_req,
	read_byte,
	read_address,
	read_data,
	read_ack,
	mem_cs2_n,
	mem_cs2_g_n,
	mem_cs2_dir,
	mem_cs2_rstdrv,
	mem_cs2_int,
	mem_cs2_iochrdy,
	mem_cs1_n,
	mem_cs1_rst_n,
	mem_cs1_rdy,
	mem_cs0_n,
	mem_we_n,
	mem_oe_n,
	mem_a,
	mem_d_o,
	mem_d_oe,
	mem_d_i
);
	input		rst;
	input		clk;
	input		write_req;
	input	[3:0]	write_byte;
	input	[31:0]	write_address;
	input	[31:0]	write_data;
	output		write_ack;
	input		read_req;
	input	[3:0]	read_byte;
	input	[31:0]	read_address;
	output	[31:0]	read_data;
	output		read_ack;
	output		mem_cs2_n;
	output		mem_cs2_g_n;
	output		mem_cs2_dir;
	output		mem_cs2_rstdrv;
	input		mem_cs2_int;
	input		mem_cs2_iochrdy;
	output		mem_cs1_n;
	output		mem_cs1_rst_n;
	input		mem_cs1_rdy;
	output		mem_cs0_n;
	output		mem_we_n;
	output		mem_oe_n;
	output	[22:0]	mem_a;
	output	[7:0]	mem_d_o;
	output	[7:0]	mem_d_oe;
	input	[7:0]	mem_d_i;
	wire		cs0_write_req;
	wire		cs0_read_req;
	wire		cs1_write_req;
	wire		cs1_read_req;
	wire		cs2_write_req;
	wire		cs2_read_req;
	wire		write_fin;
	wire		read_fin;
	reg		write_ack;
	reg		read_ack;
	assign cs0_write_req	= write_req			&& !write_ack	&& (write_address[23:22]==2'b00);	
	assign cs0_read_req	= (read_req&&!write_req)	&& !read_ack	&& ( read_address[23:22]==2'b00);	
	assign cs2_write_req	= write_req			&& !write_ack	&& (write_address[23:22]==2'b01);	
	assign cs2_read_req	= (read_req&&!write_req)	&& !read_ack	&& ( read_address[23:22]==2'b01);	
	assign cs1_write_req	= write_req			&& !write_ack	&& (write_address[23]   ==1'b1);	
	assign cs1_read_req	= (read_req&&!write_req)	&& !read_ack	&& ( read_address[23]   ==1'b1);	
	wire		cs0_write_count_full;
	wire		cs0_write_byte_full;
	wire		cs0_write_cs;
	wire		cs0_write_strobe;
	wire	[3:0]	cs0_write_load;
	wire	[22:0]	cs0_write_addr;
	wire		cs0_write_fin;
	reg	[2:0]	cs0_write_count;
	reg	[1:0]	cs0_write_byte;
	assign cs0_write_count_full		= (3'd7==cs0_write_count);
	assign cs0_write_byte_full		= (2'd3==cs0_write_byte);
	assign cs0_write_cs			= cs0_write_req                           && (3'd0!=cs0_write_count)                                                       && (3'd7!=cs0_write_count);
	assign cs0_write_strobe			= cs0_write_req                           && (3'd0!=cs0_write_count) && (3'd1!=cs0_write_count) && (3'd6!=cs0_write_count) && (3'd7!=cs0_write_count)
						&& (
							( (2'd0==cs0_write_byte) && write_byte[3] )
							||
							( (2'd1==cs0_write_byte) && write_byte[2] )
							||
							( (2'd2==cs0_write_byte) && write_byte[1] )
							||
							( (2'd3==cs0_write_byte) && write_byte[0] )
						);
	assign cs0_write_load[0]		= cs0_write_req && (2'd3==cs0_write_byte) && (3'd0==cs0_write_count);
	assign cs0_write_load[1]		= cs0_write_req && (2'd2==cs0_write_byte) && (3'd0==cs0_write_count);
	assign cs0_write_load[2]		= cs0_write_req && (2'd1==cs0_write_byte) && (3'd0==cs0_write_count);
	assign cs0_write_load[3]		= cs0_write_req && (2'd0==cs0_write_byte) && (3'd0==cs0_write_count);
	assign cs0_write_addr			= (cs0_write_req) ? {write_address[22:2],cs0_write_byte[1:0]}: 23'd0;
	assign cs0_write_fin			= cs0_write_req && (2'd3==cs0_write_byte) && (3'd7==cs0_write_count);
	always @(posedge clk or posedge rst)
		if (rst) 			
		cs0_write_count	<= 3'd0;
		else if (!cs0_write_req)	
		cs0_write_count	<= 3'd0;
		else				
		cs0_write_count	<= (cs0_write_count_full) ? 3'd0: {cs0_write_count + 3'd1};	
	always @(posedge clk or posedge rst)
		if (rst)
					cs0_write_byte	<= 2'd0;
		else if (!cs0_write_req)
			cs0_write_byte	<= 2'd0;
		else if (cs0_write_count_full)
			cs0_write_byte	<= (cs0_write_byte_full) ? 2'd0: {cs0_write_byte + 2'd1};
	wire		cs0_read_count_full;
	wire		cs0_read_byte_full;
	wire		cs0_read_cs;
	wire		cs0_read_strobe;
	wire	[3:0]	cs0_read_load;
	wire	[22:0]	cs0_read_addr;
	wire		cs0_read_fin;
	reg	[2:0]	cs0_read_count;
	reg	[1:0]	cs0_read_byte;
	assign cs0_read_count_full		= (3'd7==cs0_read_count);
	assign cs0_read_byte_full		= (2'd3==cs0_read_byte);
	assign cs0_read_cs			= cs0_read_req                          && (3'd0!=cs0_read_count)                                                     && (3'd7!=cs0_read_count);
	assign cs0_read_strobe			= cs0_read_req                          && (3'd0!=cs0_read_count) && (3'd1!=cs0_read_count) && (3'd6!=cs0_read_count) && (3'd7!=cs0_read_count)
						&& (
							( (2'd0==cs0_read_byte) && read_byte[3] )
							||
							( (2'd1==cs0_read_byte) && read_byte[2] )
							||
							( (2'd2==cs0_read_byte) && read_byte[1] )
							||
							( (2'd3==cs0_read_byte) && read_byte[0] )
						);	
	assign cs0_read_load[0]			= cs0_read_req && (2'd3==cs0_read_byte) && (3'd7==cs0_read_count); 
	assign cs0_read_load[1]			= cs0_read_req && (2'd2==cs0_read_byte) && (3'd7==cs0_read_count); 
	assign cs0_read_load[2]			= cs0_read_req && (2'd1==cs0_read_byte) && (3'd7==cs0_read_count); 
	assign cs0_read_load[3]			= cs0_read_req && (2'd0==cs0_read_byte) && (3'd7==cs0_read_count); 
	assign cs0_read_addr			= (cs0_read_req) ? {read_address[22:2],cs0_read_byte[1:0]}: 23'd0;
	assign cs0_read_fin			= cs0_read_req && (2'd3==cs0_read_byte) && (3'd7==cs0_read_count);
	always @(posedge clk or posedge rst)
		if (rst)
		 		cs0_read_count	<= 3'd0;
		else if (!cs0_read_req)
				cs0_read_count	<= 3'd0;
		else
				cs0_read_count	<= (cs0_read_count_full) ? 3'd0: {cs0_read_count + 3'd1};	
	always @(posedge clk or posedge rst)
		if (rst)
				cs0_read_byte	<= 2'd0;
		else if (!cs0_read_req)
				cs0_read_byte	<= 2'd0;
		else if (cs0_read_count_full)
			cs0_read_byte	<= (cs0_read_byte_full) ? 2'd0: {cs0_read_byte + 2'd1};
	reg		mem_cs0_n;
	always @(posedge clk or posedge rst)
		if (rst)
					mem_cs0_n	<= 1'b1;
		else
						mem_cs0_n	<= !(cs0_write_cs||cs0_read_cs);
	wire		cs1_write_count_full;
	wire		cs1_write_byte_full;
	wire		cs1_write_cs;
	wire		cs1_write_strobe;
	wire	[3:0]	cs1_write_load;
	wire	[22:0]	cs1_write_addr;
	wire		cs1_write_fin;
	reg	[2:0]	cs1_write_count;
	reg	[1:0]	cs1_write_byte;
	assign cs1_write_count_full		= (3'd7==cs1_write_count);
	assign cs1_write_byte_full		= (2'd3==cs1_write_byte);
	assign cs1_write_cs			= cs1_write_req                           && (3'd0!=cs1_write_count)                                                       && (3'd7!=cs1_write_count);
	assign cs1_write_strobe			= cs1_write_req                           && (3'd0!=cs1_write_count) && (3'd1!=cs1_write_count) && (3'd6!=cs1_write_count) && (3'd7!=cs1_write_count)
						&& (
							( (2'd0==cs1_write_byte) && write_byte[3] )
							||
							( (2'd1==cs1_write_byte) && write_byte[2] )
							||
							( (2'd2==cs1_write_byte) && write_byte[1] )
							||
							( (2'd3==cs1_write_byte) && write_byte[0] )
						);
	assign cs1_write_load[0]		= cs1_write_req && (2'd3==cs1_write_byte) && (3'd0==cs1_write_count);
	assign cs1_write_load[1]		= cs1_write_req && (2'd2==cs1_write_byte) && (3'd0==cs1_write_count);
	assign cs1_write_load[2]		= cs1_write_req && (2'd1==cs1_write_byte) && (3'd0==cs1_write_count);
	assign cs1_write_load[3]		= cs1_write_req && (2'd0==cs1_write_byte) && (3'd0==cs1_write_count);
	assign cs1_write_addr			= (cs1_write_req) ? {write_address[22:2],cs1_write_byte[1:0]}: 23'd0;
	assign cs1_write_fin			= cs1_write_req && (2'd3==cs1_write_byte) && (3'd7==cs1_write_count);
	always @(posedge clk or posedge rst)
		if (rst)
		 			cs1_write_count	<= 3'd0;
		else if (!cs1_write_req)
			cs1_write_count	<= 3'd0;
		else
						cs1_write_count	<= (cs1_write_count_full) ? 3'd0: {cs1_write_count + 3'd1};	
	always @(posedge clk or posedge rst)
		if (rst)
					cs1_write_byte	<= 2'd0;
		else if (!cs1_write_req)
			cs1_write_byte	<= 2'd0;
		else if (cs1_write_count_full)
			cs1_write_byte	<= (cs1_write_byte_full) ? 2'd0: {cs1_write_byte + 2'd1};
	wire		cs1_read_count_full;
	wire		cs1_read_byte_full;
	wire		cs1_read_cs;
	wire		cs1_read_strobe;
	wire	[3:0]	cs1_read_load;
	wire	[22:0]	cs1_read_addr;
	wire		cs1_read_fin;
	reg	[2:0]	cs1_read_count;
	reg	[1:0]	cs1_read_byte;
	assign cs1_read_count_full		= (3'd7==cs1_read_count);
	assign cs1_read_byte_full		= (2'd3==cs1_read_byte);
	assign cs1_read_cs			= cs1_read_req                          && (3'd0!=cs1_read_count)                                                     && (3'd7!=cs1_read_count);
	assign cs1_read_strobe			= cs1_read_req                          && (3'd0!=cs1_read_count) && (3'd1!=cs1_read_count) && (3'd6!=cs1_read_count) && (3'd7!=cs1_read_count)
						&& (
							( (2'd0==cs1_read_byte) && read_byte[3] )
							||
							( (2'd1==cs1_read_byte) && read_byte[2] )
							||
							( (2'd2==cs1_read_byte) && read_byte[1] )
							||
							( (2'd3==cs1_read_byte) && read_byte[0] )
						);	
	assign cs1_read_load[0]			= cs1_read_req && (2'd3==cs1_read_byte) && (3'd7==cs1_read_count);
	assign cs1_read_load[1]			= cs1_read_req && (2'd2==cs1_read_byte) && (3'd7==cs1_read_count);
	assign cs1_read_load[2]			= cs1_read_req && (2'd1==cs1_read_byte) && (3'd7==cs1_read_count);
	assign cs1_read_load[3]			= cs1_read_req && (2'd0==cs1_read_byte) && (3'd7==cs1_read_count);
	assign cs1_read_addr			= (cs1_read_req) ? {read_address[22:2],cs1_read_byte[1:0]}: 23'd0;
	assign cs1_read_fin			= cs1_read_req && (2'd3==cs1_read_byte) && (3'd7==cs1_read_count);
	always @(posedge clk or posedge rst)
		if (rst)
		 			cs1_read_count	<= 3'd0;
		else if (!cs1_read_req)
				cs1_read_count	<= 3'd0;
		else
						cs1_read_count	<= (cs1_read_count_full) ? 3'd0: {cs1_read_count + 3'd1};	
	always @(posedge clk or posedge rst)
		if (rst)
					cs1_read_byte	<= 2'd0;
		else if (!cs1_read_req)
				cs1_read_byte	<= 2'd0;
		else if (cs1_read_count_full)
			cs1_read_byte	<= (cs1_read_byte_full) ? 2'd0: {cs1_read_byte + 2'd1};
	reg		mem_cs1_n;
	reg		mem_cs1_rst_n;
	always @(posedge clk or posedge rst)
		if (rst)
			mem_cs1_n	<= 1'b1;
		else
			mem_cs1_n	<= !(cs1_write_cs||cs1_read_cs);
	always @(posedge clk or posedge rst)
		if (rst)
			mem_cs1_rst_n	<= 1'b0;
		else
			mem_cs1_rst_n	<= 1'b1;
	wire		cs2_write_count_full;
	wire		cs2_write_byte_full;
	wire		cs2_write_cs;
	wire		cs2_write_strobe;
	wire	[3:0]	cs2_write_load;
	wire	[22:0]	cs2_write_addr;
	wire		cs2_write_fin;
	reg	[2:0]	cs2_write_count;
	reg	[1:0]	cs2_write_byte;
	assign cs2_write_count_full		= (3'd7==cs2_write_count);
	assign cs2_write_byte_full		= (2'd3==cs2_write_byte);
	assign cs2_write_cs			= cs2_write_req                           && (3'd0!=cs2_write_count)                                                       && (3'd7!=cs2_write_count);
	assign cs2_write_strobe			= cs2_write_req                           && (3'd0!=cs2_write_count) && (3'd1!=cs2_write_count) && (3'd6!=cs2_write_count) && (3'd7!=cs2_write_count)
						&& (
							( (2'd0==cs2_write_byte) && write_byte[3] )
							||
							( (2'd1==cs2_write_byte) && write_byte[2] )
							||
							( (2'd2==cs2_write_byte) && write_byte[1] )
							||
							( (2'd3==cs2_write_byte) && write_byte[0] )
						);
	assign cs2_write_load[0]		= cs2_write_req && (2'd3==cs2_write_byte) && (3'd0==cs2_write_count);
	assign cs2_write_load[1]		= cs2_write_req && (2'd2==cs2_write_byte) && (3'd0==cs2_write_count);
	assign cs2_write_load[2]		= cs2_write_req && (2'd1==cs2_write_byte) && (3'd0==cs2_write_count);
	assign cs2_write_load[3]		= cs2_write_req && (2'd0==cs2_write_byte) && (3'd0==cs2_write_count);
	assign cs2_write_addr			= (cs2_write_req) ? {write_address[22:2],cs2_write_byte[1:0]}: 23'd0;
	assign cs2_write_fin			= cs2_write_req && (2'd3==cs2_write_byte) && (3'd7==cs2_write_count);
	always @(posedge clk or posedge rst)
		if (rst)
		 	cs2_write_count	<= 3'd0;
		else if (!cs2_write_req)
			cs2_write_count	<= 3'd0;
		else
			cs2_write_count	<= (cs2_write_count_full) ? 3'd0: {cs2_write_count + 3'd1};	
	always @(posedge clk or posedge rst)
		if (rst)
				cs2_write_byte	<= 2'd0;
		else if (!cs2_write_req)
			cs2_write_byte	<= 2'd0;
		else if (cs2_write_count_full)
			cs2_write_byte	<= (cs2_write_byte_full) ? 2'd0: {cs2_write_byte + 2'd1};
	wire		cs2_read_count_full;
	wire		cs2_read_byte_full;
	wire		cs2_read_cs;
	wire		cs2_read_strobe;
	wire	[3:0]	cs2_read_load;
	wire	[22:0]	cs2_read_addr;
	wire		cs2_read_fin;
	reg	[2:0]	cs2_read_count;
	reg	[1:0]	cs2_read_byte;
	assign cs2_read_count_full		= (3'd7==cs2_read_count);
	assign cs2_read_byte_full		= (2'd3==cs2_read_byte);
	assign cs2_read_cs			= cs2_read_req                          && (3'd0!=cs2_read_count)                                                     && (3'd7!=cs2_read_count);
	assign cs2_read_strobe			= cs2_read_req                          && (3'd0!=cs2_read_count) && (3'd1!=cs2_read_count) && (3'd6!=cs2_read_count) && (3'd7!=cs2_read_count)
						&& (
							( (2'd0==cs2_read_byte) && read_byte[3] )
							||
							( (2'd1==cs2_read_byte) && read_byte[2] )
							||
							( (2'd2==cs2_read_byte) && read_byte[1] )
							||
							( (2'd3==cs2_read_byte) && read_byte[0] )
						);	
	assign cs2_read_load[0]			= cs2_read_req && (2'd3==cs2_read_byte) && (3'd7==cs2_read_count);
	assign cs2_read_load[1]			= cs2_read_req && (2'd2==cs2_read_byte) && (3'd7==cs2_read_count);
	assign cs2_read_load[2]			= cs2_read_req && (2'd1==cs2_read_byte) && (3'd7==cs2_read_count);
	assign cs2_read_load[3]			= cs2_read_req && (2'd0==cs2_read_byte) && (3'd7==cs2_read_count);
	assign cs2_read_fin			= cs2_read_req && (2'd3==cs2_read_byte) && (3'd7==cs2_read_count);
	assign cs2_read_addr			= (cs2_read_req) ? {read_address[22:2],cs2_read_byte[1:0]}: 23'd0;
	always @(posedge clk or posedge rst)
		if (rst)
		 		cs2_read_count	<= 3'd0;
		else if (!cs2_read_req)
				cs2_read_count	<= 3'd0;
		else
				cs2_read_count	<= (cs2_read_count_full) ? 3'd0: {cs2_read_count + 3'd1};	
	always @(posedge clk or posedge rst)
		if (rst)
				cs2_read_byte	<= 2'd0;
		else if (!cs2_read_req)
				cs2_read_byte	<= 2'd0;
		else if (cs2_read_count_full)
			cs2_read_byte	<= (cs2_read_byte_full) ? 2'd0: {cs2_read_byte + 2'd1};
	reg		mem_cs2_n;
	reg		mem_cs2_g_n;
	reg		mem_cs2_dir;
	reg		mem_cs2_rstdrv;
	always @(posedge clk or posedge rst)
		if (rst)
			mem_cs2_n	<= 1'b1;
		else
			mem_cs2_n	<= !(cs2_write_cs||cs2_read_cs);
	always @(posedge clk or posedge rst)
		if (rst)
			mem_cs2_g_n	<= 1'b1;
		else
			mem_cs2_g_n	<= !(cs2_write_cs||cs2_read_strobe);
	always @(posedge clk or posedge rst)
		if (rst)
			mem_cs2_dir	<= 1'b1;
		else
			mem_cs2_dir	<= (cs2_write_req) ? 1'b1: (cs2_read_req) ? 1'b0: mem_cs2_dir;
	always @(posedge clk or posedge rst)
		if (rst)
			mem_cs2_rstdrv	<= 1'b1;
		else
			mem_cs2_rstdrv	<= 1'b0;
	wire		write_strobe;
	wire		read_strobe;
	wire	[3:0]	write_load;
	wire	[3:0]	read_load;
	wire	[22:0]	write_addr;
	wire	[22:0]	read_addr;
	assign write_strobe	= cs2_write_strobe || cs1_write_strobe || cs0_write_strobe;
	assign read_strobe	= cs2_read_strobe || cs1_read_strobe || cs0_read_strobe;
	assign write_load	= cs2_write_load|cs1_write_load|cs0_write_load;
	assign read_load	= cs2_read_load |cs1_read_load |cs0_read_load;
	assign write_addr	= cs2_write_addr|cs1_write_addr|cs0_write_addr;
	assign read_addr	= cs2_read_addr |cs1_read_addr |cs0_read_addr;
	reg		mem_we_n;
	reg		mem_oe_n;
	reg	[22:0]	mem_a;
	reg	[7:0]	mem_d_oe;
	always @(posedge clk or posedge rst)
		if (rst)
			mem_we_n	<= 1'b1;
		else
			mem_we_n	<= !write_strobe;
	always @(posedge clk or posedge rst)
		if (rst)
			mem_oe_n	<= 1'b1;
		else
			mem_oe_n	<= !read_strobe;
	always @(posedge clk or posedge rst)
		if (rst)
			mem_a		<= 23'h00_0000;
		else
			mem_a		<= write_addr|read_addr;
	always @(posedge clk or posedge rst)
		if (rst)
				mem_d_oe	<= 8'h00;
       		else
				mem_d_oe	<= {8{cs2_write_cs||cs1_write_cs||cs0_write_cs}}; 
	reg	[7:0]	pre_mem_d_o;
	always @(posedge clk or posedge rst)
		if (rst)			pre_mem_d_o	<= 32'h0000_0000;
		else begin
			if (write_load[3])	pre_mem_d_o	<= write_data[31:24];
			if (write_load[2])	pre_mem_d_o	<= write_data[23:16];
			if (write_load[1])	pre_mem_d_o	<= write_data[15: 8];
			if (write_load[0])	pre_mem_d_o	<= write_data[ 7: 0];
		end
	reg	[7:0]	mem_d_o; 
	always @(posedge clk or posedge rst)
		if (rst)
					mem_d_o		<= 8'h00;
		else
						mem_d_o		<= pre_mem_d_o;
	reg	[7:0]	pre_mem_d_i; 
	always @(posedge clk or posedge rst)
		if (rst)
					pre_mem_d_i	<= 8'h00;
		else
						pre_mem_d_i	<= mem_d_i;
	reg	[31:0]	read_data;
	always @(posedge clk or posedge rst)
		if (rst)			read_data	<= 32'h0000_0000;
		else begin
			if (read_load[3])	read_data[31:24] <= pre_mem_d_i;
			if (read_load[2])	read_data[23:16] <= pre_mem_d_i;
			if (read_load[1])	read_data[15: 8] <= pre_mem_d_i;
			if (read_load[0])	read_data[ 7: 0] <= pre_mem_d_i;
		end
	assign write_fin	= cs2_write_fin || cs1_write_fin || cs0_write_fin;
	always @(posedge clk or posedge rst)
		if (rst)
				write_ack <= 1'b0;
		else if (!write_req)
			write_ack <= 1'b0;
		else if (write_fin)
			write_ack <= 1'b1;
	assign read_fin		= cs2_read_fin || cs1_read_fin || cs0_read_fin;
	always @(posedge clk or posedge rst)
		if (rst)
				read_ack <= 1'b0;
		else if (!read_req)
			read_ack <= 1'b0;
		else if (read_fin)
			read_ack <= 1'b1;
endmodule