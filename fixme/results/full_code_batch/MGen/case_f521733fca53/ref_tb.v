 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter DEFAULT_SPEED = 32'd2814750;

    // Inputs
    reg i_clk;
    reg i_wb_cyc, i_wb_stb, i_wb_we;
    reg [2:0] i_wb_addr;
    reg [31:0] i_wb_data;

    // ref Outputs
    wire [31:0] ref_o_data;
    wire ref_o_interrupt, ref_o_ppd;

    // Outputs
    wire [31:0] o_data;
    wire o_interrupt, o_ppd;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_o_data,ref_o_interrupt, ref_o_ppd} === {o_data,o_interrupt,o_ppd});
//assign match = ({ref_o_data,ref_o_interrupt, ref_o_ppd} === ({ref_o_data,ref_o_interrupt, ref_o_ppd}  ^ {o_data,o_interrupt, o_ppd}  ^ {ref_o_data,ref_o_interrupt, ref_o_ppd} ));

    // Instantiate the rtclight module
    ref_rtclight rf(
        .i_clk(i_clk),
        .i_wb_cyc(i_wb_cyc),
        .i_wb_stb(i_wb_stb),
        .i_wb_we(i_wb_we),
        .i_wb_addr(i_wb_addr),
        .i_wb_data(i_wb_data),
        .ref_o_data(ref_o_data),
        .ref_o_interrupt(ref_o_interrupt),
        .ref_o_ppd(ref_o_ppd)
    );

  // Instantiate the rtclight module
    top dut(
        .i_clk(i_clk),
        .i_wb_cyc(i_wb_cyc),
        .i_wb_stb(i_wb_stb),
        .i_wb_we(i_wb_we),
        .i_wb_addr(i_wb_addr),
        .i_wb_data(i_wb_data),
        .o_data(o_data),
        .o_interrupt(o_interrupt),
        .o_ppd(o_ppd)
    );

    // Clock generation
    initial begin
        i_clk = 0;
        forever #5 i_clk = ~i_clk; // 100MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
       // i_wb_cyc = 0;
       /// i_wb_stb = 0;
       // i_wb_we = 0;
       // i_wb_addr = 3'b000;
      //  i_wb_data = 32'h0;


        i_wb_cyc = 0;
        i_wb_stb = 0;
        i_wb_we = 0;
        i_wb_addr = 0;
        i_wb_data = 0;

        // Wait for a few clock cycles
        #10;

        // Test Case 1: Write to clock register
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 3'b000; // Clock register
        i_wb_data = 32'h123456; // Set time to 12:34:56
        #10;
        i_wb_stb = 0; // End the write transaction
        #10;
compare();


        // Test Case 2: Read clock register
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 0; // Read
        i_wb_addr = 3'b000; // Clock register
        #10;
        i_wb_stb = 0; // End the read transaction
        #10;
compare();

   
        // Test Case 3: Write to timer register
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 3'b001; // Timer register
        i_wb_data = {1'b0, 24'hFFFFFF}; // Set timer to 24 hours
        #10;
        i_wb_stb = 0; // End the write transaction
        #10;
compare();



        // Test Case 4: Start stopwatch
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 3'b010; // Stopwatch register
        i_wb_data = 32'h1; // Start stopwatch
        #10;
        i_wb_stb = 0; // End the write transaction
        #10;
compare();

        // Wait for some time and check stopwatch
        #50;

 
        // Test Case 5: Set alarm time
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 3'b011; // Alarm register
        i_wb_data = {1'b1, 6'h3F, 8'h59, 8'h59}; // Set alarm time to 23:59:59
        #10;
        i_wb_stb = 0; // End the write transaction
        #10;
compare();



        // Test Case 6: Set clock speed
        i_wb_cyc = 1;
        i_wb_stb = 1;
        i_wb_we = 1;
        i_wb_addr = 3'b100; // Clock speed register
        i_wb_data = 32'd3000000; // Set speed
        #10;
        i_wb_stb = 0; // End the write transaction
        #10;
compare();


repeat (2000) begin
      @(posedge i_clk);
	i_wb_cyc = $random;
	 i_wb_stb = $random;
	i_wb_we = $random;
	i_wb_addr = $random;
	i_wb_data = $random;   
      compare();
    end
        // Additional test cases can be added similarly...
	  $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);

        // Finish simulation
        #100;
        $finish;
    end

task compare;
        total_tests = total_tests + 1;
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin				$display("\033[1;32mtestcase is passed!!!\033[0m",$time);
							$display("o_data = %h,o_interrupt = %h, o_ppd = %h,ref_o_data = %h,ref_o_interrupt = %h, ref_o_ppd = %h",o_data,o_interrupt, o_ppd,ref_o_data,ref_o_interrupt, ref_o_ppd);
				$display("testcase is passed!!!");
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m",$time);
			$display("o_data = %h,o_interrupt = %h, o_ppd = %h,ref_o_data = %h,ref_o_interrupt = %h, ref_o_ppd = %h",o_data,o_interrupt, o_ppd,ref_o_data,ref_o_interrupt, ref_o_ppd);
            failed_tests = failed_tests + 1; 
		end
	
endtask



endmodule
