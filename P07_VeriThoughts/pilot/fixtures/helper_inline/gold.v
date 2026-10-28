module helper(input a,b, output y); assign y=a^b; endmodule
module top(input a,b, output y); helper h(a,b,y); endmodule
