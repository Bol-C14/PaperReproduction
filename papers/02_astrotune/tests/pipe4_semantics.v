`timescale 1ns/1ns
module pipe4_semantics;
reg clk=0;always #5 clk=~clk;
reg rst_n=0;reg [3:0] a=0,b=0;wire [7:0] y;
verified_multi_pipe dut(.clk(clk),.rst_n(rst_n),.mul_a(a),.mul_b(b),.mul_out(y));
integer i,j,errors=0;
initial begin
 repeat(2) @(negedge clk);rst_n=1;
 for(i=0;i<16;i=i+1) for(j=0;j<16;j=j+1) begin
  @(negedge clk);a=i;b=j;
  repeat(2) @(posedge clk);
  #1;if(y !== i*j) begin errors=errors+1;$display("FAIL %d %d %d",i,j,y);end
 end
 if(errors) $fatal(1,"%d failures",errors);
 $display("PASS: all 256 unsigned 4-bit products after two pipeline edges");$finish;
end
endmodule
