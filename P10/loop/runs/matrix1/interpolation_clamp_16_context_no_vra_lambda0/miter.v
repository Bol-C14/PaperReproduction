module miter(input [15:0] a, input [15:0] b,output mismatch); wire [15:0] refout,testout;
original u_original(.a(a), .b(b), .out(refout));candidate u_candidate(.a(a), .b(b), .out(testout));
assign mismatch = |(refout ^ testout); endmodule
