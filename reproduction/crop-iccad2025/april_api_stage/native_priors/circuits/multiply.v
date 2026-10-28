// Independently authored educational workload, not a paper benchmark.
module dut(input [15:0] x, output [15:0] y);
assign y=x[7:0]*x[15:8];
endmodule
