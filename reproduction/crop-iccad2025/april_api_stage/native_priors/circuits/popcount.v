// Independently authored educational workload, not a paper benchmark.
module dut(input [31:0] x, output [5:0] y);
integer i; reg [5:0] n; always @* begin n=0; for(i=0;i<32;i=i+1) n=n+x[i]; end assign y=n;
endmodule
