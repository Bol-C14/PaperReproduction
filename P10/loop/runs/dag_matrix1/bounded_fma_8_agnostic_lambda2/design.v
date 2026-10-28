module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [7:0] n1 = a * b;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [7:0] n1 = b * a;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
