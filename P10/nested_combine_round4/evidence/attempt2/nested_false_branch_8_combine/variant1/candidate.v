module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd16;
wire [0:0] n1 = a < 8'd4;
wire [7:0] n2 = c;
wire [2:0] z3 = b;
wire [2:0] n4 = z3;
wire [0:0] n5 = !n1;
wire [0:0] n6 = n5 && n0;
wire [2:0] n7 = n4;
wire [2:0] n8 = n7;
wire [7:0] n9 = a;
wire [3:0] z10 = n9;
wire [3:0] n11 = z10;
wire [6:0] n12 = {4'd0, n8} * {3'd0, n11};
wire [7:0] n13 = {1'd0, n12};
wire [7:0] n14 = n1 ? n2 : n13;
wire [7:0] n15 = n0 ? n14 : c;
assign out = n15;
endmodule
