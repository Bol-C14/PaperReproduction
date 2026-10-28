module original(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y, output [15:0] out);
wire [0:0] n0 = y < 16'd2;
wire [15:0] n1 = a >> y;
wire [15:0] n2 = n1 + c;
wire [15:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y, output [15:0] out);
wire [0:0] n0 = y < 16'd2;
wire [15:0] n1 = a >> y;
wire [15:0] n2 = c + n1;
wire [15:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
