`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_ppd;
reg i_wb_cyc;
reg i_wb_stb;
reg i_wb_we;
reg [31:0] i_wb_data;
wire o_wb_ack;
wire ref_o_wb_ack;
wire o_wb_stall;
wire ref_o_wb_stall;
wire [31:0] o_wb_data;
wire [31:0] ref_o_wb_data;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
rtcdate dut(.i_clk(i_clk), .i_ppd(i_ppd), .i_wb_cyc(i_wb_cyc), .i_wb_stb(i_wb_stb), .i_wb_we(i_wb_we), .i_wb_data(i_wb_data), .o_wb_ack(o_wb_ack), .o_wb_stall(o_wb_stall), .o_wb_data(o_wb_data));
oracle_rtcdate golden(.i_clk(i_clk), .i_ppd(i_ppd), .i_wb_cyc(i_wb_cyc), .i_wb_stb(i_wb_stb), .i_wb_we(i_wb_we), .i_wb_data(i_wb_data), .o_wb_ack(ref_o_wb_ack), .o_wb_stall(ref_o_wb_stall), .o_wb_data(ref_o_wb_data));
initial begin
i_clk = 0;
i_ppd = 0;
i_wb_cyc = 0;
i_wb_stb = 0;
i_wb_we = 0;
i_wb_data = 0;
#2;

for(i=0;i<64;i=i+1) begin
i_ppd = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_cyc = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_stb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_we = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_wb_ack,ref_o_wb_stall,ref_o_wb_data}) === 1'bx || (^{o_wb_ack,o_wb_stall,o_wb_data}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_wb_ack,o_wb_stall,o_wb_data} !== {ref_o_wb_ack,ref_o_wb_stall,ref_o_wb_data}) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule