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
wire [7:0] n3 = {5'd0, n2} * a;
wire [7:0] n4 = n3 + n3;
wire [7:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
