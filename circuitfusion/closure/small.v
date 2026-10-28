module small(input clk,rst,en,input [3:0] a,b,output reg [3:0] q);
always @(posedge clk) if(rst) q<=0; else if(en) q<=(q+a)^b;
endmodule
