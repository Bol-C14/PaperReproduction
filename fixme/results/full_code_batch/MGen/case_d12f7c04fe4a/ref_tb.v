 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter WIDTH_IN = 4;
    parameter WIDTH_OUT = 8;

    // Testbench signals
    reg cin;
    reg [WIDTH_IN-1:0] data;
    reg add_sub;
    reg clock;
    reg sload;
    reg clken;
    reg sign_data;
    reg aclr;
    
    // Outputs
    wire [WIDTH_OUT-1:0] result_ref, result_dut;
    wire cout_ref, cout_dut;
    wire overflow_ref, overflow_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({result_ref, cout_ref, overflow_ref} === ({result_ref, cout_ref, overflow_ref} ^ {result_dut, cout_dut, overflow_dut} ^ {result_ref, cout_ref, overflow_ref}));


    // Instantiate the altaccumulate module
    altaccumulate_ref #(
        .width_in(WIDTH_IN),
        .width_out(WIDTH_OUT),
        .extra_latency(1)
    ) ref_model (
        .cin(cin),
        .data(data),
        .add_sub(add_sub),
        .clock(clock),
        .sload(sload),
        .clken(clken),
        .sign_data(sign_data),
        .aclr(aclr),
        .result(result_ref),
        .cout(cout_ref),
        .overflow(overflow_ref)
    );

    top #(
        .width_in(WIDTH_IN),
        .width_out(WIDTH_OUT),
        .extra_latency(1)
    ) dut (
        .cin(cin),
        .data(data),
        .add_sub(add_sub),
        .clock(clock),
        .sload(sload),
        .clken(clken),
        .sign_data(sign_data),
        .aclr(aclr),
        .result(result_dut),
        .cout(cout_dut),
        .overflow(overflow_dut)
    );


    // Clock generation
    initial begin
        clock = 0;
        forever #5 clock = ~clock; // 100 MHz clock
    end

    // Test procedure
    initial begin
        // Initialize signals
        cin = 0;
        data = 0;
        add_sub = 0;
        sload = 0;
        clken = 0;
        sign_data = 0;
        aclr = 0;

        // Release reset
        #10;
        aclr = 1; // Assert reset
        #10;
        aclr = 0;// De-assert reset
        clken = 1;

        //Load
        @(negedge clock);
        sload = 1;
        data = 4'hA;
        @(negedge clock);
        sign_data = 1;
        add_sub = 0;
        sload = 0;
        data = 4'hF;
        cin = 0;
        @(negedge clock);
        compare();

        
        // Test Case 1: Addition
        repeat (25) begin
            data = $random; // Input data
            add_sub = 1; // Addition
            cin = $random; // Carry in
            sload = 0; // Not loading
            @(negedge clock);
            compare();
        end

        @(negedge clock);
        compare();
        sload = 1;
        data = 4'hF;
        @(negedge clock);
        compare();

        // Test Case 2: Subtraction
        repeat (25) begin
            data = $random; // Input data
            add_sub = 0; // Addition
            cin = $random; // Carry in
            sload = 0; // Not loading
            @(negedge clock);
            compare();
        end

        @(negedge clock);
        compare();
        sload = 1;
        data = 4'h7;
        @(negedge clock);
        compare();
        sload = 0; // Not loading

        
        repeat (45) begin
            data = $random; // Input data
            add_sub = $random; // Addition
            cin = $random; // Carry in
            sign_data = $random;
            @(negedge clock);
            compare();
        end

        #10;
        aclr = 1; // Assert reset
        clken = 0;
        #10;
        aclr = 0;// De-assert reset
        clken = 1;
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
      
        // Finish simulation
        $finish;
    end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("cin, data = %h, add_sub = %h, sload = %h, clken = %h, sign_data = %h, aclr = %h, result_dut = %h, cout_dut = %h, overflow_dut = %h, result_ref = %h, cout_ref = %h, overflow_ref = %h", cin, data, add_sub, sload, clken, sign_data, aclr, result_dut, cout_dut, overflow_dut, result_ref, cout_ref, overflow_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("cin, data = %h, add_sub = %h, sload = %h, clken = %h, sign_data = %h, aclr = %h, result_dut = %h, cout_dut = %h, overflow_dut = %h, result_ref = %h, cout_ref = %h, overflow_ref = %h", cin, data, add_sub, sload, clken, sign_data, aclr, result_dut, cout_dut, overflow_dut, result_ref, cout_ref, overflow_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask


    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end
    
endmodule
