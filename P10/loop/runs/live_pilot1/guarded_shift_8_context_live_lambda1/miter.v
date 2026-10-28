module miter(input [7:0] a, input [7:0] b, input [7:0] c, input [7:0] y,output mismatch); wire [7:0] refout,testout;
original u_original(.a(a), .b(b), .c(c), .y(y), .out(refout));candidate u_candidate(.a(a), .b(b), .c(c), .y(y), .out(testout));
assign mismatch = |(refout ^ testout); endmodule
