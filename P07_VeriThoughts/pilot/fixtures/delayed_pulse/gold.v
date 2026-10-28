module top(input clk, output y); reg [7:0] count; always @(posedge clk) count<=count+8'd1; assign y=(count==8'd60); endmodule
