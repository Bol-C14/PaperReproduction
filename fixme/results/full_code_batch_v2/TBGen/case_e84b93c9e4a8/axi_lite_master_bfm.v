`timescale 1ns/1ps

module axi_lite_master_bfm #
   (
    parameter integer C_M_AXI_ADDR_WIDTH = 32,
    parameter integer C_M_AXI_DATA_WIDTH = 32
    )
   (
    input wire M_AXI_ACLK,
    input wire M_AXI_ARESETN,
    output wire [C_M_AXI_ADDR_WIDTH-1:0] M_AXI_AWADDR,
    output wire [3-1:0] M_AXI_AWPROT,
    output wire M_AXI_AWVALID,
    input wire M_AXI_AWREADY,
    output wire [C_M_AXI_DATA_WIDTH-1:0] M_AXI_WDATA,
    output wire [C_M_AXI_DATA_WIDTH/8-1:0] M_AXI_WSTRB,
    output wire M_AXI_WVALID,
    input wire M_AXI_WREADY,
    input wire [2-1:0] M_AXI_BRESP,
    input wire M_AXI_BVALID,
    output wire M_AXI_BREADY,
    output wire [C_M_AXI_ADDR_WIDTH-1:0] M_AXI_ARADDR,
    output wire [3-1:0] M_AXI_ARPROT,
    output wire M_AXI_ARVALID,
    input wire M_AXI_ARREADY,
    input wire [C_M_AXI_DATA_WIDTH-1:0] M_AXI_RDATA,
    input wire [2-1:0] M_AXI_RRESP,
    input wire M_AXI_RVALID,
    output wire M_AXI_RREADY,
    input wire INTR_IN
    );
   reg 		awvalid;
   reg 		wvalid;
   reg 		push_write;
   reg 		pop_read;
   reg          arvalid;
   reg          rready;
   reg          bready;
   reg [31:0] 	awaddr;
   reg [31:0] 	wdata;
   reg [31:0] 	araddr;
   wire 	write_resp_error;
   wire         read_resp_error;
assign M_AXI_AWADDR = awaddr;
assign M_AXI_WDATA = wdata;
assign M_AXI_AWPROT = 3'h0;
assign M_AXI_AWVALID = awvalid;
assign M_AXI_WVALID = wvalid;
assign M_AXI_WSTRB = -1;
assign M_AXI_BREADY = bready;
assign M_AXI_ARADDR = araddr;
assign M_AXI_ARVALID = arvalid;
assign M_AXI_ARPROT = 3'b0;
assign M_AXI_RREADY = rready;
always @(posedge M_AXI_ACLK)
  begin
     if (M_AXI_ARESETN == 0 )
       awvalid <= 1'b0;
     else if (M_AXI_AWREADY && awvalid)
       awvalid <= 1'b0;
     else if (push_write)
       awvalid <= 1'b1;
     else
       awvalid <= awvalid;
  end 
   always @(posedge M_AXI_ACLK)
  begin
      if (M_AXI_ARESETN == 0 )
	wvalid <= 1'b0;
      else if (M_AXI_WREADY && wvalid)
	wvalid <= 1'b0;
     else if (push_write)
       wvalid <= 1'b1;
     else
       wvalid <= awvalid;
  end 
always @(posedge M_AXI_ACLK)
  begin
     if (M_AXI_ARESETN == 0)
 	  bready <= 1'b0;
      else
 	  bready <= 1'b1;
  end
assign write_resp_error = bready & M_AXI_BVALID & M_AXI_BRESP[1];
always @(posedge M_AXI_ACLK)
  begin
     if (M_AXI_ARESETN == 0 )
       arvalid <= 1'b0;
     else if (M_AXI_ARREADY && arvalid)
       arvalid <= 1'b0;
     else if (pop_read)
       arvalid <= 1'b1;
     else
       arvalid <= arvalid;
  end 
always @(posedge M_AXI_ACLK)
  begin
     if (M_AXI_ARESETN == 0)
 	  rready <= 1'b0;
      else
 	  rready <= 1'b1;
   end
assign read_resp_error = rready & M_AXI_RVALID & M_AXI_RRESP[1];  
task axi4_wr_req(input [31:0]addr, input [31:0]data);
integer i;
begin
  $write("axi4_wr %08x", addr);
  $write(" %08x", data);
  for (i=0; i<1; i=i+1) @(posedge M_AXI_ACLK);
  awaddr     = addr;
  wdata      = data;
  push_write = 1'b1;
  for (i=0; i<1; i=i+1) @(posedge M_AXI_ACLK);
  awaddr     = addr;
  wdata      = data;
  push_write = 1'b0;
  for (i=0; i<1; i=i+1) @(posedge M_AXI_ACLK);
  @(~awvalid && ~wvalid);
end
endtask
task axi4_rd_req(input [31:0]addr);
integer i;
begin
  $write("axi4_rd %08x", addr);
  for (i=0; i<1; i=i+1) @(posedge M_AXI_ACLK);
  araddr   = addr;
  pop_read = 1'b1;
  for (i=0; i<1; i=i+1) @(posedge M_AXI_ACLK);
  araddr   = addr;
  pop_read = 1'b0;
  for (i=0; i<1; i=i+1) @(posedge M_AXI_ACLK);
  @(~arvalid);
end
endtask
task axi4_wr_ack;
begin
  @(M_AXI_BVALID && bready);
  @(posedge M_AXI_ACLK);
  $write(" W_RESP: %08x
", M_AXI_BRESP);
end
endtask
task axi4_rd_ack;
begin
  @(M_AXI_RVALID && rready);
  @(posedge M_AXI_ACLK);
  $write(" %08x", M_AXI_RDATA);
  $write(" R_RESP: %08x
", M_AXI_RRESP);
end
endtask
initial begin
  #300;
  @(posedge M_AXI_ACLK);
  axi4_wr_req(32'h00000004,32'h12345678);axi4_wr_ack;
  axi4_rd_req(32'h00000004             );axi4_rd_ack;
end
endmodule
