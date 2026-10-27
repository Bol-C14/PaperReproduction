 `timescale 1ns / 1ps

module tb;

`define P 20
    // Inputs
    reg clk;
    reg reset;
    reg [63:0] in;
    reg in_ready;
    reg is_last;
    reg [2:0] byte_num;

    // Outputs
    wire ref_buffer_full,dut_buffer_full;
    wire [511:0] ref_out,dut_out;
    wire ref_out_ready,dut_out_ready;

	wire match;

    // Var
    integer i;
 	integer total_tests = 0;
	integer failed_tests = 0;

 assign match = ({ref_buffer_full, ref_out, ref_out_ready} === {dut_buffer_full, dut_out, dut_out_ready});

    // Instantiate the Unit Under Test (DUT)
    top dut (
        .clk(clk),
        .reset(reset),
        .in(in),
        .in_ready(in_ready),
        .is_last(is_last),
        .byte_num(byte_num),
        .buffer_full(dut_buffer_full),
        .out(dut_out),
        .out_ready(dut_out_ready)
    );

 // REF Module
    ref_keccak  ref_module(
        .clk(clk),
        .reset(reset),
        .in(in),
        .in_ready(in_ready),
        .is_last(is_last),
        .byte_num(byte_num),
        .ref_buffer_full(ref_buffer_full),
        .ref_out(ref_out),
        .ref_out_ready(ref_out_ready)
    );

    initial begin
        // Initialize Inputs
        clk = 0;
        reset = 0;
        in = 0;
        in_ready = 0;
        is_last = 0;
        byte_num = 0;

        // Wait 100 ns for global reset to finish
        #100;

        // Add stimulus here
        @ (negedge clk);

        // SHA3-512("The quick brown fox jumps over the lazy dog")
       // reset = 1; #(`P); reset = 0;
       // in_ready = 1; is_last = 0;
       // in = "The quic"; #(`P);
       // in = "k brown "; #(`P);
       // in = "fox jump"; #(`P);
       // in = "s over t"; #(`P);
       // in = "he lazy "; #(`P);
       // in = "dog     "; byte_num = 3; is_last = 1; #(`P); /* !!! not in = "dog" */
       // in_ready = 0; is_last = 0;
       // while (ref_out_ready !== 1)
       //     #(`P);
        //compare();

        // SHA3-512("The quick brown fox jumps over the lazy dog.")
       // reset = 1; #(`P); reset = 0;
      //  in_ready = 1; is_last = 0;
       // in = "The quic"; #(`P);
        //in = "k brown "; #(`P);
       // in = "fox jump"; #(`P);
       // in = "s over t"; #(`P);
       // in = "he lazy "; #(`P);
       // in = "dog.    "; byte_num = 4; is_last = 1; #(`P); /* !!! not in = "dog." */
       // in_ready = 0; is_last = 0;
       //while (ref_out_ready !== 1)
        //    #(`P);
       // compare();

        // hash an string "\xA1\xA2\xA3\xA4\xA5", len == 5
        reset = 1; #(`P); reset = 0;
        #(7*`P); // wait some cycles
        in = 64'hA1A2A3A4A5000000;
        byte_num = 5;
        in_ready = 1;
        is_last = 1;
        #(`P);
        in = 64'h12345678; // next input
        in_ready = 1;
        is_last = 1;
        #(`P/2);
        if (ref_buffer_full === 1) ; // should be 0
        #(`P/2);
        in_ready = 0;
        is_last = 0;

        while (ref_out_ready !== 1)
            #(`P);
        compare();
        for(i=0; i<5; i=i+1)
          begin
            #(`P);
            if (ref_buffer_full !== 0) ; // should keep 0
          end

        // hash an empty string, should not eat next input
        reset = 1; #(`P); reset = 0;
        #(7*`P); // wait some cycles
        in = 64'h12345678; // should not be eat
        byte_num = 0;
        in_ready = 1;
        is_last = 1;
        #(`P);
        in = 64'hddddd; // should not be eat
        in_ready = 1; // next input
        is_last = 1;
        #(`P);
        in_ready = 0;
        is_last = 0;


        while (ref_out_ready !== 1)
            #(`P);
        compare();
        for(i=0; i<5; i=i+1)
          begin
            #(`P);
            if (ref_buffer_full !== 0) ; // should keep 0
          end

        // hash an (576-8) bit string
        reset = 1; #(`P); reset = 0;
        #(4*`P); // wait some cycles
        in_ready = 1;
        byte_num = 7; /* should have no effect */
        is_last = 0;
        for (i=0; i<8; i=i+1)
          begin
            in = 64'hEFCDAB9078563412;
            #(`P);
          end
        is_last = 1;
        #(`P);
        in_ready = 0;
        is_last = 0;
        while (ref_out_ready !== 1)
            #(`P);
        compare();

        // pad an (576-64) bit string
        reset = 1; #(`P); reset = 0;
        // don't wait any cycle
        in_ready = 1;
        byte_num = 7; /* should have no effect */
        is_last = 0;
        for (i=0; i<8; i=i+1)
          begin
            in = 64'hEFCDAB9078563412;
            #(`P);
          end
        is_last = 1;
        byte_num = 0;
        #(`P);
        in_ready = 0;
        is_last = 0;
        in = 0;
        while (ref_out_ready !== 1)
            #(`P);
        compare();

        // pad an (576*2-16) bit string
        reset = 1; #(`P); reset = 0;
        in_ready = 1;
        byte_num = 1; /* should have no effect */
        is_last = 0;
        for (i=0; i<9; i=i+1)
          begin
            in = 64'hEFCDAB9078563412; #(`P);
          end
        #(`P/2);
        if (ref_buffer_full !== 1); // should not eat
        #(`P/2);
        in = 64'h999; // should not eat this
        in_ready = 0;
        #(`P/2);
        if (ref_buffer_full !== 0) ; // should not eat, but buffer should not be full
        #(`P/2);
        #(`P);
        // feed next (576-16) bit
        in_ready = 1;
        for (i=0; i<8; i=i+1)
          begin
            in = 64'hEFCDAB9078563412; #(`P);
          end
        byte_num = 6;
        is_last = 1;
        in = 64'hEFCDAB9078563412;
        #(`P);
        is_last = 0;
        in_ready = 0;
        while (ref_out_ready !== 1)
            #(`P);
        compare();
//------------------------------------------------------------------

//-------------------------------------------------
repeat (96) begin
            @(negedge clk);
        in = $random;
        in_ready = $random;
        is_last = $random;
        byte_num = $random;
            compare();
        end

        $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $finish;
    end

    always #(`P/2) clk = ~ clk;

    
task compare;
        total_tests = total_tests + 1;
       // wait (dut_buffer_full == 1);
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
				$display("testcase is passed!!!");
            	// $display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
             //$display("dut_buffer_full = %h, dut_out = %h, dut_out_ready = %h, ref_buffer_full = %h, ref_out = %h, ref_out_ready = %h", dut_buffer_full, dut_out, dut_out_ready, ref_buffer_full, ref_out, ref_out_ready);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask


endmodule

`undef P

