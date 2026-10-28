module original(input [3:0] x, output [3:0] out);
wire [3:0] n0 = $signed(x) < 0 ? -x : x;
assign out = n0;
endmodule
module candidate(input [3:0] x, output [3:0] out);

assign out = x;
endmodule
