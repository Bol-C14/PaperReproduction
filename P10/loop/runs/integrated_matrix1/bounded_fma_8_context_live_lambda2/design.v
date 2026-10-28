module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [7:0] n1 = a * b;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [7:0] n1 = c;
wire [7:0] n2 = n1;
wire [7:0] n3 = a;
wire [2:0] z4 = n3;
wire [2:0] n5 = z4;
wire [7:0] n6 = b;
wire [7:0] n7 = n6;
wire [7:0] n8 = {5'd0, n5} * n7;
wire [7:0] n9 = n8;
wire [7:0] n10 = n9;
wire [7:0] n11 = n2 + n10;
wire [7:0] n12 = n0 ? n11 : c;
assign out = n12;
endmodule
