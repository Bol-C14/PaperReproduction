// Independently authored educational workload, not a paper benchmark.
module dut(input [20:0] x, output [15:0] y);
assign y=x[20] ? (x[15:0] >> x[19:16]) : (x[15:0] << x[19:16]);
endmodule
