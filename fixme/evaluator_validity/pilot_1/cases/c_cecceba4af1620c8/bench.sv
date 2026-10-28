`timescale 1ns/1ps
module calibration_tb;reg d0,d1,d2,d3,s1,s0;wire y;reg expected;integer i;integer checks=0;integer failures=0;integer unknowns=0;
mux dut(d0,d1,d2,d3,s1,s0,y);
initial begin for(i=0;i<64;i=i+1)begin {s1,s0,d0,d1,d2,d3}=i;expected=s1?(s0?d3:d2):(s0?d1:d0);#2;
if(y===1'bx)unknowns=unknowns+1;else begin checks=checks+1;if(y!==expected)begin failures=failures+1;$display("COUNTEREXAMPLE input=%06b observed=%b expected=%b",i[5:0],y,expected);end end end
$display("VALIDITY_CHECKS checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns);$finish;end endmodule
