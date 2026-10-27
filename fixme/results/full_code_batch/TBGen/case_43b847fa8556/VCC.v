`timescale 1ns/1ps

module VCC(Y);
 output Y;
 supply1    Y;
       specify
		specparam MacroType = "comb";
   endspecify
endmodule
