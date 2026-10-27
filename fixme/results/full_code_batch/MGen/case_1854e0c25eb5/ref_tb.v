 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter I2C_ADR = 7'b001_0000; // Address of the slave device
    parameter CLK_PERIOD = 20000; // Clock period for SCL

    // Inputs
    reg scl;
    reg sda;
    reg in;

    // Outputs
    wire ref_sda,dut_sda;

   assign ref_sda = in? sda : 1'bz;
   assign dut_sda = in? sda : 1'bz;

    wire match;
    integer total_tests = 0;
    integer failed_tests = 0;

assign match =(ref_sda === dut_sda);

    // Instantiate the i2c_slave_model
    top #(.I2C_ADR(I2C_ADR)) uut1 (
        .scl(scl),
        .sda(dut_sda)
	
    );

   // Instantiate the i2c_slave_model
    ref_i2c_slave_model #(.I2C_ADR(I2C_ADR)) uut2 (
        .scl(scl),
        .ref_sda(ref_sda)
    );

    // Generate clock signal for SCL
    initial begin
        scl = 0;
        forever #(CLK_PERIOD / 2) scl = ~scl; // Toggle clock
    end

    // Test Procedure
    initial begin
        // Initialize SDA line as high (idle state)
        sda = 1'b1;
        in = 1;

        // Wait for a clock cycle
        @(posedge scl);
          #5000;
    
        // Test Case 1: Start condition
        sda = 1'b0; // Pull SDA low
        @(negedge scl);
          #5000;
        sda = 1'b1; // 
        @(negedge scl);
          #5000;
        sda = 1'b1; // 
        @(negedge scl);
          #5000;
        sda = 1'b1; //
        @(negedge scl);
          #5000;
        sda = 1'b1; //
        @(negedge scl);
          #5000;
        sda = 1'b1; // 
        @(negedge scl);
          #5000;
        sda = 1'b1; //
        @(negedge scl);
          #5000;
        sda = 1'b1; //
        @(negedge scl);
          #5000;
        sda = 1'b0; //
        @(posedge scl);
          #5000;
        sda = 1'b1; // Release SDA
          #20000;
	compare();

        // Check for Start condition

        // Test Case 2: Send Address (Write)
        @(posedge scl);
          #5000;
        sda = 1'b0; // Start condition
        @(negedge scl);
          #5000;
        sda = I2C_ADR[6]; // Send high bit of address
        @(negedge scl);
          #5000;
        sda = I2C_ADR[5]; // Send next bit
        @(negedge scl);
          #5000;
        sda = I2C_ADR[4]; // Continue sending bits
        @(negedge scl);
          #5000;
        sda = I2C_ADR[3];
        @(negedge scl);
          #5000;
        sda = I2C_ADR[2];
        @(negedge scl);
          #5000;
        sda = I2C_ADR[1];
        @(negedge scl);
          #5000;
        sda = I2C_ADR[0]; // Send last bit
        @(negedge scl);
          #5000;
        sda = 1'b0; //
        @(negedge scl);
          #5000;
        sda = 1'b0; //
        repeat (10000) @(posedge scl);
          #5000;
        sda = 1'b1; // Release SDA
          #200000;
	compare();




      repeat (998) begin
        @(posedge scl);
        sda = 1'b0; // Pull SDA low
        @(negedge scl);
          #5000;
        sda = $random; // 
        @(negedge scl);
          #5000;
        sda = $random; // 
        @(negedge scl);
          #5000;
        sda = $random;//
        @(negedge scl);
          #5000;
        sda = $random; //
        @(negedge scl);
          #5000;
        sda = $random; // 
        @(negedge scl);
          #5000;
        sda = $random; //
        @(negedge scl);
          #5000;
        sda = $random; //
        @(negedge scl);
          #5000;
        sda = $random; //
        @(negedge scl);
          #5000;
        sda = 0; //
        @(posedge scl);
          #5000;
        sda = 1; // Release SDA
          #200000;
	  compare();
       end

        #(CLK_PERIOD * 10);

    // Finish simulation
        $display("All tests passed: design passed");
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


    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end


endmodule
