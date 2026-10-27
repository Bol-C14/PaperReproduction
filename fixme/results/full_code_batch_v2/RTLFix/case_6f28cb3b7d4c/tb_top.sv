`timescale 1ns/1ps

// This is your top-level testbench module
// DO NOT change the file name or module name
module tb_top;
    // Testbench signals
    reg d0, d1, d2, d3, s1, s0;
    wire y;
    
    // Test counters
    integer test_count;
    integer pass_count;
    integer fail_count;

    // Instantiate the DUT (Device Under Test)
    mux dut (
        .d0(d0),
        .d1(d1),
        .d2(d2),
        .d3(d3),
        .s1(s1),
        .s0(s0),
        .y(y)
    );

    // Waveform dump
    // Do not remove
    initial begin
        $dumpfile("dump.fst");
        $dumpvars(0, tb_top);
    end

    // Test sequence
    initial begin
        // Initialize counters
        test_count = 0;
        pass_count = 0;
        fail_count = 0;
        
        // Test all combinations
        $display("Testing 4:1 Multiplexer");
        $display("s1 s0 | d0 d1 d2 d3 | mux1_out mux2_out | y | expected_y");
        
        // s1=0, s0=0 -> y=d0
        s1=0; s0=0; d0=0; d1=1; d2=1; d3=0; #10;
        check_internal();
        
        // s1=0, s0=1 -> y=d1
        s1=0; s0=1; d0=0; d1=1; d2=1; d3=0; #10;
        check_internal();
        
        // s1=1, s0=0 -> y=d2
        s1=1; s0=0; d0=0; d1=1; d2=0; d3=0; #10;
        check_internal();
        
        // s1=1, s0=1 -> y=d3
        s1=1; s0=1; d0=0; d1=1; d2=1; d3=1; #10;
        check_internal();
        
        // Additional test with different data
        s1=0; s0=0; d0=1; d1=0; d2=0; d3=1; #10;
        check_internal();
        
        s1=1; s0=1; d0=1; d1=0; d2=1; d3=1; #10;
        check_internal();
        
        // Final summary
        $display("\n============================================================");
        $display("Test Summary:");
        $display("Total Tests: %0d", test_count);
        $display("Passed: %0d", pass_count);
        $display("Failed: %0d", fail_count);
        
        if (fail_count == 0) begin
            $display("\n*** ALL TESTS PASSED ***");
        end else begin
            $display("\n*** SOME TESTS FAILED ***");
        end
        $display("============================================================");
        
        // End simulation
        $display("\nTest completed");
        $finish;
    end

    task check_internal;
        reg expected_mux1_out, expected_mux2_out, expected_y;
        integer errors;
        begin
            errors = 0;
            expected_mux1_out = s0 ? d1 : d0;
            expected_mux2_out = s0 ? d3 : d2;
            expected_y = s1 ? expected_mux2_out : expected_mux1_out;
            
            $display("%b  %b  | %b  %b  %b  %b  |    %b        %b     | %b |     %b", 
                     s1, s0, d0, d1, d2, d3, dut.mux1_out, dut.mux2_out, y, expected_y);
            
            if (dut.mux1_out !== expected_mux1_out) begin
                $display("ERROR: Internal mux1_out mismatch: expected %b, got %b", expected_mux1_out, dut.mux1_out);
                errors = errors + 1;
            end
            if (dut.mux2_out !== expected_mux2_out) begin
                $display("ERROR: Internal mux2_out mismatch: expected %b, got %b", expected_mux2_out, dut.mux2_out);
                errors = errors + 1;
            end
            if (y !== expected_y) begin
                $display("ERROR: Output y mismatch: expected %b, got %b", expected_y, y);
                errors = errors + 1;
            end
            
            if (errors == 0) begin
                pass_count = pass_count + 1;
            end else begin
                fail_count = fail_count + 1;
            end
            test_count = test_count + 1;
        end
    endtask

endmodule