`timescale 1ns/1ps
 
module	ref_writeqspi(i_clk, i_wreq, i_ereq, i_pipewr, i_endpipe, i_addr, i_data,
			ref_o_bus_ack, ref_o_qspi_req, i_qspi_grant,
				ref_o_spi_wr, ref_o_spi_hold, ref_o_spi_word, ref_o_spi_len,
				ref_o_spi_spd, ref_o_spi_dir, i_spi_data, i_spi_valid,
					i_spi_busy, i_spi_stopped,
				ref_o_data_ack, i_quad, ref_o_wip);
	input		i_clk;
	input		i_wreq, i_ereq, i_pipewr, i_endpipe;
	input		[21:0]	i_addr;
	input		[31:0]	i_data;
	output	reg		ref_o_bus_ack, ref_o_qspi_req;
	input			i_qspi_grant;
	output	reg		ref_o_spi_wr, ref_o_spi_hold;
	output	reg	[31:0]	ref_o_spi_word;
	output	reg	[1:0]	ref_o_spi_len;
	output	reg		ref_o_spi_spd, ref_o_spi_dir;
	input		[31:0]	i_spi_data;
	input			i_spi_valid;
	input			i_spi_busy, i_spi_stopped;
	output	reg		ref_o_data_ack;
	input			i_quad;
	output	reg		ref_o_wip;
`ifdef	QSPI_READ_ONLY
	always @(posedge i_clk)
		ref_o_data_ack <= (i_wreq)||(i_ereq);
	always @(posedge i_clk)
		ref_o_bus_ack <= (i_wreq)||(i_ereq);
	always @(posedge i_clk)
	begin
		ref_o_qspi_req <= 1'b0;
		ref_o_spi_wr   <= 1'b0;
		ref_o_spi_hold <= 1'b0;
		ref_o_spi_dir  <= 1'b1; 
		ref_o_spi_spd  <= i_quad;
		ref_o_spi_len  <= 2'b00;
		ref_o_spi_word <= 32'h00;
		ref_o_wip <= 1'b0;
	end
`else
`define	WR_IDLE				4'h0
`define	WR_START_WRITE			4'h1
`define	WR_START_QWRITE			4'h2
`define	WR_PROGRAM			4'h3
`define	WR_PROGRAM_GETNEXT		4'h4
`define	WR_START_ERASE			4'h5
`define	WR_WAIT_ON_STOP			4'h6
`define	WR_REQUEST_STATUS		4'h7
`define	WR_REQUEST_STATUS_NEXT		4'h8
`define	WR_READ_STATUS			4'h9
`define	WR_WAIT_ON_FINAL_STOP		4'ha
	reg	accepted;
	initial	accepted = 1'b0;
	always @(posedge i_clk)
		accepted <= (~i_spi_busy)&&(i_qspi_grant)&&(ref_o_spi_wr)&&(~accepted);
	reg		cyc, chk_wip, valid_status;
	reg	[3:0]	wr_state;
	initial	wr_state = `WR_IDLE;
	initial	cyc = 1'b0;
	always @(posedge i_clk)
	begin
		chk_wip <= 1'b0;
		ref_o_bus_ack  <= 1'b0;
		ref_o_data_ack <= 1'b0;
		case(wr_state)
		`WR_IDLE: begin
			valid_status <= 1'b0;
			ref_o_qspi_req <= 1'b0;
			cyc <= 1'b0;
			if (i_ereq)
				wr_state <= `WR_START_ERASE;
			else if (i_wreq)
				wr_state <= (i_quad)?`WR_START_QWRITE
					: `WR_START_WRITE;
			end
		`WR_START_WRITE: begin
			ref_o_wip      <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_wr   <= 1'b1;
			ref_o_spi_dir  <= 1'b0;
			ref_o_spi_len  <= 2'b11;
			ref_o_spi_spd  <= 1'b0;
			ref_o_spi_hold <= 1'b1;
			ref_o_spi_word <= { 8'h02, i_addr, 2'b00 };
			cyc <= 1'b1;
			if (accepted)
			begin
				ref_o_bus_ack  <= 1'b1;
				ref_o_data_ack <= 1'b1;
				wr_state <= `WR_PROGRAM;
				ref_o_spi_word <= i_data;
			end end
		`WR_START_QWRITE: begin
			ref_o_wip      <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_wr   <= 1'b1;
			ref_o_spi_dir  <= 1'b0;
			ref_o_spi_len  <= 2'b11;
			ref_o_spi_spd  <= 1'b0;
			ref_o_spi_hold <= 1'b1;
			ref_o_spi_word <= { 8'h32, i_addr, 2'b00 };
			cyc <= 1'b1;
			if (accepted)
			begin
				ref_o_bus_ack  <= 1'b1;
				ref_o_data_ack <= 1'b1;
				wr_state <= `WR_PROGRAM;
				ref_o_spi_word <= i_data;
			end end
		`WR_PROGRAM: begin
			ref_o_wip     <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_wr   <= 1'b1;
			ref_o_spi_dir  <= 1'b0;
			ref_o_spi_len  <= 2'b11;
			ref_o_spi_spd  <= i_quad;
			ref_o_spi_hold <= 1'b1;
			if (accepted)
				wr_state <= `WR_PROGRAM_GETNEXT;
			end
		`WR_PROGRAM_GETNEXT: begin
			ref_o_wip      <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_wr   <= 1'b0;
			ref_o_spi_dir  <= 1'b0;
			ref_o_spi_len  <= 2'b11;
			ref_o_spi_spd  <= i_quad;
			ref_o_spi_hold <= 1'b1;
			ref_o_spi_word <= i_data;
			cyc <= (cyc)&&(~i_endpipe);
			if (~cyc)
				wr_state <= `WR_WAIT_ON_STOP;
			else if (i_pipewr)
			begin
				ref_o_bus_ack  <= 1'b1;
				ref_o_data_ack <= 1'b1;
				wr_state <= `WR_PROGRAM;
			end end
		`WR_START_ERASE: begin
			ref_o_wip <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_wr  <= 1'b1;
			ref_o_spi_dir <= 1'b0;
			ref_o_spi_spd <= 1'b0;
			ref_o_spi_len <= 2'b11;
			if (i_data[28])
				ref_o_spi_word[31:24] <= 8'h20;
			else
				ref_o_spi_word[31:24] <= 8'hd8;
			ref_o_spi_word[23:0] <= { i_data[21:10], 12'h0 };
			ref_o_bus_ack <= accepted;
			if (accepted)
				wr_state <= `WR_WAIT_ON_STOP;
			end
		`WR_WAIT_ON_STOP: begin
			ref_o_wip <= 1'b1;
			ref_o_qspi_req <= 1'b0;
			ref_o_spi_wr   <= 1'b0;
			ref_o_spi_hold <= 1'b0;
			if (i_spi_stopped)
				wr_state <= `WR_REQUEST_STATUS;
			end
		`WR_REQUEST_STATUS: begin
			ref_o_wip <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_hold <= 1'b0;
			ref_o_spi_wr   <= 1'b1;
			ref_o_spi_spd  <= 1'b0; 
			ref_o_spi_len  <= 2'b00; 
			ref_o_spi_dir  <= 1'b0; 
			ref_o_spi_word <= { 8'h05, 24'h00 };
			if (accepted)
				wr_state <= `WR_REQUEST_STATUS_NEXT;
			end
		`WR_REQUEST_STATUS_NEXT: begin
			ref_o_wip <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_hold <= 1'b0;
			ref_o_spi_wr   <= 1'b1;
			ref_o_spi_spd  <= 1'b0; 
			ref_o_spi_len  <= 2'b00; 
			ref_o_spi_dir  <= 1'b1; 
			ref_o_spi_word <= 32'h00;
			if (accepted)
				wr_state <= `WR_READ_STATUS;
			valid_status <= 1'b0;
			end
		`WR_READ_STATUS: begin
			ref_o_wip <= 1'b1;
			ref_o_qspi_req <= 1'b1;
			ref_o_spi_hold <= 1'b0;
			ref_o_spi_wr   <= 1'b1;
			ref_o_spi_spd  <= 1'b0; 
			ref_o_spi_len  <= 2'b00; 
			ref_o_spi_dir  <= 1'b1; 
			ref_o_spi_word <= 32'h00;
			if (i_spi_valid)
				valid_status <= 1'b1;
			if ((i_spi_valid)&&(valid_status))
				chk_wip <= 1'b1;
			if ((chk_wip)&&(~i_spi_data[0]))
				wr_state <= `WR_WAIT_ON_FINAL_STOP;
			end
		default: begin
			ref_o_qspi_req <= 1'b0;
			ref_o_spi_wr <= 1'b0;
			ref_o_wip <= 1'b0;
			if (i_spi_stopped)
				wr_state <= `WR_IDLE;
			end
		endcase
	end
`endif
endmodule

