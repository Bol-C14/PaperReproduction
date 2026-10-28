`timescale 1ns/1ps
module calibration_tb;reg select;reg[15:0]in0,in1;wire[15:0]out;integer seed=13579;integer i;integer checks=0;integer failures=0;integer unknowns=0;
address_mux dut(select,in0,in1,out);reg[15:0]expected;
initial begin select=0;in0=0;in1=0;
for(i=0;i<64;i=i+1) begin select=i%2;in0={$random(seed)};in1={$random(seed)};expected=select?in1:in0;#2;
if((^out)===1'bx)unknowns=unknowns+1;else begin checks=checks+1;if(out!==expected)failures=failures+1;end end
$display("VALIDITY_CHECKS checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns);
if(failures==0 && unknowns==0)$display("TEST_PASS");else $display("TEST_FAIL");$finish;end endmodule
