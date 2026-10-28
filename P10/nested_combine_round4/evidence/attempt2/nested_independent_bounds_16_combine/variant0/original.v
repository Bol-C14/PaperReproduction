module original(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = a < 16'd8;
wire [0:0] n1 = b < 16'd4;
wire [15:0] n2 = a * b;
wire [15:0] n3 = n2 + 16'd1;
wire [15:0] n4 = n1 ? n3 : c;
wire [15:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
