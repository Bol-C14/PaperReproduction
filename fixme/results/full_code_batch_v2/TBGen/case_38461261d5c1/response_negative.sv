`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_rst;
reg i_wr;
reg [7:0] i_data;
wire o_empty_n;
wire ref_o_empty_n;
reg i_rd;
wire [7:0] o_data;
wire [7:0] ref_o_data;
wire [15:0] o_status;
wire [15:0] ref_o_status;
wire o_err;
wire ref_o_err;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
ufifo dut(.i_clk(i_clk), .i_rst(i_rst), .i_wr(i_wr), .i_data(i_data), .o_empty_n(o_empty_n), .i_rd(i_rd), .o_data(o_data), .o_status(o_status), .o_err(o_err));
oracle_ufifo golden(.i_clk(i_clk), .i_rst(i_rst), .i_wr(i_wr), .i_data(i_data), .o_empty_n(ref_o_empty_n), .i_rd(i_rd), .o_data(ref_o_data), .o_status(ref_o_status), .o_err(ref_o_err));
initial begin
i_clk = 0;
i_rst = 1;
i_wr = 0;
i_data = 0;
i_rd = 0;
#2;
i_rst = 0;
for(i=0;i<64;i=i+1) begin
i_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_rd = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_empty_n,ref_o_data,ref_o_status,ref_o_err}) === 1'bx || (^{o_empty_n,o_data,o_status,o_err}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_empty_n,o_data,o_status,o_err} !== ({ref_o_empty_n,ref_o_data,ref_o_status,ref_o_err} ^ 1'b1)) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule