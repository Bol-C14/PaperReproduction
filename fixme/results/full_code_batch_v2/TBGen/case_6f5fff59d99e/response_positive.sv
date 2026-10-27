`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg reset_n;
reg [4:0] rs1_addr_i;
reg [4:0] rs2_addr_i;
reg [4:0] rd_addr_i;
reg wr_en_i;
reg [31:0] wr_data_i;
wire [31:0] rs1_data_o;
wire [31:0] ref_rs1_data_o;
wire [31:0] rs2_data_o;
wire [31:0] ref_rs2_data_o;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
rv_regfile dut(.clk(clk), .reset_n(reset_n), .rs1_addr_i(rs1_addr_i), .rs2_addr_i(rs2_addr_i), .rd_addr_i(rd_addr_i), .wr_en_i(wr_en_i), .wr_data_i(wr_data_i), .rs1_data_o(rs1_data_o), .rs2_data_o(rs2_data_o));
oracle_rv_regfile golden(.clk(clk), .reset_n(reset_n), .rs1_addr_i(rs1_addr_i), .rs2_addr_i(rs2_addr_i), .rd_addr_i(rd_addr_i), .wr_en_i(wr_en_i), .wr_data_i(wr_data_i), .rs1_data_o(ref_rs1_data_o), .rs2_data_o(ref_rs2_data_o));
initial begin
clk = 0;
reset_n = 0;
rs1_addr_i = 0;
rs2_addr_i = 0;
rd_addr_i = 0;
wr_en_i = 0;
wr_data_i = 0;
#2;
reset_n = 1;
for(i=0;i<64;i=i+1) begin
rs1_addr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rs2_addr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rd_addr_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wr_en_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
wr_data_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_rs1_data_o,ref_rs2_data_o}) === 1'bx || (^{rs1_data_o,rs2_data_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({rs1_data_o,rs2_data_o} !== {ref_rs1_data_o,ref_rs2_data_o}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule