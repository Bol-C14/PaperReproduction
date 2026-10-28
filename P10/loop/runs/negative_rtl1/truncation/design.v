module original(input [3:0] a, input [3:0] b, output [7:0] out);
wire [7:0] n0 = {4'd0, a} + {4'd0, b};
assign out = n0;
endmodule
module candidate(input [3:0] a, input [3:0] b, output [7:0] out);
wire [3:0] n0 = a + b;
wire [7:0] n1 = {4'd0, n0};
assign out = n1;
endmodule
