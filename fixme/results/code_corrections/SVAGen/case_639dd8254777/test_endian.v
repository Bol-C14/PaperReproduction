`timescale 1ns/1ps

module test_endian;
	reg [31:0] i;
	initial begin
		i = 32'h12345678; 
		#100;
        $display("%h %h %h %h", i[31:24], i[23:16], i[15:8], i[7:0]);
        $finish;
	end
endmodule
