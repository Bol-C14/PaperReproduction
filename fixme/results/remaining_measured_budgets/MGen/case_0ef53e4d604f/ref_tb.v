 `timescale 1ns / 1ps

module tb;

    // Parameters
    reg CS;
    reg WR;
    reg clk;
    reg cmd;
    reg [7:0] din;
    reg [1:0] CE;

    wire [7:0] dout_ref, dout_dut;
    wire [7:0] mode_ref, mode_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({dout_ref, mode_ref} === ({dout_ref, mode_ref} ^ {dout_dut, mode_dut} ^ {dout_ref, mode_ref}));


    // Instantiate the counter module
    counter_ref ref_model (
        .CS(CS),
        .WR(WR),
        .clk(clk),
        .cmd(cmd),
        .din(din),
        .dout_ref(dout_ref),
        .mode_ref(mode_ref),
        .CE(CE)
    );

    top dut (
        .CS(CS),
        .WR(WR),
        .clk(clk),
        .cmd(cmd),
        .din(din),
        .dout(dout_dut),
        .mode(mode_dut),
        .CE(CE)
    );


    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100 MHz clock
    end

    // Test procedure
    initial begin
        // Initialize inputs
        CS = 0;
        WR = 0;
        cmd = 0;
        din = 0;
        CE = 2'b00;

        // Test Case 1: Write command
        #10;
        CS = 1; WR = 1; cmd = 1; din = 8'b00011000; CE = 2'b10; // Set mode
        #10;
        CS = 0; WR = 0; // Release CS
        #100;
        compare();

        // Test Case 2: Read operation
        #10;
        CS = 1; WR = 0; cmd = 0; CE = 2'b10; // Start read
        #10;
        CS = 0; // Release CS
        #100;
        compare();

        // Test Case 3: Initialize counter
        #10;
        CS = 1; WR = 1; cmd = 0; din = 8'hFF; CE = 2'b10; // Initialize counter
        #10;
        CS = 0; WR = 0; // Release CS
        #100;
        compare();

        // Test Case 4: Counter decrement
        #10;
        CE = 2'b10; // Enable counter operation
        #100;
        compare();

        // Test Case 5: New command
        #10;
        CS = 1; WR = 1; cmd = 1; din = 8'b00000111; CE = 2'b10; // New command
        #10;
        CS = 0; WR = 0; // Release CS
        #100;
        compare();

        // Test Case 6: Stop counter
        #10;
        CS = 1; WR = 0; cmd = 0; CE = 2'b10; // Read stop
        #10;
        CS = 0; // Release CS
        #100;
        compare();

        CS = 1; WR = 0; cmd = 1; CE = 2'b10;
        din = 8'b00101000;
        #10;
        CS = 0;
        #500000;
        compare();
        
        #10;
        CS = 1; WR = 1; cmd = 1; CE = 2'b10;
        din = 8'b00100000;
        #20;
        CS = 1; WR = 1; cmd = 0;
        #10;
        CS = 0;
        #700000;
        compare();


        repeat (192) begin
            CS = 1;
            WR = $random;
            cmd = $random;
            din = $random;
            CE = $random;
            #50;
            CS = 0;
            #500000;
            compare();
        end
        // Finish simulation
        #100;

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
//				$display("testcase is passed!!!");
            	$display("CS = %b, WR = %b, cmd = %b, din = %b, CE = %b, dout_dut = %b, mode_dut = %b, dout_ref = %b, mode_ref = %b", CS, WR, cmd, din, CE, dout_dut, mode_dut, dout_ref, mode_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("CS = %b, WR = %b, cmd = %b, din = %b, CE = %b, dout_dut = %b, mode_dut = %b, dout_ref = %b, mode_ref = %b", CS, WR, cmd, din, CE, dout_dut, mode_dut, dout_ref, mode_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

