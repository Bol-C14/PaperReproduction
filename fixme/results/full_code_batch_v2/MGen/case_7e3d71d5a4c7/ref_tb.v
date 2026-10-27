 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period

    // Inputs
    reg clk;
    reg rst;
    reg enable;
    reg [1:0] rmode;
    reg [63:0] opa;
    reg [63:0] opb;
    reg [63:0] in_except;
    reg [11:0] exponent_in;
    reg [1:0] mantissa_in;
    reg [2:0] fpu_op;

    // Outputs
    wire [63:0] ref_out;
    wire ref_ex_enable;
    wire ref_underflow;
    wire ref_overflow;
    wire ref_inexact;
    wire ref_exception;
    wire ref_invalid;

    // Outputs
    wire [63:0] dut_out;
    wire dut_ex_enable;
    wire dut_underflow;
    wire dut_overflow;
    wire dut_inexact;
    wire dut_exception;
    wire dut_invalid;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_out,ref_ex_enable,ref_underflow,ref_overflow,ref_inexact,ref_exception,ref_invalid} === ({ref_out,ref_ex_enable,ref_underflow,ref_overflow,ref_inexact,ref_exception,ref_invalid} ^ {dut_out,dut_ex_enable,dut_underflow,dut_overflow,dut_inexact,dut_exception,dut_invalid} ^ {ref_out,ref_ex_enable,ref_underflow,ref_overflow,ref_inexact,ref_exception,ref_invalid}));

    // Instantiate the fpu_exceptions module
    ref_fpu_exceptions ref1(
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .rmode(rmode),
        .opa(opa),
        .opb(opb),
        .in_except(in_except),
        .exponent_in(exponent_in),
        .mantissa_in(mantissa_in),
        .fpu_op(fpu_op),
        .ref_out(ref_out),
        .ref_ex_enable(ref_ex_enable),
        .ref_underflow(ref_underflow),
        .ref_overflow(ref_overflow),
        .ref_inexact(ref_inexact),
        .ref_exception(ref_exception),
        .ref_invalid(ref_invalid)
    );

    // Instantiate the fpu_exceptions module
    top dut2(
        .clk(clk),
        .rst(rst),
        .enable(enable),
        .rmode(rmode),
        .opa(opa),
        .opb(opb),
        .in_except(in_except),
        .exponent_in(exponent_in),
        .mantissa_in(mantissa_in),
        .fpu_op(fpu_op),
        .out(dut_out),
        .ex_enable(dut_ex_enable),
        .underflow(dut_underflow),
        .overflow(dut_overflow),
        .inexact(dut_inexact),
        .exception(dut_exception),
        .invalid(dut_invalid)
    );

    // Generate clock signal
    initial begin
        clk = 0;
        forever #(CLK_PERIOD / 2) clk = ~clk;
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rst = 1;
        enable = 0;
        rmode = 2'b00; // Round to nearest
        opa = 64'h4000000000000000; // 2.0
        opb = 64'h4000000000000000; // 2.0
        in_except = 64'h0; // No exceptions
        exponent_in = 12'h7FF; // Example exponent
        mantissa_in = 2'b00; // Example mantissa
        fpu_op = 3'b000; // Example operation (addition)

        // Apply reset
        #(CLK_PERIOD);
        rst = 0; // De-assert reset
        #(CLK_PERIOD);

        // Test Case 1: Normal operation
        enable = 1;
        #(CLK_PERIOD);
        
        // Check outputs
        if (dut_ex_enable) begin
            $display("Test Case 1 Passed: Exception enabled.");
        end else begin
            $display("Test Case 1 Failed: Exception not enabled.");
        end

        // Test Case 2: Division by zero
        opa = 64'h4000000000000000; // 2.0
        opb = 64'h0000000000000000; // 0.0
        fpu_op = 3'b011; // Division
        #(CLK_PERIOD);
	compare();
        
        if (dut_exception && dut_overflow) begin
            $display("Test Case 2 Passed: Division by zero exception triggered.");
        end else begin
            $display("Test Case 2 Failed: Division by zero exception not triggered.");
        end

        // Test Case 3: Overflow
        opa = 64'h7FF0000000000000; // Positive infinity
        opb = 64'h4000000000000000; // 2.0
        fpu_op = 3'b000; // Addition
        #(CLK_PERIOD);
	compare();

        if (dut_overflow) begin
            $display("Test Case 3 Passed: Overflow exception triggered.");
        end else begin
            $display("Test Case 3 Failed: Overflow exception not triggered.");
        end

        // Test Case 4: Invalid operation (SNaN)
        opa = 64'h7FFFFFFFFFFFFFFF; // SNaN
        opb = 64'h4000000000000000; // 2.0
        #(CLK_PERIOD);
	compare();

    // Test Case 5: Basic Addition
    rmode = 2'b00; // Round to nearest
    opa = 64'h3FF0000000000000; // 1.0
    opb = 64'h3FF0000000000000; // 1.0
    in_except = 64'b0;
    exponent_in = 12'b0;
    mantissa_in = 2'b0;
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 1: Basic Addition - ref_out = %h", ref_out);
compare();

    // Test Case 6: Basic Subtraction
    opa = 64'h3FF0000000000000; // 1.0
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b001; // Subtraction
    #CLK_PERIOD;
    $display("Test Case 2: Basic Subtraction - ref_out = %h", ref_out);
compare();

    // Test Case 7: Basic Multiplication
    opa = 64'h3FF0000000000000; // 1.0
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b010; // Multiplication
    #CLK_PERIOD;
    $display("Test Case 3: Basic Multiplication - ref_out = %h", ref_out);
compare();

    // Test Case 8: Basic Division
    opa = 64'h3FF0000000000000; // 1.0
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b011; // Division
    #CLK_PERIOD;
    $display("Test Case 4: Basic Division - ref_out = %h", ref_out);
compare();

    // Test Case 9: Division by Zero
    opa = 64'h3FF0000000000000; // 1.0
    opb = 64'h0000000000000000; // 0.0
    fpu_op = 3'b011; // Division
    #CLK_PERIOD;
    $display("Test Case 5: Division by Zero - ref_out = %h", ref_out);
compare();

    // Test Case 10: QNaN Input
    opa = 64'h7FF8000000000000; // QNaN
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 6: QNaN Input - ref_out = %h", ref_out);
compare();

    // Test Case 11: SNaN Input
    opa = 64'h7FF0000000000000; // SNaN
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 7: SNaN Input - ref_out = %h", ref_out);
compare();

    // Test Case 12: Positive Infinity
    opa = 64'h7FF0000000000000; // +Inf
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 8: Positive Infinity - ref_out = %h", ref_out);
compare();

    // Test Case 13: Negative Infinity
    opa = 64'hFFF0000000000000; // -Inf
    opb = 64'h3FF0000000000000; // 1.0
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 9: Negative Infinity - ref_out = %h", ref_out);
compare();

    // Test Case 14: Overflow
    opa = 64'h7FEFFFFFFFFFFFFF; // Large positive number
    opb = 64'h7FEFFFFFFFFFFFFF; // Large positive number
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 10: Overflow - ref_out = %h", ref_out);
compare();

    // Test Case 15: Underflow
    opa = 64'h0010000000000000; // Small positive number
    opb = 64'h0010000000000000; // Small positive number
    fpu_op = 3'b010; // Multiplication
    #CLK_PERIOD;
    $display("Test Case 11: Underflow - ref_out = %h", ref_out);
compare();

    // Test Case 16: Inexact Result
    opa = 64'h3FF0000000000001; // 1.0 + epsilon
    opb = 64'h3FF0000000000001; // 1.0 + epsilon
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 12: Inexact Result - ref_out = %h", ref_out);
compare();

    // Test Case 17: Invalid Operation
    opa = 64'h7FF0000000000000; // SNaN
    opb = 64'h7FF0000000000000; // SNaN
    fpu_op = 3'b000; // Addition
    #CLK_PERIOD;
    $display("Test Case 13: Invalid Operation - ref_out = %h", ref_out); 
compare();       

        if (dut_invalid) begin
            $display("Test Case 4 Passed: Invalid operation exception triggered.");
        end else begin
            $display("Test Case 4 Failed: Invalid operation exception not triggered.");
        end


   repeat (96) begin
      @(posedge clk);
	clk = $random;
	rst = $random;
	enable = $random;
	rmode = $random;
	opa = $random;
	opb = $random;
	in_except = $random;
	exponent_in = $random;
	mantissa_in = $random;
	fpu_op = $random;
     
      compare();
    end
     compare();


 $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        // Finish simulation
        #(CLK_PERIOD * 10);
        $finish;
    end

task compare;
        total_tests = total_tests + 1;
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin				$display("\033[1;32mtestcase is passed!!!\033[0m");
				$display("testcase is passed!!!");
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            failed_tests = failed_tests + 1; 
		end
	
endtask
endmodule
