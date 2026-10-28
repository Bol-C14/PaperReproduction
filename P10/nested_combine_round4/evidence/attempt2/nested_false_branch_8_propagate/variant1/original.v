module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = a < 8'd16;
wire [0:0] n1 = a < 8'd4;
wire [2:0] z2 = b;
wire [2:0] n3 = z2;
wire [7:0] n4 = a * {5'd0, n3};
wire [7:0] n5 = n1 ? c : n4;
wire [7:0] n6 = n0 ? n5 : c;
assign out = n6;
endmodule
