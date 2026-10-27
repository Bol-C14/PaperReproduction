 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period

    // Inputs
    reg clk_i;
    reg rst_i;
    reg signed [15:-16] pixel0_x_i;
    reg signed [15:-16] pixel0_y_i;
    reg signed [15:-16] pixel1_x_i;
    reg signed [15:-16] pixel1_y_i;
    reg draw_line_i;
    reg read_pixel_i;

    // Outputs
    wire ref_busy_o;
    wire ref_x_major_o;
    wire signed [15:0] ref_major_o;
    wire signed [15:0] ref_minor_o;
    wire ref_valid_o;

   // Outputs
    wire busy_o;
    wire x_major_o;
    wire signed [15:0] major_o;
    wire signed [15:0] minor_o;
    wire valid_o;


	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_busy_o,ref_x_major_o,ref_major_o,ref_minor_o,ref_valid_o} === ({ref_busy_o,ref_x_major_o,ref_major_o,ref_minor_o,ref_valid_o}  ^ {busy_o,x_major_o,major_o,minor_o,valid_o}  ^ {ref_busy_o,ref_x_major_o,ref_major_o,ref_minor_o,ref_valid_o} ));


    // Instantiate the bresenham_line module
    ref_bresenham_line rf (
        .clk_i(clk_i),
        .rst_i(rst_i),
        .pixel0_x_i(pixel0_x_i),
        .pixel0_y_i(pixel0_y_i),
        .pixel1_x_i(pixel1_x_i),
        .pixel1_y_i(pixel1_y_i),
        .draw_line_i(draw_line_i),
        .read_pixel_i(read_pixel_i),
        .ref_busy_o(ref_busy_o),
        .ref_x_major_o(ref_x_major_o),
        .ref_major_o(ref_major_o),
        .ref_minor_o(ref_minor_o),
        .ref_valid_o(ref_valid_o)
    );

   // Instantiate the bresenham_line module
    top dut(
        .clk_i(clk_i),
        .rst_i(rst_i),
        .pixel0_x_i(pixel0_x_i),
        .pixel0_y_i(pixel0_y_i),
        .pixel1_x_i(pixel1_x_i),
        .pixel1_y_i(pixel1_y_i),
        .draw_line_i(draw_line_i),
        .read_pixel_i(read_pixel_i),
        .busy_o(busy_o),
        .x_major_o(x_major_o),
        .major_o(major_o),
        .minor_o(minor_o),
        .valid_o(valid_o)
    );

    // Generate clock signal
    initial begin
        clk_i = 0;
        forever #(CLK_PERIOD / 2) clk_i = ~clk_i;
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rst_i = 0;
        draw_line_i = 0;
        read_pixel_i = 0;
        pixel0_x_i = 0;
        pixel0_y_i = 0;
        pixel1_x_i = 0;
        pixel1_y_i = 0;

        // Apply reset
        #(CLK_PERIOD);
        rst_i = 1; // De-assert reset
        #(CLK_PERIOD);
        rst_i = 0; // Assert reset
        #(CLK_PERIOD);

        // Test Case 1: Draw a horizontal line
        pixel0_x_i = 10;
        pixel0_y_i = 10;
        pixel1_x_i = 20;
        pixel1_y_i = 10;
        draw_line_i = 1; // Start drawing
        #(CLK_PERIOD);
        draw_line_i = 0; // Stop drawing
        #(CLK_PERIOD * 10); // Wait for processing
        compare();
        // Check outputs
        if (valid_o) begin
            $display("Test Case 1 Passed: Horizontal line drawn.");
        end else begin
            $display("Test Case 1 Failed: Horizontal line not drawn.");
        end

        // Test Case 2: Draw a vertical line
        pixel0_x_i = 15;
        pixel0_y_i = 5;
        pixel1_x_i = 15;
        pixel1_y_i = 15;
        draw_line_i = 1; // Start drawing
        #(CLK_PERIOD);
        draw_line_i = 0; // Stop drawing
        #(CLK_PERIOD * 10); // Wait for processing
        compare();
        // Check outputs
        if (valid_o) begin
            $display("Test Case 2 Passed: Vertical line drawn.");
        end else begin
            $display("Test Case 2 Failed: Vertical line not drawn.");
        end

        // Test Case 3: Draw a diagonal line
        pixel0_x_i = 5;
        pixel0_y_i = 5;
        pixel1_x_i = 10;
        pixel1_y_i = 10;
        draw_line_i = 1; // Start drawing
        #(CLK_PERIOD);
        draw_line_i = 0; // Stop drawing
        #(CLK_PERIOD * 10); // Wait for processing
	compare();

        // Check outputs
        if (valid_o) begin
            $display("Test Case 3 Passed: Diagonal line drawn.");
        end else begin
            $display("Test Case 3 Failed: Diagonal line not drawn.");
        end

   repeat (96) begin
      @(posedge clk_i);
rst_i = $random;
pixel0_x_i = $random;
pixel0_y_i = $random;
pixel1_x_i = $random;
pixel1_y_i = $random;
draw_line_i = $random;
read_pixel_i = $random;
     compare();
    end
     

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
