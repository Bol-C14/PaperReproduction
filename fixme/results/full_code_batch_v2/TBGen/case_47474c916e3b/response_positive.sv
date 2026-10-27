`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_reset;
reg i_wr;
reg [31:0] i_proc_bus;
wire [31:0] o_proc_bus;
wire [31:0] ref_o_proc_bus;
reg [14:0] i_brd_ints;
wire o_interrupt;
wire ref_o_interrupt;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
icontrol dut(.i_clk(i_clk), .i_reset(i_reset), .i_wr(i_wr), .i_proc_bus(i_proc_bus), .o_proc_bus(o_proc_bus), .i_brd_ints(i_brd_ints), .o_interrupt(o_interrupt));
oracle_icontrol golden(.i_clk(i_clk), .i_reset(i_reset), .i_wr(i_wr), .i_proc_bus(i_proc_bus), .o_proc_bus(ref_o_proc_bus), .i_brd_ints(i_brd_ints), .o_interrupt(ref_o_interrupt));
initial begin
i_clk = 0;
i_reset = 1;
i_wr = 0;
i_proc_bus = 0;
i_brd_ints = 0;
#2;
i_reset = 0;
for(i=0;i<64;i=i+1) begin
i_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_proc_bus = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_brd_ints = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_proc_bus,ref_o_interrupt}) === 1'bx || (^{o_proc_bus,o_interrupt}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_proc_bus,o_interrupt} !== {ref_o_proc_bus,ref_o_interrupt}) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule