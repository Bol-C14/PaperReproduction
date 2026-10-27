`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_req;
reg i_write;
reg [127:0] i_wdata;
reg [15:0] i_be;
reg [31:0] i_addr;
wire [127:0] o_rdata;
wire [127:0] ref_o_rdata;
wire o_ack;
wire ref_o_ack;
wire o_valid;
wire ref_o_valid;
reg i_accepted;
wire o_write;
wire ref_o_write;
wire [127:0] o_wdata;
wire [127:0] ref_o_wdata;
wire [15:0] o_be;
wire [15:0] ref_o_be;
wire [31:0] o_addr;
wire [31:0] ref_o_addr;
reg [127:0] i_rdata;
reg i_rdata_valid;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
a25_wishbone_buf dut(.i_clk(i_clk), .i_req(i_req), .i_write(i_write), .i_wdata(i_wdata), .i_be(i_be), .i_addr(i_addr), .o_rdata(o_rdata), .o_ack(o_ack), .o_valid(o_valid), .i_accepted(i_accepted), .o_write(o_write), .o_wdata(o_wdata), .o_be(o_be), .o_addr(o_addr), .i_rdata(i_rdata), .i_rdata_valid(i_rdata_valid));
oracle_a25_wishbone_buf golden(.i_clk(i_clk), .i_req(i_req), .i_write(i_write), .i_wdata(i_wdata), .i_be(i_be), .i_addr(i_addr), .o_rdata(ref_o_rdata), .o_ack(ref_o_ack), .o_valid(ref_o_valid), .i_accepted(i_accepted), .o_write(ref_o_write), .o_wdata(ref_o_wdata), .o_be(ref_o_be), .o_addr(ref_o_addr), .i_rdata(i_rdata), .i_rdata_valid(i_rdata_valid));
initial begin
i_clk = 0;
i_req = 0;
i_write = 0;
i_wdata = 0;
i_be = 0;
i_addr = 0;
i_accepted = 0;
i_rdata = 0;
i_rdata_valid = 0;
#2;

for(i=0;i<64;i=i+1) begin
i_req = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_write = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wdata = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_be = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_addr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_accepted = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_rdata = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_rdata_valid = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_rdata,ref_o_ack,ref_o_valid,ref_o_write,ref_o_wdata,ref_o_be,ref_o_addr}) === 1'bx || (^{o_rdata,o_ack,o_valid,o_write,o_wdata,o_be,o_addr}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_rdata,o_ack,o_valid,o_write,o_wdata,o_be,o_addr} !== ({ref_o_rdata,ref_o_ack,ref_o_valid,ref_o_write,ref_o_wdata,ref_o_be,ref_o_addr} ^ 1'b1)) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule