module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd8;
wire [0:0] n1 = b < 16'd4;
wire [15:0] n2 = 16'd1;
wire [15:0] n3 = b;
wire [1:0] z4 = n3;
wire [1:0] n5 = z4;
wire [15:0] n6 = a;
wire [15:0] n7 = n6;
wire [15:0] n8 = {14'd0, n5} * n7;
wire [15:0] n9 = n8;
wire [15:0] n10 = n2 + n9;
wire [15:0] n11 = n1 ? n10 : c;
wire [15:0] n12 = n0 ? n11 : c;
assign out = n12;
endmodule
