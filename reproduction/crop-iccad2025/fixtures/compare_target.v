// Newly authored educational fixture; SPDX-License-Identifier: MIT
module dut(input [11:0] a,b, output [11:0] y);
assign y = (a < b) ? a : b;
endmodule
