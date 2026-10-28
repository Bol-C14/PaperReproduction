module candidate(input [7:0] a, input [0:0] b, output [0:0] out);
wire [0:0] n0 = $signed(a) < 8'sd4;
wire [0:0] n1 = $signed(a) < -8'sd3;
wire [0:0] n2 = !n1;
wire [0:0] n3 = n0 && n2;
wire [0:0] n4 = n3 ? 1'd0 : b;
assign out = n4;
endmodule
