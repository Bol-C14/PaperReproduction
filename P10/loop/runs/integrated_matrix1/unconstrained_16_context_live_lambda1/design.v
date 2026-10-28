module original(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [15:0] n0 = a * b;
wire [15:0] n1 = n0 + c;
assign out = n1;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [15:0] n0 = b * a;
wire [15:0] n1 = c + n0;
assign out = n1;
endmodule
