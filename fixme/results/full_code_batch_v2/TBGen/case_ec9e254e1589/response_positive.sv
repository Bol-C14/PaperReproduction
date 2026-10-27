`timescale 1ns/1ps
module calibration_tb;
reg clk;
reg rst;
reg enable;
reg [1:0] rmode;
reg [63:0] opa;
reg [63:0] opb;
reg [63:0] in_except;
reg [11:0] exponent_in;
reg [1:0] mantissa_in;
reg [2:0] fpu_op;
wire [63:0] out;
wire [63:0] ref_out;
wire ex_enable;
wire ref_ex_enable;
wire underflow;
wire ref_underflow;
wire overflow;
wire ref_overflow;
wire inexact;
wire ref_inexact;
wire exception;
wire ref_exception;
wire invalid;
wire ref_invalid;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
fpu_exceptions dut(.clk(clk), .rst(rst), .enable(enable), .rmode(rmode), .opa(opa), .opb(opb), .in_except(in_except), .exponent_in(exponent_in), .mantissa_in(mantissa_in), .fpu_op(fpu_op), .out(out), .ex_enable(ex_enable), .underflow(underflow), .overflow(overflow), .inexact(inexact), .exception(exception), .invalid(invalid));
oracle_fpu_exceptions golden(.clk(clk), .rst(rst), .enable(enable), .rmode(rmode), .opa(opa), .opb(opb), .in_except(in_except), .exponent_in(exponent_in), .mantissa_in(mantissa_in), .fpu_op(fpu_op), .out(ref_out), .ex_enable(ref_ex_enable), .underflow(ref_underflow), .overflow(ref_overflow), .inexact(ref_inexact), .exception(ref_exception), .invalid(ref_invalid));
initial begin
clk = 0;
rst = 1;
enable = 0;
rmode = 0;
opa = 0;
opb = 0;
in_except = 0;
exponent_in = 0;
mantissa_in = 0;
fpu_op = 0;
#2;
rst = 0;
for(i=0;i<64;i=i+1) begin
enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
rmode = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opa = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
opb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
in_except = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
exponent_in = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
mantissa_in = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
fpu_op = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clk=1; #2;
if ((^{ref_out,ref_ex_enable,ref_underflow,ref_overflow,ref_inexact,ref_exception,ref_invalid}) === 1'bx || (^{out,ex_enable,underflow,overflow,inexact,exception,invalid}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({out,ex_enable,underflow,overflow,inexact,exception,invalid} !== {ref_out,ref_ex_enable,ref_underflow,ref_overflow,ref_inexact,ref_exception,ref_invalid}) failures=failures+1; end
clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule