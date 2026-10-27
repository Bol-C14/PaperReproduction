`timescale 1ns/1ps
module oracle_R_GATE ( INA, INB, INC, PPBIT );
input  INA;
input  INB;
input  INC;
output PPBIT;
   assign PPBIT = ( ~ (INA & INB)) & INC;
endmodule