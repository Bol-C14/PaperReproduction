`timescale 1ns/1ps
module oracle_aximwr2wbsp #(
	parameter C_AXI_ID_WIDTH	= 6, 
	parameter C_AXI_DATA_WIDTH	= 32,
	parameter C_AXI_ADDR_WIDTH	= 28,	
	parameter AW			= 26,
	parameter LGFIFO                =  4
	) (
	input	wire			i_axi_clk,	
	input	wire			i_axi_reset_n,
	output	wire			o_axi_awready, 
	input	wire	[C_AXI_ID_WIDTH-1:0]	i_axi_awid,	
	input	wire	[C_AXI_ADDR_WIDTH-1:0]	i_axi_awaddr,	
	input	wire	[7:0]		i_axi_awlen,	
	input	wire	[2:0]		i_axi_awsize,	
	input	wire	[1:0]		i_axi_awburst,	
	input	wire	[0:0]		i_axi_awlock,	
	input	wire	[3:0]		i_axi_awcache,	
	input	wire	[2:0]		i_axi_awprot,	
	input	wire	[3:0]		i_axi_awqos,	
	input	wire			i_axi_awvalid,	
	output	wire			o_axi_wready,  
	input	wire	[C_AXI_DATA_WIDTH-1:0]	i_axi_wdata,	
	input	wire	[C_AXI_DATA_WIDTH/8-1:0] i_axi_wstrb,	
	input	wire			i_axi_wlast,	
	input	wire			i_axi_wvalid,	
	output	wire [C_AXI_ID_WIDTH-1:0] o_axi_bid,	
	output	wire [1:0]		o_axi_bresp,	
	output	wire			o_axi_bvalid,  
	input	wire			i_axi_bready,  
	output	reg			o_wb_cyc,
	output	reg			o_wb_stb,
	output	wire [(AW-1):0]		o_wb_addr,
	output	wire [(C_AXI_DATA_WIDTH-1):0]	o_wb_data,
	output	wire [(C_AXI_DATA_WIDTH/8-1):0]	o_wb_sel,
	input	wire			i_wb_ack,
	input	wire			i_wb_stall,
	input	wire			i_wb_err
`ifdef	FORMAL
	,
	output	wire	[LGFIFO-1:0]	f_fifo_ahead,
	output	wire	[LGFIFO-1:0]	f_fifo_dhead,
	output	wire	[LGFIFO-1:0]	f_fifo_neck,
	output	wire	[LGFIFO-1:0]	f_fifo_torso,
	output	wire	[LGFIFO-1:0]	f_fifo_tail
`endif
);
	localparam	DW = C_AXI_DATA_WIDTH;
	wire	w_reset;
	assign	w_reset = (i_axi_reset_n == 1'b0);
	reg	[LGFIFO-1:0]	fifo_ahead, fifo_dhead, fifo_neck, fifo_torso,
				fifo_tail;
	wire	[LGFIFO-1:0]	next_ahead, next_dhead, next_neck, next_torso,
				next_tail;
	assign	next_ahead = fifo_ahead + 1;
	assign	next_dhead = fifo_dhead + 1;
	assign	next_neck  = fifo_neck  + 1;
	assign	next_torso = fifo_torso + 1;
	assign	next_tail  = fifo_tail  + 1;
	reg	[(C_AXI_ID_WIDTH+AW)-1:0]	afifo	[0:((1<<(LGFIFO))-1)];
	reg	[(DW + DW/8)-1:0]		dfifo	[0:((1<<(LGFIFO))-1)];
	reg	[((1<<(LGFIFO))-1):0]		efifo;
	reg	[(C_AXI_ID_WIDTH+AW)-1:0]	afifo_at_neck, afifo_at_tail;
	reg	[(DW + DW/8)-1:0]		dfifo_at_neck;
	reg					efifo_at_tail;
	reg	filling_fifo, incr;
	reg	[7:0]	len;
	reg	[(AW-1):0]	wr_fifo_addr;
	reg	[(C_AXI_ID_WIDTH-1):0]	wr_fifo_id;
	wire	axi_aw_req, axi_wr_req, axi_wr_ack;
	assign	axi_aw_req = (o_axi_awready)&&(i_axi_awvalid);
	assign	axi_wr_req = (o_axi_wready)&&(i_axi_wvalid);
	assign	axi_wr_ack = (o_axi_bvalid)&&(i_axi_bready);
	wire	fifo_full;
	assign	fifo_full = (next_ahead == fifo_tail)||(next_dhead ==fifo_tail);
	initial	fifo_ahead = 0;
	initial	fifo_dhead = 0;
	always @(posedge i_axi_clk)
	begin
		if (filling_fifo)
		begin
			if (!fifo_full)
			begin
				len <= len - 1;
				if (len == 1)
					filling_fifo <= 1'b0;
				fifo_ahead <= next_ahead;
				wr_fifo_addr <= wr_fifo_addr
					+ {{(AW-1){1'b0}},incr};
			end
		end else begin
			wr_fifo_addr <= i_axi_awaddr[(C_AXI_ADDR_WIDTH-1):(C_AXI_ADDR_WIDTH-AW)];
			wr_fifo_id   <= i_axi_awid;
			incr         <= i_axi_awburst[0];
			if (axi_aw_req)
			begin
				fifo_ahead <= next_ahead;
				len <= i_axi_awlen;
				filling_fifo <= (i_axi_awlen != 0);
			end
		end
		if (w_reset)
		begin
			fifo_ahead <= 0;
			len <= 0;
			filling_fifo <= 0;
		end
	end
	always @(posedge i_axi_clk)
		afifo[fifo_ahead] <= { wr_fifo_id, wr_fifo_addr };
	initial	fifo_dhead = 0;
	always @(posedge i_axi_clk)
		if (w_reset)
			fifo_dhead <= 0;
		else if (axi_wr_req)
			fifo_dhead <= next_dhead;
	always @(posedge i_axi_clk)
		dfifo[fifo_dhead] <= { i_axi_wstrb, i_axi_wdata };
	reg	err_state;
	initial	o_wb_cyc   = 0;
	initial o_wb_stb   = 0;
	initial fifo_neck  = 0;
	initial fifo_torso = 0;
	initial err_state  = 0;
	always @(posedge i_axi_clk)
	begin
		if (w_reset)
		begin
			o_wb_cyc <= 0;
			o_wb_stb <= 0;
			fifo_neck <= 0;
			fifo_torso <= 0;
			err_state <= 0;
		end else if (o_wb_stb)
		begin
			if (i_wb_err)
			begin
				o_wb_cyc <= 1'b0;
				o_wb_stb <= 1'b0;
				err_state <= 1'b1;
			end else if (!i_wb_stall)
				o_wb_stb <= (fifo_ahead != next_neck)
					&&(fifo_dhead != next_neck);
			if ((!i_wb_stall)&&(fifo_neck != fifo_ahead)&&(fifo_neck != fifo_dhead))
				fifo_neck <= next_neck;
			if (i_wb_ack)
				fifo_torso <= next_torso;
			if (fifo_neck == next_torso)
				o_wb_cyc <= 1'b0;
		end else if ((err_state)||(i_wb_err))
		begin
			o_wb_cyc <= 1'b0;
			o_wb_stb <= 1'b0;
			err_state <= (err_state)||(i_wb_err);
			if ((o_wb_cyc)&&(fifo_torso != fifo_neck))
				fifo_torso <= next_torso;
			if (fifo_neck == next_torso)
				err_state <= 1'b0;
		end else if (o_wb_cyc)
		begin
			if (i_wb_ack)
				fifo_torso <= next_torso;
			if (fifo_neck == next_torso)
				o_wb_cyc <= 1'b0;
		end else if((fifo_ahead!= fifo_neck)
				&&(fifo_dhead != fifo_neck))
		begin
			o_wb_cyc <= 1;
			o_wb_stb <= 1;
		end
	end
	initial	efifo = 0;
	always @(posedge i_axi_clk)
		if(w_reset)
			efifo <= 0;
		else
			efifo[fifo_torso] <= (i_wb_err)||(err_state);
	always @(posedge i_axi_clk)
		afifo_at_neck <= afifo[fifo_neck];
	assign	o_wb_addr = afifo_at_neck[(AW-1):0];
	always @(posedge i_axi_clk)
		dfifo_at_neck <= dfifo[fifo_neck];
	assign	o_wb_data = dfifo_at_neck[DW-1:0];
	assign	o_wb_sel  = dfifo_at_neck[(DW+(DW/8))-1:DW];
	initial	fifo_tail = 0;
	always @(posedge i_axi_clk)
		if (w_reset)
			fifo_tail <= 0;
		else if (axi_wr_ack)
			fifo_tail <= next_tail;
	always @(posedge i_axi_clk)
		afifo_at_tail <= afifo[fifo_tail];
	always @(posedge i_axi_clk)
		efifo_at_tail <= efifo[fifo_tail];
	assign	o_axi_bid   = afifo_at_tail[(C_AXI_ID_WIDTH+AW)-1:AW];
	assign	o_axi_bresp = {(2){efifo_at_tail}};
	assign	o_axi_bvalid  = (fifo_tail  != fifo_torso);
	assign	o_axi_awready = (next_ahead != fifo_tail);
	assign	o_axi_wready  = (next_dhead != fifo_tail);
	wire	[(C_AXI_ID_WIDTH+AW+C_AXI_ADDR_WIDTH-AW)
		+(1)+1+3+1+4+3+4-1:0]	unused;
	assign	unused = { i_axi_awburst[1], i_axi_awsize,
			i_axi_awlock, i_axi_awcache, i_axi_awprot,
			i_axi_awqos, i_axi_wlast,
			afifo_at_neck[(C_AXI_ID_WIDTH+AW-1):AW],
			afifo_at_tail[(AW-1):0],
			i_axi_awaddr[(C_AXI_ADDR_WIDTH-AW)-1:0] };
`ifdef	FORMAL
	always @(*)
		assume(!i_axi_awburst[1]);
	reg	f_past_valid;
	initial	f_past_valid = 1'b0;
	always @(posedge i_axi_clk)
		f_past_valid <= 1'b1;
	wire	[LGFIFO-1:0]	f_afifo_used, f_dfifo_used,
				f_fifo_neck_used, f_fifo_torso_used;
	assign	f_afifo_used      = fifo_ahead - fifo_tail;
	assign	f_dfifo_used      = fifo_dhead - fifo_tail;
	assign	f_fifo_neck_used  = fifo_dhead - fifo_neck;
	assign	f_fifo_torso_used = fifo_dhead - fifo_torso;
	always @(*)
		assert((f_afifo_used < {(LGFIFO){1'b1}})||(!o_axi_awready));
	always @(*)
		assert((f_dfifo_used < {(LGFIFO){1'b1}})||(!o_axi_wready));
	always @(*)
		assert(f_fifo_neck_used  <= f_dfifo_used);
	always @(*)
		assert(f_fifo_torso_used <= f_dfifo_used);
	always @(*)
		assert((!o_wb_stb)||
			((fifo_neck != fifo_ahead)
				&&(fifo_neck != fifo_dhead)));
	assign	f_fifo_ahead = fifo_ahead;
	assign	f_fifo_dhead = fifo_dhead;
	assign	f_fifo_neck  = fifo_neck;
	assign	f_fifo_torso = fifo_torso;
	assign	f_fifo_tail  = fifo_tail;
	always @(*)
		if (i_axi_awvalid)
			assert(!i_axi_awburst[1]);
`endif
endmodule