module candidate(input [7:0] a, input [7:0] b, output [7:0] out);
wire [2:0] z0 = a;
wire [2:0] n1 = z0;
wire [1:0] z2 = b;
wire [1:0] n3 = z2;
wire [4:0] n4 = {2'd0, n1} * {3'd0, n3};
wire [7:0] n5 = {3'd0, n4};
wire [7:0] n6 = n5 + 8'd1;
assign out = n6;
endmodule
