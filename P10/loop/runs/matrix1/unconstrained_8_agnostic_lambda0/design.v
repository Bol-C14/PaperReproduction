module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [7:0] n0 = a * b;
wire [7:0] n1 = n0 + c;
assign out = n1;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [7:0] n0 = a * b;
wire [7:0] n1 = n0 + c;
assign out = n1;
endmodule
