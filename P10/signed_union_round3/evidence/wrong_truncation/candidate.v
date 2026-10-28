module candidate(input [7:0] a, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) < 8'sd4;
wire [7:0] n1 = $signed(a) < 0 ? -a : a;
wire [1:0] z2 = n1;
wire [1:0] n3 = z2;
wire [7:0] n4 = {6'd0, n3};
wire [7:0] n5 = n0 ? n4 : c;
assign out = n5;
endmodule
