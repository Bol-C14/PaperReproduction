module original(input [7:0] a, input [7:0] b, input [7:0] c, input [7:0] y, output [7:0] out);
wire [0:0] n0 = y < 8'd2;
wire [7:0] n1 = a >> y;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
module candidate(input [7:0] a, input [7:0] b, input [7:0] c, input [7:0] y, output [7:0] out);
wire [0:0] n0 = y < 8'd2;
wire [7:0] n1 = a >> y;
wire [7:0] n2 = n1 + c;
wire [7:0] n3 = n0 ? n2 : b;
assign out = n3;
endmodule
