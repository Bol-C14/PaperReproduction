module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) < 8'sd4;
wire [0:0] n1 = $signed(a) < -8'sd3;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [2:0] z4 = b;
wire [2:0] n5 = z4;
wire [7:0] n6 = 8'd2 + a;
wire [7:0] n7 = $signed(n6) < 0 ? -n6 : n6;
wire [7:0] n8 = {5'd0, n5} * n7;
wire [7:0] n9 = n3 ? n8 : c;
assign out = n9;
endmodule
