`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg reset_n;
reg [31:0] init_pattern_data;
reg load_init_pattern;
reg next_pattern;
reg [7:0] update_rule;
reg load_update_rule;
wire [31:0] prng_data;
wire [31:0] ref_prng_data;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
ca_prng dut(.clk(clk), .reset_n(reset_n), .init_pattern_data(init_pattern_data), .load_init_pattern(load_init_pattern), .next_pattern(next_pattern), .update_rule(update_rule), .load_update_rule(load_update_rule), .prng_data(prng_data));
oracle_ca_prng golden(.clk(clk), .reset_n(reset_n), .init_pattern_data(init_pattern_data), .load_init_pattern(load_init_pattern), .next_pattern(next_pattern), .update_rule(update_rule), .load_update_rule(load_update_rule), .prng_data(ref_prng_data));
initial begin
clk = 0;
reset_n = 0;
init_pattern_data = 0;
load_init_pattern = 0;
next_pattern = 0;
update_rule = 0;
load_update_rule = 0;
#2;
reset_n = 1;
for(i=0;i<64;i=i+1) begin
init_pattern_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
load_init_pattern = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
next_pattern = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
update_rule = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
load_update_rule = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_prng_data}) === 1'bx || (^{prng_data}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({prng_data} !== {ref_prng_data}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule