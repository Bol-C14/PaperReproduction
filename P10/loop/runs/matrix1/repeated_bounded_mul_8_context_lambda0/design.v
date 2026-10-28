module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd4;
wire [2:0] z1 = b;
wire [2:0] n2 = z1;
wire [7:0] n3 = a * {5'd0, n2};
wire [7:0] n4 = n3 + n3;
wire [7:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd4;
wire [2:0] z1 = b;
wire [2:0] n2 = z1;
wire [2:0] n3 = n2;
wire [2:0] n4 = n3;
wire [7:0] n5 = a;
wire [1:0] z6 = n5;
wire [1:0] n7 = z6;
wire [4:0] n8 = {2'd0, n4} * {3'd0, n7};
wire [7:0] n9 = {3'd0, n8};
wire [4:0] z10 = n9;
wire [4:0] n11 = z10;
wire [5:0] n12 = {1'd0, n11} + {1'd0, n11};
wire [7:0] n13 = {2'd0, n12};
wire [0:0] n14 = !n0;
wire [7:0] n15 = c;
wire [7:0] n16 = n0 ? n13 : n15;
assign out = n16;
endmodule
