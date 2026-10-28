module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd16;
wire [0:0] n1 = a < 16'd4;
wire [2:0] z2 = b;
wire [2:0] n3 = z2;
wire [15:0] n4 = a * {13'd0, n3};
wire [15:0] n5 = n1 ? c : n4;
wire [15:0] n6 = n0 ? n5 : c;
assign out = n6;
endmodule
