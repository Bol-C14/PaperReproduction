 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter BW = 32;
    
    // Inputs
    reg i_clk;
    reg i_rst;
    reg i_wr;
    reg i_signed;
    reg [BW-1:0] i_numerator;
    reg [BW-1:0] i_denominator;
    
    // Outputs
    wire o_busy_dut, o_busy_ref;
    wire o_valid_dut, o_valid_ref;
    wire o_err_dut, o_err_ref;
    wire [BW-1:0] o_quotient_dut, o_quotient_ref;
    wire [3:0] o_flags_dut, o_flags_ref;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref} === ({o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref} ^ {o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut} ^ {o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref}));


    // Instantiate the div module
    div_ref #(.BW(BW)) ref_model (
        .i_clk(i_clk),
        .i_rst(i_rst),
        .i_wr(i_wr),
        .i_signed(i_signed),
        .i_numerator(i_numerator),
        .i_denominator(i_denominator),
        .o_busy_ref(o_busy_ref),
        .o_valid_ref(o_valid_ref),
        .o_err_ref(o_err_ref),
        .o_quotient_ref(o_quotient_ref),
        .o_flags_ref(o_flags_ref)
    );
    top #(.BW(BW)) dut (
        .i_clk(i_clk),
        .i_rst(i_rst),
        .i_wr(i_wr),
        .i_signed(i_signed),
        .i_numerator(i_numerator),
        .i_denominator(i_denominator),
        .o_busy(o_busy_dut),
        .o_valid(o_valid_dut),
        .o_err(o_err_dut),
        .o_quotient(o_quotient_dut),
        .o_flags(o_flags_dut)
    );


    // Clock generation
    initial begin
        i_clk = 0;
        forever #5 i_clk = ~i_clk; // 100 MHz clock
    end

    // Test procedure
    initial begin
        // Initialize inputs
        i_rst = 1;
        i_wr = 0;
        i_signed = 0;
        i_numerator = 0;
        i_denominator = 0;

        // Reset the module
        #10;
        i_rst = 0;

        @(negedge i_clk);        
        // Test Case 1: Basic Division
        i_wr = 1;
        i_signed = 0;
        i_numerator = 32'h0000000A;  // 10
        i_denominator = 32'h00000002; // 2
        #10; // Wait for processing
        i_wr = 0; // Release write
        compare(); // Wait for valid output


        // Test Case 2: Division by Zero
        @(negedge i_clk);
        i_wr = 1;
        i_signed = 0;
        i_numerator = 32'h0000000A;  // 10
        i_denominator = 32'h00000000; // 0
        #10; // Wait for processing
        i_wr = 0; // Release write
        compare(); // Wait for valid output

        @(negedge i_clk);
        i_wr = 1;
        i_signed = 0;
        i_numerator = 32'h00000000;  // 0
        i_denominator = 32'h0000000A; // 10
        #10; // Wait for processing
        i_wr = 0; // Release write
        compare(); // Wait for valid output

        // Test Case 3: Negative Result
        @(negedge i_clk);
        i_wr = 1;
        i_signed = 1;
        i_numerator = 32'hFFFFFFFF;  // -1
        i_denominator = 32'h00000002; // 2
        #10; // Wait for processing
        i_wr = 0; // Release write<F2>
        compare(); // Wait for valid output

        repeat (96) begin
            @(negedge i_clk);
            i_wr = 1;
            i_signed = $random;
            i_numerator = $random;  
            i_denominator = $random;
            #10;
            i_wr = 0;
            compare();
        end

        // Test Case 4: Reset Functionality
        @(negedge i_clk);
        i_rst = 1; // Assert reset
        @(negedge i_clk);
        i_rst = 0; // Release reset
        #10;
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
    end

    task compare;
        total_tests = total_tests + 1;
        wait (o_valid_dut == 1);
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask


    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
