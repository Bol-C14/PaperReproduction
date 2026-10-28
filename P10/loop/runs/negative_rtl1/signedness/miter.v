module miter(input [3:0] x,output mismatch);wire [3:0] refout,testout;original u_original(.x(x), .out(refout));candidate u_candidate(.x(x), .out(testout));assign mismatch=|(refout^testout);endmodule
