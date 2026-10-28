module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [0:0] n1 = b < 8'd4;
wire [7:0] n2 = 8'd1;
wire [7:0] n3 = b;
wire [1:0] z4 = n3;
wire [1:0] n5 = z4;
wire [7:0] n6 = a;
wire [7:0] n7 = n6;
wire [7:0] n8 = {6'd0, n5} * n7;
wire [7:0] n9 = n8;
wire [7:0] n10 = n2 + n9;
wire [7:0] n11 = n1 ? n10 : c;
wire [7:0] n12 = n11;
wire [7:0] n13 = n0 ? n12 : c;
assign out = n13;
endmodule
