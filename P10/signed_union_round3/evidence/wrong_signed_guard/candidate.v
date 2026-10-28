module candidate(input [7:0] a, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd4;
wire [7:0] n1 = $signed(a) < 0 ? -a : a;
wire [7:0] n2 = n0 ? n1 : c;
assign out = n2;
endmodule
