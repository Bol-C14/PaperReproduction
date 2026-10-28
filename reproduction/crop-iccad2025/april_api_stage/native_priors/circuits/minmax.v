// Independently authored educational workload, not a paper benchmark.
module dut(input [31:0] x, output [15:0] y);
wire [7:0] a=x[7:0],b=x[15:8],c=x[23:16],d=x[31:24]; wire [7:0] lo=a<b?a:b,hi=c>d?c:d; assign y={hi,lo};
endmodule
