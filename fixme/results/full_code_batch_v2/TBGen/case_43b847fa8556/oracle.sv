`timescale 1ns/1ps
module oracle_VCC(Y);
 output Y;
 supply1    Y;
       specify
		specparam MacroType = "comb";
   endspecify
endmodule