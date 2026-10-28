module original(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [7:0] n1 = $signed(a) < 0 ? -a : a;
wire [7:0] n2 = n1 + b;
wire [7:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, output [7:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [7:0] n1 = b;
wire [7:0] n2 = n1;
wire [7:0] n3 = a;
wire [7:0] n4 = n3;
wire [7:0] n5 = n2 + n4;
wire [7:0] n6 = n5;
wire [7:0] n7 = n0 ? n6 : c;
assign out = n7;
endmodule
