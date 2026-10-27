`timescale 1ns/1ps
module calibration_tb;
reg Reset;
reg Clk;
reg tx_pause_en;
reg xoff_cpu;
reg xon_cpu;
reg [15:0] pause_quanta;
reg pause_quanta_val;
wire pause_apply;
wire ref_pause_apply;
reg pause_quanta_sub;
wire xoff_gen;
wire ref_xoff_gen;
reg xoff_gen_complete;
wire xon_gen;
wire ref_xon_gen;
reg xon_gen_complete;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
flow_ctrl dut(.Reset(Reset), .Clk(Clk), .tx_pause_en(tx_pause_en), .xoff_cpu(xoff_cpu), .xon_cpu(xon_cpu), .pause_quanta(pause_quanta), .pause_quanta_val(pause_quanta_val), .pause_apply(pause_apply), .pause_quanta_sub(pause_quanta_sub), .xoff_gen(xoff_gen), .xoff_gen_complete(xoff_gen_complete), .xon_gen(xon_gen), .xon_gen_complete(xon_gen_complete));
oracle_flow_ctrl golden(.Reset(Reset), .Clk(Clk), .tx_pause_en(tx_pause_en), .xoff_cpu(xoff_cpu), .xon_cpu(xon_cpu), .pause_quanta(pause_quanta), .pause_quanta_val(pause_quanta_val), .pause_apply(ref_pause_apply), .pause_quanta_sub(pause_quanta_sub), .xoff_gen(ref_xoff_gen), .xoff_gen_complete(xoff_gen_complete), .xon_gen(ref_xon_gen), .xon_gen_complete(xon_gen_complete));
initial begin
Reset = 1;
Clk = 0;
tx_pause_en = 0;
xoff_cpu = 0;
xon_cpu = 0;
pause_quanta = 0;
pause_quanta_val = 0;
pause_quanta_sub = 0;
xoff_gen_complete = 0;
xon_gen_complete = 0;
#2;
Reset = 0;
for(i=0;i<64;i=i+1) begin
tx_pause_en = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xoff_cpu = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xon_cpu = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pause_quanta = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pause_quanta_val = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pause_quanta_sub = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xoff_gen_complete = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
xon_gen_complete = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_pause_apply,ref_xoff_gen,ref_xon_gen}) === 1'bx || (^{pause_apply,xoff_gen,xon_gen}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({pause_apply,xoff_gen,xon_gen} !== {ref_pause_apply,ref_xoff_gen,ref_xon_gen}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule