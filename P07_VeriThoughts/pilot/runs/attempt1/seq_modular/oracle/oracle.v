module gold_top(input clk, output reg [3:0] q); always @(posedge clk) q<=q+4'd1; endmodule

module cand_top(input clk, output reg [3:0] q); always @(posedge clk) q<=q-4'd15; endmodule

module tb;
reg clk; wire [3:0] gy,cy; integer i;
gold_top g(clk,gy); cand_top c(clk,cy);
initial begin clk=0; g.q=0; c.q=0; #1;
 $display("OBS %0d %0d %0d",0,gy,cy);
 for(i=1;i<=260;i=i+1) begin #1; clk=1; #1;
 $display("OBS %0d %0d %0d",i,gy,cy); #1; clk=0; end
 $finish; end endmodule
