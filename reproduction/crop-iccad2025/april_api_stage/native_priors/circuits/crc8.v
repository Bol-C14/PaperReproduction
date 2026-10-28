// Independently authored educational workload, not a paper benchmark.
module dut(input [23:0] x, output [7:0] y);
integer i; reg [7:0] c; always @* begin c=x[7:0]; for(i=23;i>=8;i=i-1) begin if(c[7]^x[i]) c=(c<<1)^8'h07; else c=c<<1; end end assign y=c;
endmodule
