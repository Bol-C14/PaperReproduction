module miter(input [15:0] a, input [15:0] c, output fail); wire [15:0] x,y; original u(.a(a), .c(c),.out(x)); candidate v(.a(a), .c(c),.out(y)); assign fail = x != y; endmodule
