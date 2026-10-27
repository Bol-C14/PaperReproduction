// Independently authored exhaustive smoke test; not a CVDP hidden harness.
`timescale 1ns/1ps
module tb;
 reg [3:0] A, B;
 wire [4:0] X;
 integer i,j;
 adder #(.DATA_WIDTH(4)) dut(.A(A),.B(B),.X(X));
 initial begin
  for (i=0;i<16;i=i+1) begin
   for (j=0;j<16;j=j+1) begin
    A=i; B=j; #1;
    if (X !== (i+j)) $fatal(1,"adder mismatch");
   end
  end
  $display("PASS: 256 exhaustive input pairs");
  $finish;
 end
 initial begin #1000; $fatal(1,"timeout"); end
endmodule
