module miter(input [15:0] a, input [15:0] b, input [15:0] c, input [15:0] y,output mismatch); wire [15:0] refout,testout;
original u_original(.a(a), .b(b), .c(c), .y(y), .out(refout));candidate u_candidate(.a(a), .b(b), .c(c), .y(y), .out(testout));
assign mismatch = |(refout ^ testout); endmodule
