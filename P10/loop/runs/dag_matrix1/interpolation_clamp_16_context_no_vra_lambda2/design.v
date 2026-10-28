module original(input [15:0] a, input [15:0] b, output [15:0] out);
wire [3:0] z0 = a;
wire [3:0] n1 = z0;
wire [15:0] n2 = {12'd0, n1} * 16'd3;
wire [3:0] z3 = b;
wire [3:0] n4 = z3;
wire [15:0] n5 = {12'd0, n4} * 16'd5;
wire [15:0] n6 = n2 + n5;
wire [0:0] n7 = n6 < 16'd128;
wire [15:0] n8 = n7 ? n6 : 16'd127;
assign out = n8;
endmodule
module candidate(input [15:0] a, input [15:0] b, output [15:0] out);
wire [3:0] z0 = b;
wire [3:0] n1 = z0;
wire [15:0] n2 = 16'd5 * {12'd0, n1};
wire [3:0] z3 = a;
wire [3:0] n4 = z3;
wire [15:0] n5 = 16'd3 * {12'd0, n4};
wire [15:0] n6 = n2 + n5;
wire [0:0] n7 = n6 < 16'd128;
wire [15:0] n8 = n6;
wire [0:0] n9 = !n7;
wire [15:0] n10 = 16'd127;
wire [15:0] n11 = n7 ? n8 : n10;
assign out = n11;
endmodule
