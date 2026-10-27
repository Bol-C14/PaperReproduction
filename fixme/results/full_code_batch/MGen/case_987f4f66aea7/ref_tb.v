 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter LGMEM = 5'd10;
    parameter BUSW = 32;

    // Inputs
    reg i_clk;
    reg i_ce;
    reg i_trigger;
    reg [BUSW-1:0] i_data;
    reg i_wb_clk;
    reg i_wb_cyc;
    reg i_wb_stb;
    reg i_wb_we;
    reg i_wb_addr;
    reg [BUSW-1:0] i_wb_data;

    // Outputs
    wire o_wb_ack,ref_o_wb_ack;
    wire o_wb_stall,ref_o_wb_stall;
    wire [BUSW-1:0] o_wb_data,ref_o_wb_data;
    wire o_interrupt,ref_o_interrupt;

wire       match;
integer    total_tests = 0;
integer    failed_tests = 0;

assign match = ({ref_o_wb_ack, ref_o_wb_stall, ref_o_wb_data, ref_o_interrupt} === {o_wb_ack, o_wb_stall, o_wb_data, o_interrupt});

    // Instantiate the wbscope module
    top #(
        .LGMEM(LGMEM),
        .BUSW(BUSW)
    ) uut (
        .i_clk(i_clk),
        .i_ce(i_ce),
        .i_trigger(i_trigger),
        .i_data(i_data),
        .i_wb_clk(i_wb_clk),
        .i_wb_cyc(i_wb_cyc),
        .i_wb_stb(i_wb_stb),
        .i_wb_we(i_wb_we),
        .i_wb_addr(i_wb_addr),
        .i_wb_data(i_wb_data),
        .o_wb_ack(o_wb_ack),
        .o_wb_stall(o_wb_stall),
        .o_wb_data(o_wb_data),
        .o_interrupt(o_interrupt)
    );

    ref_wbscope #(
        .LGMEM(LGMEM),
        .BUSW(BUSW)
    ) ref_model (
        .i_clk(i_clk),
        .i_ce(i_ce),
        .i_trigger(i_trigger),
        .i_data(i_data),
        .i_wb_clk(i_wb_clk),
        .i_wb_cyc(i_wb_cyc),
        .i_wb_stb(i_wb_stb),
        .i_wb_we(i_wb_we),
        .i_wb_addr(i_wb_addr),
        .i_wb_data(i_wb_data),
        .ref_o_wb_ack(ref_o_wb_ack),
        .ref_o_wb_stall(ref_o_wb_stall),
        .ref_o_wb_data(ref_o_wb_data),
        .ref_o_interrupt(ref_o_interrupt)
    );

    // Clock generation
    initial begin
        i_clk = 0;
        forever #5 i_clk = ~i_clk; // 100MHz clock
    end

    initial begin
        i_wb_clk = 0;
        forever #10 i_wb_clk = ~i_wb_clk; // 50MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        i_ce = 0;
        i_trigger = 0;
        i_data = 0;
        i_wb_cyc = 0;
        i_wb_stb = 0;
        i_wb_we = 0;
        i_wb_addr = 0;
        i_wb_data = 0;

        // Test Case 1: Write to the register
        #15; // Wait for a few clock cycles
        i_ce = 1;
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 0; // Write to address 0
        i_wb_data = 32'h12345678; // Sample data
        #20;

        // Check acknowledgment
        if (!o_wb_ack) $display("Test Case 1 Failed: Expected o_wb_ack = 1, got %b", o_wb_ack);
        compare();

        // Test Case 2: Read back from the register
        i_wb_we = 0; // Change to read
        #10;

        // Check if the data read matches expected
        if (o_wb_data !== 32'h12345678) $display("Test Case 2 Failed: Expected o_wb_data = 0x12345678, got %h", o_wb_data);
        compare();

        // Test Case 3: Trigger the scope
        i_trigger = 1; // Set trigger
        #10;
        i_trigger = 0; // Reset trigger

        // Check interrupt signal
        if (!o_interrupt) $display("Test Case 3 Failed: Expected o_interrupt = 1, got %b", o_interrupt);
        compare();

        // Test Case 4: Check stall signal
        if (o_wb_stall) $display("Test Case 4 Failed: Expected o_wb_stall = 0, got %b", o_wb_stall);
        compare();

        repeat (1000) begin
            #10; // Wait for a short period
            i_ce = $random % 2; // Random value for i_ce
            i_trigger = $random % 2; // Random value for i_trigger
            i_data = $random; // Random value for i_data
            i_wb_cyc = $random % 2; // Random value for i_wb_cyc
            i_wb_stb = $random % 2; // Random value for i_wb_stb
            i_wb_we = $random % 2; // Random value for i_wb_we
            i_wb_data = $random; // Random value for i_wb_data
            i_wb_addr = $random % (1 << LGMEM); // Random address within the memory range
        #10;
        compare();
        end

        // Edge case testing
        test_single_cycle();
        test_multiple_cycles();
        test_boundary_conditions();

        // Finish simulation after tests
        #50;
    $display("\033[1;34mAll tests completed.\033[0m");
    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $finish;
    end

    // Test single cycle
    task test_single_cycle;
    begin
        i_ce = 1;
        i_trigger = 1;
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 0;
        i_wb_data = 32'hA5A5A5A5;
        #10;
        i_wb_stb = 0; // Single cycle write
    end
    endtask

    // Test multiple cycles
    task test_multiple_cycles;
    begin
        i_ce = 1;
        i_trigger = 1;
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 0;
        i_wb_data = 32'hA5A5A5A5;
        repeat (5) begin
            #10;
            i_wb_addr = i_wb_addr + 1; // Multiple cycle write
        end
        i_wb_stb = 0; // End of multiple cycle write
    end
    endtask

    // Test boundary conditions
    task test_boundary_conditions;
    begin
        i_ce = 1;
        i_trigger = 1;
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = (1 << LGMEM) - 1; // Boundary address
        i_wb_data = 32'h5A5A5A5A;
        #10;
        i_wb_stb = 0; // Write at boundary address
    end
    endtask


task compare;
     total_tests = total_tests + 1;
     if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
	   begin
	   $display("\033[1;32mtestcase is passed!!!\033[0m");
	   end
	   else begin
	   $display("\033[1;31mtestcase is failed!!!\033[0m");
         failed_tests = failed_tests + 1; 
         end
endtask

endmodule
