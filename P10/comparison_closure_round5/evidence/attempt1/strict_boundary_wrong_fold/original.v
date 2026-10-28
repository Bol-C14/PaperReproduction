module original(input [7:0] a, input [0:0] b, output [0:0] out);
wire [0:0] n0 = $signed(a) < 8'sd1;
wire [0:0] n1 = $signed(a) < 8'sd0;
wire [0:0] n2 = n0 ? n1 : b;
assign out = n2;
endmodule
