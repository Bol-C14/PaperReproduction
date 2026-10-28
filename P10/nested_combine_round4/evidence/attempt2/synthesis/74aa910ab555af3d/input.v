module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd16;
wire [0:0] n1 = a < 8'd4;
wire [0:0] n2 = !n1;
wire [7:0] n3 = a;
wire [2:0] z4 = b;
wire [2:0] n5 = z4;
wire [2:0] n6 = n5;
wire [7:0] n7 = n3 * {5'd0, n6};
wire [7:0] n8 = n1 ? c : n7;
wire [7:0] n9 = n0 ? n8 : c;
assign out = n9;
endmodule
