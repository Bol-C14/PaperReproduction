 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter number_of_channels = 1;
    parameter deserialization_factor = 4;
    parameter NUMBER_OF_CHANNELS = 1;

    // Inputs
    reg [number_of_channels - 1:0] rx_in;
    reg rx_fastclk;
    reg rx_slowclk;
    reg rx_locked;
    reg [number_of_channels - 1:0] rx_coreclk;
    reg [number_of_channels - 1:0] rx_reset;
    reg [number_of_channels - 1:0] rx_dpll_reset;
    reg [number_of_channels - 1:0] rx_channel_data_align;

    // Outputs
    wire [deserialization_factor * number_of_channels - 1:0] rx_out,ref_rx_out;
    wire [number_of_channels - 1:0] rx_dpa_locked,ref_rx_dpa_locked;

wire       match;
integer    total_tests = 0;
integer    failed_tests = 0;
assign match = ({ref_rx_out, ref_rx_dpa_locked} === {rx_out, rx_dpa_locked});

    // Instantiate the stratixgx_dpa_lvds_rx module
    top #(
        .number_of_channels(number_of_channels),
        .deserialization_factor(deserialization_factor)
    ) uut (
        .rx_in(rx_in),
        .rx_fastclk(rx_fastclk),
        .rx_slowclk(rx_slowclk),
        .rx_locked(rx_locked),
        .rx_coreclk(rx_coreclk),
        .rx_reset(rx_reset),
        .rx_dpll_reset(rx_dpll_reset),
        .rx_channel_data_align(rx_channel_data_align),
        .rx_out(rx_out),
        .rx_dpa_locked(rx_dpa_locked)
    );

    ref_stratixgx_dpa_lvds_rx #(
        .number_of_channels(number_of_channels),
        .deserialization_factor(deserialization_factor)
    ) ref_model (
        .rx_in(rx_in),
        .rx_fastclk(rx_fastclk),
        .rx_slowclk(rx_slowclk),
        .rx_locked(rx_locked),
        .rx_coreclk(rx_coreclk),
        .rx_reset(rx_reset),
        .rx_dpll_reset(rx_dpll_reset),
        .rx_channel_data_align(rx_channel_data_align),
        .ref_rx_out(ref_rx_out),
        .ref_rx_dpa_locked(ref_rx_dpa_locked)
    );


    // Clock generation
    initial begin
        rx_fastclk = 0;
        forever #10 rx_fastclk = ~rx_fastclk; // 100MHz clock
    end

    initial begin
        rx_slowclk = 0;
        forever #20 rx_slowclk = ~rx_slowclk; // 50MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rx_in = 0;
        rx_locked = 0;
        rx_coreclk = 0;
        rx_reset = 0;
        rx_dpll_reset = 0;
        rx_channel_data_align = 0;

        // Test Case 1: Basic Reset and Initialization
        #15;
        rx_reset = 1; // Assert reset
            compare();
        #10;
        rx_reset = 0; // Deassert reset
            compare();

        // Test Case 2: Simulate the input data
        #20;
        rx_locked = 1; // Set locked
        rx_in = 1; // Simulate input signal
            compare();

        // Apply core clock
        #5 rx_coreclk = 1;
            compare();
        #5 rx_coreclk = 0;
            compare();

        // Check output after applying input
        #10;
        if (rx_out !== {deserialization_factor{1'b0}}) begin
            compare();
            $display("Test Case 2 Failed: Expected rx_out = 0, got %b", rx_out);
        end

        // Test Case 3: Data Alignment and DPA Locked
        rx_channel_data_align = 1; // Enable data alignment
        #20;

        // Check DPA locked
        if (rx_dpa_locked !== {number_of_channels{1'b1}}) begin
            compare();
            $display("Test Case 3 Failed: Expected rx_dpa_locked = 1, got %b", rx_dpa_locked);
        end

        // Test Case 4: Check output data after alignment
        #10;
        if (rx_out !== {deserialization_factor{1'b0}}) begin
            compare();
            $display("Test Case 4 Failed: Expected rx_out = 0, got %b", rx_out);
        end

        #10;
        repeat (1000) begin
            @(posedge rx_fastclk);
            rx_in = $random % (1 << NUMBER_OF_CHANNELS);
            rx_locked = $random % 2;
            rx_coreclk = $random % (1 << NUMBER_OF_CHANNELS);
            rx_dpll_reset = $random % (1 << NUMBER_OF_CHANNELS);
            rx_channel_data_align = $random % (1 << NUMBER_OF_CHANNELS);
             #10;
            compare();
        end

        // Finish simulation after tests
        #50;
        $display("All tests completed.");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $finish;
    end

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
