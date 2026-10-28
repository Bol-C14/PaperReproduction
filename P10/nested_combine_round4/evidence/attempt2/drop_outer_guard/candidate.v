module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = b < 8'd4;
wire [7:0] n1 = a * b;
wire [7:0] n2 = n1 + 8'd1;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
