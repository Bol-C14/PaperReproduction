// Newly authored educational fixture; SPDX-License-Identifier: MIT
module dut(input [7:0] a,b, output [7:0] y);
assign y = (a < b) ? a : b;
endmodule
