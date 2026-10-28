module gold_top(input clk, output y); reg [7:0] count; always @(posedge clk) count<=count+8'd1; assign y=(count==8'd60); endmodule

module cand_top(input clk, output y); reg [7:0] count; always @(posedge clk) count<=count+8'd1; assign y=1'b0; endmodule

module tb;
reg clk; wire gy,cy; integer i;
gold_top g(clk,gy); cand_top c(clk,cy);
initial begin clk=0; g.count=0; c.count=0; #1;
 $display("OBS %0d %0d %0d",0,gy,cy);
 for(i=1;i<=260;i=i+1) begin #1; clk=1; #1;
 $display("OBS %0d %0d %0d",i,gy,cy); #1; clk=0; end
 $finish; end endmodule
