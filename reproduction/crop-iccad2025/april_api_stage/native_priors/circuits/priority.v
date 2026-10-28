// Independently authored educational workload, not a paper benchmark.
module dut(input [31:0] x, output [5:0] y);
integer i; reg [4:0] index; always @* begin index=0; for(i=0;i<32;i=i+1) if(x[i]) index=i; end assign y={|x,index};
endmodule
