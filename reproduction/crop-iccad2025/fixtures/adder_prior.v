// Newly authored educational fixture; SPDX-License-Identifier: MIT
module dut(input [7:0] a,b, input cin, output [8:0] y);
assign y = {1'b0, a} + {1'b0, b} + cin;
endmodule
