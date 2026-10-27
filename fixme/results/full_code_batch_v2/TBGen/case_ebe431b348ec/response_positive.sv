`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg [7:0] addr0_i;
reg [7:0] data0_i;
reg stb0_i;
reg we0_i;
reg req0;
wire gnt0;
wire ref_gnt0;
reg [7:0] addr1_i;
reg [7:0] data1_i;
reg stb1_i;
reg we1_i;
reg req1;
wire gnt1;
wire ref_gnt1;
reg [7:0] addr2_i;
reg [7:0] data2_i;
reg stb2_i;
reg we2_i;
reg req2;
wire gnt2;
wire ref_gnt2;
wire [7:0] addr_o;
wire [7:0] ref_addr_o;
wire [7:0] data_o;
wire [7:0] ref_data_o;
wire stb_o;
wire ref_stb_o;
wire we_o;
wire ref_we_o;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
wishboneArb dut(.clk(clk), .rst(rst), .addr0_i(addr0_i), .data0_i(data0_i), .stb0_i(stb0_i), .we0_i(we0_i), .req0(req0), .gnt0(gnt0), .addr1_i(addr1_i), .data1_i(data1_i), .stb1_i(stb1_i), .we1_i(we1_i), .req1(req1), .gnt1(gnt1), .addr2_i(addr2_i), .data2_i(data2_i), .stb2_i(stb2_i), .we2_i(we2_i), .req2(req2), .gnt2(gnt2), .addr_o(addr_o), .data_o(data_o), .stb_o(stb_o), .we_o(we_o));
oracle_wishboneArb golden(.clk(clk), .rst(rst), .addr0_i(addr0_i), .data0_i(data0_i), .stb0_i(stb0_i), .we0_i(we0_i), .req0(req0), .gnt0(ref_gnt0), .addr1_i(addr1_i), .data1_i(data1_i), .stb1_i(stb1_i), .we1_i(we1_i), .req1(req1), .gnt1(ref_gnt1), .addr2_i(addr2_i), .data2_i(data2_i), .stb2_i(stb2_i), .we2_i(we2_i), .req2(req2), .gnt2(ref_gnt2), .addr_o(ref_addr_o), .data_o(ref_data_o), .stb_o(ref_stb_o), .we_o(ref_we_o));
initial begin
clk = 0;
rst = 1;
addr0_i = 0;
data0_i = 0;
stb0_i = 0;
we0_i = 0;
req0 = 0;
addr1_i = 0;
data1_i = 0;
stb1_i = 0;
we1_i = 0;
req1 = 0;
addr2_i = 0;
data2_i = 0;
stb2_i = 0;
we2_i = 0;
req2 = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
addr0_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
data0_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
stb0_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
we0_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
req0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
addr1_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
data1_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
stb1_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
we1_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
req1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
addr2_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
data2_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
stb2_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
we2_i = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
req2 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_gnt0,ref_gnt1,ref_gnt2,ref_addr_o,ref_data_o,ref_stb_o,ref_we_o}) === 1'bx || (^{gnt0,gnt1,gnt2,addr_o,data_o,stb_o,we_o}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({gnt0,gnt1,gnt2,addr_o,data_o,stb_o,we_o} !== {ref_gnt0,ref_gnt1,ref_gnt2,ref_addr_o,ref_data_o,ref_stb_o,ref_we_o}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule