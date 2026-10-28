module miter(input [7:0] a, input [0:0] b, output fail); wire [0:0] x,y; original u(.a(a), .b(b),.out(x)); candidate v(.a(a), .b(b),.out(y)); assign fail = x != y; endmodule
