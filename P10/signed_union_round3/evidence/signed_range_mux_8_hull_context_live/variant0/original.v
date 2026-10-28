module original(input [7:0] a, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) < 8'sd8;
wire [0:0] n1 = $signed(a) < -8'sd7;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [0:0] n4 = $signed(a) < 8'sd0;
wire [7:0] n5 = -a;
wire [7:0] n6 = n4 ? n5 : a;
wire [7:0] n7 = n3 ? n6 : c;
assign out = n7;
endmodule
