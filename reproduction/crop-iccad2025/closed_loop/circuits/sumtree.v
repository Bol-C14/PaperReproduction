// Independently authored educational workload, not a paper benchmark.
module dut(input [31:0] x, output [9:0] y);
wire [9:0] a={2'b0,x[7:0]}, b={2'b0,x[15:8]}, c={2'b0,x[23:16]}, d={2'b0,x[31:24]}; assign y=a+b+c+d;
endmodule
