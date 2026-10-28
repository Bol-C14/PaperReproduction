// Independently authored educational workload, not a paper benchmark.
module dut(input [17:0] x, output [7:0] y);
wire [7:0] a=x[7:0], b=x[15:8]; assign y=x[17:16]==0 ? a+b : x[17:16]==1 ? a-b : x[17:16]==2 ? a&b : a^b;
endmodule
