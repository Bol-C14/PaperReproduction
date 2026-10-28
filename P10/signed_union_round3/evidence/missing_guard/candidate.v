module candidate(input [7:0] a, output [7:0] out);
wire [7:0] n0 = $signed(a) < 0 ? -a : a;
assign out = n0;
endmodule
