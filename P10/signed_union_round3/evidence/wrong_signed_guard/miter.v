module miter(input [7:0] a, input [7:0] c, output fail); wire [7:0] x,y; original u(.a(a), .c(c),.out(x)); candidate v(.a(a), .c(c),.out(y)); assign fail = x != y; endmodule
