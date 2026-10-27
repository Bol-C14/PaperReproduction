`timescale 1ns/1ps
module calibration_tb;
wire [31:0] mix_out_enc;
wire [31:0] ref_mix_out_enc;
wire [31:0] mix_out_dec;
wire [31:0] ref_mix_out_dec;
reg [31:0] mix_in;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
mix_columns dut(.mix_out_enc(mix_out_enc), .mix_out_dec(mix_out_dec), .mix_in(mix_in));
oracle_mix_columns golden(.mix_out_enc(ref_mix_out_enc), .mix_out_dec(ref_mix_out_dec), .mix_in(mix_in));
initial begin
mix_in = 0;
#2;

for(i=0;i<64;i=i+1) begin
mix_in = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_mix_out_enc,ref_mix_out_dec}) === 1'bx || (^{mix_out_enc,mix_out_dec}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({mix_out_enc,mix_out_dec} !== {ref_mix_out_enc,ref_mix_out_dec}) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule