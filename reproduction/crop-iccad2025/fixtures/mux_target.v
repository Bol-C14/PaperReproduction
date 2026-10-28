// Newly authored educational fixture; SPDX-License-Identifier: MIT
module dut(input [11:0] a,b,c,d, input [1:0] sel, output [11:0] y);
assign y = sel[1] ? (sel[0] ? d : c) : (sel[0] ? b : a);
endmodule
