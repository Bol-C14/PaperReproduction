`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_stb;
reg [6:0] i_bits;
wire o_stb;
wire ref_o_stb;
wire [7:0] o_char;
wire [7:0] ref_o_char;
wire o_busy;
wire ref_o_busy;
reg i_busy;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
wbusixchar dut(.i_clk(i_clk), .i_stb(i_stb), .i_bits(i_bits), .o_stb(o_stb), .o_char(o_char), .o_busy(o_busy), .i_busy(i_busy));
oracle_wbusixchar golden(.i_clk(i_clk), .i_stb(i_stb), .i_bits(i_bits), .o_stb(ref_o_stb), .o_char(ref_o_char), .o_busy(ref_o_busy), .i_busy(i_busy));
initial begin
i_clk = 0;
i_stb = 0;
i_bits = 0;
i_busy = 0;
#2;

for(i=0;i<64;i=i+1) begin
i_stb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_bits = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_busy = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_stb,ref_o_char,ref_o_busy}) === 1'bx || (^{o_stb,o_char,o_busy}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_stb,o_char,o_busy} !== {ref_o_stb,ref_o_char,ref_o_busy}) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule