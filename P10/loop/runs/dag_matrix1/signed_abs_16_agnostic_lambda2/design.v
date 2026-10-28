module original(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [15:0] n1 = $signed(a) < 0 ? -a : a;
wire [15:0] n2 = n1 + b;
wire [15:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
module candidate(input [15:0] a, input [15:0] b, input [15:0] c, output [15:0] out);
wire [0:0] n0 = $signed(a) >= 0;
wire [15:0] n1 = $signed(a) < 0 ? -a : a;
wire [15:0] n2 = b + n1;
wire [15:0] n3 = n0 ? n2 : c;
assign out = n3;
endmodule
