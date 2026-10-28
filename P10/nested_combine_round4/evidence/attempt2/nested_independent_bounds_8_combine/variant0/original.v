module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd8;
wire [0:0] n1 = b < 8'd4;
wire [7:0] n2 = a * b;
wire [7:0] n3 = n2 + 8'd1;
wire [7:0] n4 = n1 ? n3 : c;
wire [7:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
