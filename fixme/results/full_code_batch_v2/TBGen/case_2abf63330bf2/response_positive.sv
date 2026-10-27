`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg reset;
reg [2:0] rot;
wire rot_btn;
wire ref_rot_btn;
wire rot_event;
wire ref_rot_event;
wire rot_left;
wire ref_rot_left;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
rotary dut(.clk(clk), .reset(reset), .rot(rot), .rot_btn(rot_btn), .rot_event(rot_event), .rot_left(rot_left));
oracle_rotary golden(.clk(clk), .reset(reset), .rot(rot), .rot_btn(ref_rot_btn), .rot_event(ref_rot_event), .rot_left(ref_rot_left));
initial begin
clk = 0;
reset = 1;
rot = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
rot = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_rot_btn,ref_rot_event,ref_rot_left}) === 1'bx || (^{rot_btn,rot_event,rot_left}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({rot_btn,rot_event,rot_left} !== {ref_rot_btn,ref_rot_event,ref_rot_left}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule