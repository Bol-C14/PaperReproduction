// Newly authored educational fixture; SPDX-License-Identifier: MIT
module dut(input [11:0] a,b, input cin, output [12:0] y);
assign y = {1'b0, a} + {1'b0, b} + cin;
endmodule
