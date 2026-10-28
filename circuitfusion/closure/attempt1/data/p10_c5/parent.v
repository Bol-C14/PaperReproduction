module dut(input clk,rst,en,input [3:0] a,b,output reg [3:0] q);
always @(posedge clk) if(rst) q<=4'd0; else if(en) q<=((a + (q + b)) + 4'd5);
endmodule
