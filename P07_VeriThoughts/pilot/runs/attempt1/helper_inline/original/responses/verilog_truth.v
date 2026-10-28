module helper1(input a,b, output y); assign y=a^b; endmodule
module top1(input a,b, output y); helper1 h(a,b,y); endmodule
