`timescale 1ns/1ps
 
module sparc_exu_ecc_dec_ref (
   e_ref, 
   q
   ) ; 
   input [6:0] q;
   output [63:0] e_ref;
   assign e_ref[0] = ~q[6] & ~q[5] & ~q[4] & ~q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[1] = ~q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[2] = ~q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[3] = ~q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & q[1] & q[0];
   assign e_ref[4] = ~q[6] & ~q[5] & ~q[4] & q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[5] = ~q[6] & ~q[5] & ~q[4] & q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[6] = ~q[6] & ~q[5] & ~q[4] & q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[7] = ~q[6] & ~q[5] & ~q[4] & q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[8] = ~q[6] & ~q[5] & ~q[4] & q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[9] = ~q[6] & ~q[5] & ~q[4] & q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[10] = ~q[6] & ~q[5] & ~q[4] & q[3] & q[2] & q[1] & q[0];
   assign e_ref[11] = ~q[6] & ~q[5] & q[4] & ~q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[12] = ~q[6] & ~q[5] & q[4] & ~q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[13] = ~q[6] & ~q[5] & q[4] & ~q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[14] = ~q[6] & ~q[5] & q[4] & ~q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[15] = ~q[6] & ~q[5] & q[4] & ~q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[16] = ~q[6] & ~q[5] & q[4] & ~q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[17] = ~q[6] & ~q[5] & q[4] & ~q[3] & q[2] & q[1] & q[0];
   assign e_ref[18] = ~q[6] & ~q[5] & q[4] & q[3] & ~q[2] & ~q[1] & ~q[0];
   assign e_ref[19] = ~q[6] & ~q[5] & q[4] & q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[20] = ~q[6] & ~q[5] & q[4] & q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[21] = ~q[6] & ~q[5] & q[4] & q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[22] = ~q[6] & ~q[5] & q[4] & q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[23] = ~q[6] & ~q[5] & q[4] & q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[24] = ~q[6] & ~q[5] & q[4] & q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[25] = ~q[6] & ~q[5] & q[4] & q[3] & q[2] & q[1] & q[0];
   assign e_ref[26] = ~q[6] & q[5] & ~q[4] & ~q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[27] = ~q[6] & q[5] & ~q[4] & ~q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[28] = ~q[6] & q[5] & ~q[4] & ~q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[29] = ~q[6] & q[5] & ~q[4] & ~q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[30] = ~q[6] & q[5] & ~q[4] & ~q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[31] = ~q[6] & q[5] & ~q[4] & ~q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[32] = ~q[6] & q[5] & ~q[4] & ~q[3] & q[2] & q[1] & q[0];
   assign e_ref[33] = ~q[6] & q[5] & ~q[4] & q[3] & ~q[2] & ~q[1] & ~q[0];
   assign e_ref[34] = ~q[6] & q[5] & ~q[4] & q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[35] = ~q[6] & q[5] & ~q[4] & q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[36] = ~q[6] & q[5] & ~q[4] & q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[37] = ~q[6] & q[5] & ~q[4] & q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[38] = ~q[6] & q[5] & ~q[4] & q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[39] = ~q[6] & q[5] & ~q[4] & q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[40] = ~q[6] & q[5] & ~q[4] & q[3] & q[2] & q[1] & q[0];
   assign e_ref[41] = ~q[6] & q[5] & q[4] & ~q[3] & ~q[2] & ~q[1] & ~q[0];
   assign e_ref[42] = ~q[6] & q[5] & q[4] & ~q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[43] = ~q[6] & q[5] & q[4] & ~q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[44] = ~q[6] & q[5] & q[4] & ~q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[45] = ~q[6] & q[5] & q[4] & ~q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[46] = ~q[6] & q[5] & q[4] & ~q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[47] = ~q[6] & q[5] & q[4] & ~q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[48] = ~q[6] & q[5] & q[4] & ~q[3] & q[2] & q[1] & q[0];
   assign e_ref[49] = ~q[6] & q[5] & q[4] & q[3] & ~q[2] & ~q[1] & ~q[0];
   assign e_ref[50] = ~q[6] & q[5] & q[4] & q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[51] = ~q[6] & q[5] & q[4] & q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[52] = ~q[6] & q[5] & q[4] & q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[53] = ~q[6] & q[5] & q[4] & q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[54] = ~q[6] & q[5] & q[4] & q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[55] = ~q[6] & q[5] & q[4] & q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[56] = ~q[6] & q[5] & q[4] & q[3] & q[2] & q[1] & q[0];
   assign e_ref[57] = q[6] & ~q[5] & ~q[4] & ~q[3] & ~q[2] & ~q[1] & q[0];
   assign e_ref[58] = q[6] & ~q[5] & ~q[4] & ~q[3] & ~q[2] & q[1] & ~q[0];
   assign e_ref[59] = q[6] & ~q[5] & ~q[4] & ~q[3] & ~q[2] & q[1] & q[0];
   assign e_ref[60] = q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & ~q[1] & ~q[0];
   assign e_ref[61] = q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & ~q[1] & q[0];
   assign e_ref[62] = q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & q[1] & ~q[0];
   assign e_ref[63] = q[6] & ~q[5] & ~q[4] & ~q[3] & q[2] & q[1] & q[0];
endmodule

