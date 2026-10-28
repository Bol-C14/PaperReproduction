module candidate(input [7:0] a, input [0:0] b, output [0:0] out);
wire [0:0] n0 = $signed(a) < 8'sd1;
wire [0:0] n1 = n0 ? 1'd1 : b;
assign out = n1;
endmodule
