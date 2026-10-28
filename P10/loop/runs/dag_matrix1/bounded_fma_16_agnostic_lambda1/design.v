module original(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd8;
wire [15:0] n1 = a * b;
wire [15:0] n2 = n1 + c;
wire [15:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd8;
wire [15:0] n1 = a * b;
wire [15:0] n2 = n1 + c;
wire [15:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
