`timescale 1ns/1ps
module calibration_tb;
reg select;
reg [15:0] in0;
reg [15:0] in1;
wire [15:0] out;
wire [15:0] ref_out;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
address_mux dut(.select(select), .in0(in0), .in1(in1), .out(out));
oracle_address_mux golden(.select(select), .in0(in0), .in1(in1), .out(ref_out));
initial begin
select = 0;
in0 = 0;
in1 = 0;
#2;

for(i=0;i<64;i=i+1) begin
select = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2;
if ((^{ref_out}) === 1'bx || (^{out}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({out} !== ({ref_out} ^ 1'b1)) failures=failures+1; end

end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule