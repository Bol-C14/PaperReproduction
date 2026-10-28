module gold_top(input a,b, output y); assign y=~(a&b); endmodule

module cand_top(input a,b, output y); assign y=(~a)|(~b); endmodule

module tb;
reg a,b; wire gy,cy; integer i;
gold_top g(a,b,gy); cand_top c(a,b,cy);
initial begin
 for(i=0;i<4;i=i+1) begin {a,b}=i; #1; $display("OBS %0d %0d %0d",i,gy,cy); end
 $finish; end endmodule
