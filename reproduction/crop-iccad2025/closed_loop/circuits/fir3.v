// Independently authored educational workload, not a paper benchmark.
module dut(input [35:0] x, output [13:0] y);
wire [11:0] p0=x[5:0]*x[23:18],p1=x[11:6]*x[29:24],p2=x[17:12]*x[35:30]; assign y={2'b0,p0}+{2'b0,p1}+{2'b0,p2};
endmodule
