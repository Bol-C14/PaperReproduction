module original(input [7:0] a, input [7:0] b, input [3:0] y, output [7:0] out);
wire [0:0] n0 = y < 4'd3;
wire [7:0] n1 = a >> y;
wire [7:0] n2 = n0 ? n1 : b;
assign out = n2;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [3:0] y, output [7:0] out);
wire [0:0] n0 = y < 4'd3;
wire [0:0] z1 = y;
wire [0:0] n2 = z1;
wire [7:0] n3 = a >> n2;
wire [7:0] n4 = n0 ? n3 : b;
assign out = n4;
endmodule
