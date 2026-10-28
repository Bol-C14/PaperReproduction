module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd16;
wire [0:0] n1 = a < 16'd4;
wire [15:0] n2 = c;
wire [15:0] n3 = a;
wire [3:0] z4 = n3;
wire [3:0] n5 = z4;
wire [2:0] z6 = b;
wire [2:0] n7 = z6;
wire [2:0] n8 = n7;
wire [2:0] n9 = n8;
wire [6:0] n10 = {3'd0, n5} * {4'd0, n9};
wire [15:0] n11 = {9'd0, n10};
wire [15:0] n12 = n1 ? n2 : n11;
wire [15:0] n13 = n0 ? n12 : c;
assign out = n13;
endmodule
