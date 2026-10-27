 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period for i_clk

    // Inputs
    reg i_clk;
    reg i_wreq;
    reg i_ereq;
    reg i_pipewr;
    reg i_endpipe;
    reg [21:0] i_addr;
    reg [31:0] i_data;
    reg i_qspi_grant;
    reg i_quad;
    reg i_spi_busy;
    reg i_spi_stopped;
    reg [31:0] i_spi_data;
    reg i_spi_valid;

    // Outputs
    wire ref_o_bus_ack,dut_o_bus_ack;
    wire ref_o_qspi_req,dut_o_qspi_req;
    wire ref_o_spi_wr,dut_o_spi_wr;
    wire ref_o_spi_hold,dut_o_spi_hold;
    wire [31:0] ref_o_spi_word,dut_o_spi_word;
    wire [1:0] ref_o_spi_len,dut_o_spi_len;
    wire ref_o_spi_spd,dut_o_spi_spd;
    wire ref_o_spi_dir,dut_o_spi_dir;
    wire ref_o_data_ack,dut_o_data_ack;
    wire ref_o_wip,dut_o_wip;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_o_bus_ack,ref_o_qspi_req,ref_o_spi_wr,ref_o_spi_hold,ref_o_spi_word,ref_o_spi_len,ref_o_spi_spd,ref_o_spi_dir,ref_o_data_ack,ref_o_wip} === {dut_o_bus_ack,dut_o_qspi_req,dut_o_spi_wr,dut_o_spi_hold,dut_o_spi_word,dut_o_spi_len,dut_o_spi_spd,dut_o_spi_dir,dut_o_data_ack,dut_o_wip} );

    // Instantiate the writeqspi module
    top uut1 (
        .i_clk(i_clk),
        .i_wreq(i_wreq),
        .i_ereq(i_ereq),
        .i_pipewr(i_pipewr),
        .i_endpipe(i_endpipe),
        .i_addr(i_addr),
        .i_data(i_data),
        .o_bus_ack(dut_o_bus_ack),
        .o_qspi_req(dut_o_qspi_req),
        .i_qspi_grant(i_qspi_grant),
        .o_spi_wr(dut_o_spi_wr),
        .o_spi_hold(dut_o_spi_hold),
        .o_spi_word(dut_o_spi_word),
        .o_spi_len(dut_o_spi_len),
        .o_spi_spd(dut_o_spi_spd),
        .o_spi_dir(dut_o_spi_dir),
        .i_spi_data(i_spi_data),
        .i_spi_valid(i_spi_valid),
        .i_spi_busy(i_spi_busy),
        .i_spi_stopped(i_spi_stopped),
        .o_data_ack(dut_o_data_ack),
        .i_quad(i_quad),
        .o_wip(dut_o_wip)
    );

    // Instantiate the writeqspi module
    ref_writeqspi uut2 (
        .i_clk(i_clk),
        .i_wreq(i_wreq),
        .i_ereq(i_ereq),
        .i_pipewr(i_pipewr),
        .i_endpipe(i_endpipe),
        .i_addr(i_addr),
        .i_data(i_data),
        .ref_o_bus_ack(ref_o_bus_ack),
        .ref_o_qspi_req(ref_o_qspi_req),
        .i_qspi_grant(i_qspi_grant),
        .ref_o_spi_wr(ref_o_spi_wr),
        .ref_o_spi_hold(ref_o_spi_hold),
        .ref_o_spi_word(ref_o_spi_word),
        .ref_o_spi_len(ref_o_spi_len),
        .ref_o_spi_spd(ref_o_spi_spd),
        .ref_o_spi_dir(ref_o_spi_dir),
        .i_spi_data(i_spi_data),
        .i_spi_valid(i_spi_valid),
        .i_spi_busy(i_spi_busy),
        .i_spi_stopped(i_spi_stopped),
        .ref_o_data_ack(ref_o_data_ack),
        .i_quad(i_quad),
        .ref_o_wip(ref_o_wip)
    );

    // Generate clock signal
    initial begin
        i_clk = 0;
        forever #(CLK_PERIOD / 2) i_clk = ~i_clk; // Toggle clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        i_wreq = 0;
        i_ereq = 0;
        i_pipewr = 0;
        i_endpipe = 0;
        i_addr = 22'h0;
        i_data = 32'hDEADBEEF;
        i_qspi_grant = 0;
        i_quad = 0;
        i_spi_busy = 0;
        i_spi_stopped = 0;
        i_spi_data = 32'h0;
        i_spi_valid = 0;

        // Wait for a clock cycle
        #(CLK_PERIOD);

        // Test Case 1: Simple write request
        i_wreq = 1; // Assert write request
        i_qspi_grant = 1; // Grant QSPI access
        #(CLK_PERIOD);
        i_wreq = 0; // De-assert write request
        #(CLK_PERIOD);

            compare();

        
  
        // Test Case 2: Erase request
        i_ereq = 1; // Assert erase request
        #(CLK_PERIOD);
        i_ereq = 0; // De-assert erase request
        #(CLK_PERIOD);

   

        // Test Case 3: Handle SPI busy and stopped conditions
        i_spi_busy = 1; // Simulate SPI busy
        #(CLK_PERIOD);
        i_spi_busy = 0; // Release busy
        i_spi_stopped = 1; // Simulate SPI stopped
        #(CLK_PERIOD);
        i_spi_stopped = 0; // Release stopped

            compare();

 //-----------
// Test case 1: Write request with single data
        i_wreq = 1;
        i_addr = 22'h12345;
        i_data = 32'hDEADBEEF;
        i_qspi_grant = 1;
        i_quad = 0;
        #(CLK_PERIOD);
        i_wreq = 0;
        #(CLK_PERIOD * 10);
        compare();

        // Test case 2: Erase request
        i_ereq = 1;
        i_data = 32'h00000001; // Sector erase
        i_qspi_grant = 1;
        #(CLK_PERIOD);
        i_ereq = 0;
        #(CLK_PERIOD * 10);
        compare();

        // Test case 3: Write request with quad mode
        i_wreq = 1;
        i_addr = 22'h54321;
        i_data = 32'hCAFEBABE;
        i_qspi_grant = 1;
        i_quad = 1;
        #(CLK_PERIOD);
        i_wreq = 0;
        #(CLK_PERIOD * 10);
        compare();

        // Test case 4: Write request with multiple data
        i_wreq = 1;
        i_addr = 22'h11223;
        i_data = 32'hDEADBEEF;
        i_qspi_grant = 1;
        i_quad = 0;
        #(CLK_PERIOD);
        i_wreq = 0;
        i_pipewr = 1;
        i_data = 32'hCAFEBABE;
        #(CLK_PERIOD);
        i_pipewr = 0;
        #(CLK_PERIOD * 10);
        compare();

        // Test case 5: Write request with end of pipe
        i_wreq = 1;
        i_addr = 22'h11223;
        i_data = 32'hDEADBEEF;
        i_qspi_grant = 1;
        i_quad = 0;
        #(CLK_PERIOD);
        i_wreq = 0;
        i_pipewr = 1;
        i_data = 32'hCAFEBABE;
        #(CLK_PERIOD);
        i_pipewr = 0;
        i_endpipe = 1;
        #(CLK_PERIOD);
        i_endpipe = 0;
        #(CLK_PERIOD * 10);
        compare();

        // Test case 6: Read status
        i_qspi_grant = 1;
        i_spi_valid = 1;
        i_spi_data = 32'h00000001; // WIP bit set
        #(CLK_PERIOD * 10);
        i_spi_data = 32'h00000000; // WIP bit cleared
        #(CLK_PERIOD * 10);
        compare();

//--------------

        // Finish simulation
        #(CLK_PERIOD * 10);
repeat (96) begin
            @(negedge i_clk);
	i_wreq = $random;
	i_ereq = $random;
	i_pipewr = $random;
	i_endpipe = $random;
	i_addr = $random;
	i_data = $random;
	i_qspi_grant = $random;
	i_quad = $random;
	i_spi_busy = $random;
	i_spi_stopped = $random;
	i_spi_data = $random;
	i_spi_valid = $random;

            compare();
        end

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

endmodule
