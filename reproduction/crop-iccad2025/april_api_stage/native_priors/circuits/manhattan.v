// Independently authored educational workload, not a paper benchmark.
module dut(input [31:0] x, output [9:0] y);
wire [7:0] a=x[7:0],b=x[15:8],c=x[23:16],d=x[31:24]; wire [7:0] dx=a>b?a-b:b-a,dy=c>d?c-d:d-c; assign y={2'b0,dx}+{2'b0,dy};
endmodule
