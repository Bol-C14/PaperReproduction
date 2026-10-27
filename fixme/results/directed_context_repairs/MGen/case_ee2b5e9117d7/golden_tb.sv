 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period for wb_clk_i

    // Inputs
    reg wb_clk_i;
    reg wb_rst_i;
    reg [31:0] m1_wb_adr_i, m1_wb_dat_i;
    reg [3:0] m1_wb_sel_i;
    reg m1_wb_cyc_i, m1_wb_stb_i, m1_wb_we_i;
    reg [31:0] m2_wb_adr_i, m2_wb_dat_i;
    reg [3:0] m2_wb_sel_i;
    reg m2_wb_cyc_i, m2_wb_stb_i, m2_wb_we_i;
    reg [31:0] s1_wb_dat_i, s2_wb_dat_i;
    reg s1_wb_ack_i, s1_wb_err_i;
    reg s2_wb_ack_i, s2_wb_err_i;

    // ref Outputs
    wire [31:0] ref_m1_wb_dat_o;
    wire ref_m1_wb_ack_o, ref_m1_wb_err_o;
    wire [31:0] ref_m2_wb_dat_o;
    wire ref_m2_wb_ack_o, ref_m2_wb_err_o;
    wire [31:0] ref_s1_wb_adr_o, ref_s1_wb_dat_o;
    wire [3:0] ref_s1_wb_sel_o;
    wire ref_s1_wb_we_o, ref_s1_wb_cyc_o, ref_s1_wb_stb_o;
    wire [31:0] ref_s2_wb_adr_o, ref_s2_wb_dat_o;
    wire [3:0] ref_s2_wb_sel_o;
    wire ref_s2_wb_we_o, ref_s2_wb_cyc_o, ref_s2_wb_stb_o;

    // Outputs
    wire [31:0] m1_wb_dat_o;
    wire m1_wb_ack_o, m1_wb_err_o;
    wire [31:0] m2_wb_dat_o;
    wire m2_wb_ack_o, m2_wb_err_o;
    wire [31:0] s1_wb_adr_o, s1_wb_dat_o;
    wire [3:0] s1_wb_sel_o;
    wire s1_wb_we_o, s1_wb_cyc_o, s1_wb_stb_o;
    wire [31:0] s2_wb_adr_o, s2_wb_dat_o;
    wire [3:0] s2_wb_sel_o;
    wire s2_wb_we_o, s2_wb_cyc_o, s2_wb_stb_o;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_m1_wb_dat_o,ref_m1_wb_ack_o, ref_m1_wb_err_o,ref_m2_wb_dat_o,ref_m2_wb_ack_o, ref_m2_wb_err_o,ref_s1_wb_adr_o, ref_s1_wb_dat_o,ref_s1_wb_sel_o,ref_s1_wb_we_o, ref_s1_wb_cyc_o, ref_s1_wb_stb_o,ref_s2_wb_adr_o, ref_s2_wb_dat_o,ref_s2_wb_sel_o,ref_s2_wb_we_o, ref_s2_wb_cyc_o, ref_s2_wb_stb_o} === {m1_wb_dat_o,m1_wb_ack_o, m1_wb_err_o,m2_wb_dat_o,m2_wb_ack_o, m2_wb_err_o,s1_wb_adr_o,s1_wb_dat_o,s1_wb_sel_o,s1_wb_we_o, s1_wb_cyc_o, s1_wb_stb_o,s2_wb_adr_o, s2_wb_dat_o,s2_wb_sel_o,s2_wb_we_o,ref_s2_wb_cyc_o, s2_wb_stb_o} );

    // Instantiate the eth_cop module
    ref_eth_cop rf(
        .wb_clk_i(wb_clk_i),
        .wb_rst_i(wb_rst_i),
        .m1_wb_adr_i(m1_wb_adr_i), .m1_wb_dat_i(m1_wb_dat_i),
        .m1_wb_sel_i(m1_wb_sel_i), .m1_wb_cyc_i(m1_wb_cyc_i),
        .m1_wb_stb_i(m1_wb_stb_i), .m1_wb_we_i(m1_wb_we_i),
        .ref_m1_wb_dat_o(ref_m1_wb_dat_o), .ref_m1_wb_ack_o(ref_m1_wb_ack_o),
        .ref_m1_wb_err_o(ref_m1_wb_err_o),
        .m2_wb_adr_i(m2_wb_adr_i), .m2_wb_dat_i(m2_wb_dat_i),
        .m2_wb_sel_i(m2_wb_sel_i), .m2_wb_cyc_i(m2_wb_cyc_i),
        .m2_wb_stb_i(m2_wb_stb_i), .m2_wb_we_i(m2_wb_we_i),
        .ref_m2_wb_dat_o(ref_m2_wb_dat_o), .ref_m2_wb_ack_o(ref_m2_wb_ack_o),
        .ref_m2_wb_err_o(ref_m2_wb_err_o),
        .ref_s1_wb_adr_o(ref_s1_wb_adr_o), .ref_s1_wb_dat_o(ref_s1_wb_dat_o),
        .ref_s1_wb_sel_o(ref_s1_wb_sel_o), .ref_s1_wb_we_o(ref_s1_wb_we_o),
        .ref_s1_wb_cyc_o(ref_s1_wb_cyc_o), .ref_s1_wb_stb_o(ref_s1_wb_stb_o),
        .s1_wb_ack_i(s1_wb_ack_i), .s1_wb_err_i(s1_wb_err_i),
        .s1_wb_dat_i(s1_wb_dat_i),
        .ref_s2_wb_adr_o(ref_s2_wb_adr_o), .ref_s2_wb_dat_o(ref_s2_wb_dat_o),
        .ref_s2_wb_sel_o(ref_s2_wb_sel_o), .ref_s2_wb_we_o(ref_s2_wb_we_o),
        .ref_s2_wb_cyc_o(ref_s2_wb_cyc_o), .ref_s2_wb_stb_o(ref_s2_wb_stb_o),
        .s2_wb_ack_i(s2_wb_ack_i), .s2_wb_err_i(s2_wb_err_i),
        .s2_wb_dat_i(s2_wb_dat_i)
    );

    // Instantiate the eth_cop module
   top dut (
        .wb_clk_i(wb_clk_i),
        .wb_rst_i(wb_rst_i),
        .m1_wb_adr_i(m1_wb_adr_i), .m1_wb_dat_i(m1_wb_dat_i),
        .m1_wb_sel_i(m1_wb_sel_i), .m1_wb_cyc_i(m1_wb_cyc_i),
        .m1_wb_stb_i(m1_wb_stb_i), .m1_wb_we_i(m1_wb_we_i),
        .m1_wb_dat_o(m1_wb_dat_o), .m1_wb_ack_o(m1_wb_ack_o),
        .m1_wb_err_o(m1_wb_err_o),
        .m2_wb_adr_i(m2_wb_adr_i), .m2_wb_dat_i(m2_wb_dat_i),
        .m2_wb_sel_i(m2_wb_sel_i), .m2_wb_cyc_i(m2_wb_cyc_i),
        .m2_wb_stb_i(m2_wb_stb_i), .m2_wb_we_i(m2_wb_we_i),
        .m2_wb_dat_o(m2_wb_dat_o), .m2_wb_ack_o(m2_wb_ack_o),
        .m2_wb_err_o(m2_wb_err_o),
        .s1_wb_adr_o(s1_wb_adr_o), .s1_wb_dat_o(s1_wb_dat_o),
        .s1_wb_sel_o(s1_wb_sel_o), .s1_wb_we_o(s1_wb_we_o),
        .s1_wb_cyc_o(s1_wb_cyc_o), .s1_wb_stb_o(s1_wb_stb_o),
        .s1_wb_ack_i(s1_wb_ack_i), .s1_wb_err_i(s1_wb_err_i),
        .s1_wb_dat_i(s1_wb_dat_i),
        .s2_wb_adr_o(s2_wb_adr_o), .s2_wb_dat_o(s2_wb_dat_o),
        .s2_wb_sel_o(s2_wb_sel_o), .s2_wb_we_o(s2_wb_we_o),
        .s2_wb_cyc_o(s2_wb_cyc_o), .s2_wb_stb_o(s2_wb_stb_o),
        .s2_wb_ack_i(s2_wb_ack_i), .s2_wb_err_i(s2_wb_err_i),
        .s2_wb_dat_i(s2_wb_dat_i)
    );

    // Generate clock signal
    initial begin
        wb_clk_i = 0;
        forever #(CLK_PERIOD / 2) wb_clk_i = ~wb_clk_i; // Toggle clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        wb_rst_i = 1;
        m1_wb_adr_i = 0; m1_wb_dat_i = 0; m1_wb_sel_i = 0;
        m1_wb_cyc_i = 0; m1_wb_stb_i = 0; m1_wb_we_i = 0;
        m2_wb_adr_i = 0; m2_wb_dat_i = 0; m2_wb_sel_i = 0;
        m2_wb_cyc_i = 0; m2_wb_stb_i = 0; m2_wb_we_i = 0;
        s1_wb_dat_i = 0; s2_wb_dat_i = 0;
        s1_wb_ack_i = 0; s1_wb_err_i = 0;
        s2_wb_ack_i = 0; s2_wb_err_i = 0;

        // Apply reset
        #(CLK_PERIOD);
        wb_rst_i = 0; // De-assert reset
        #(CLK_PERIOD);

        // Test Case 1: Simple Write to s1
        m1_wb_adr_i = 32'hd0000000; // Address for s1
        m1_wb_dat_i = 32'hA5A5A5A5; // Data to write
        m1_wb_sel_i = 4'b1111; // Select all bytes
        m1_wb_cyc_i = 1; // Assert cycle
        m1_wb_stb_i = 1; // Assert strobe
        m1_wb_we_i = 1; // Write enable
        #(CLK_PERIOD);
        m1_wb_cyc_i = 0; // End cycle
        m1_wb_stb_i = 0; // End strobe
        #(CLK_PERIOD);
compare();

        // Test Case 2: Read from s1
        s1_wb_ack_i = 1; // Simulate acknowledgment from slave
        s1_wb_dat_i = 32'hA5A5A5A5; // Simulated data from slave
        m1_wb_adr_i = 32'hd0000000; // Address for s1
        m1_wb_cyc_i = 1; // Assert cycle
        m1_wb_stb_i = 1; // Assert strobe
        m1_wb_we_i = 0; // Read
        #(CLK_PERIOD);
        m1_wb_cyc_i = 0; // End cycle
        m1_wb_stb_i = 0; // End strobe
        #(CLK_PERIOD);
compare();

        // Test Case 3: Write to s2
        m2_wb_adr_i = 32'h2000; // Address for s2
        m2_wb_dat_i = 32'h5A5A5A5A; // Data to write
        m2_wb_sel_i = 4'b1111; // Select all bytes
        m2_wb_cyc_i = 1; // Assert cycle
        m2_wb_stb_i = 1; // Assert strobe
        m2_wb_we_i = 1; // Write enable
        #(CLK_PERIOD);
        m2_wb_cyc_i = 0; // End cycle
        m2_wb_stb_i = 0; // End strobe
        #(CLK_PERIOD);

compare();

        // Test Case 4: Read from s2
        s2_wb_ack_i = 1; // Simulate acknowledgment from slave
        s2_wb_dat_i = 32'h5A5A5A5A; // Simulated data from slave
        m2_wb_adr_i = 32'h2000; // Address for s2
        m2_wb_cyc_i = 1; // Assert cycle
        m2_wb_stb_i = 1; // Assert strobe
        m2_wb_we_i = 0; // Read
        #(CLK_PERIOD);
        m2_wb_cyc_i = 0; // End cycle
        m2_wb_stb_i = 0; // End strobe
        #(CLK_PERIOD);
compare();
 

repeat (1000) begin
            @(negedge wb_clk_i);
	m1_wb_adr_i = $random;
	m1_wb_dat_i = $random;
	m1_wb_sel_i = $random;
	m1_wb_cyc_i = $random;
	m1_wb_stb_i = $random;
	m1_wb_we_i = $random;
	m2_wb_adr_i = $random;
	m2_wb_dat_i = $random;
	m2_wb_sel_i = $random;
	m2_wb_cyc_i = $random;
	m2_wb_stb_i = $random;
	m2_wb_we_i = $random;
	s1_wb_dat_i = $random;
	s2_wb_dat_i = $random;
	s1_wb_ack_i = $random;
	s1_wb_err_i = $random;
	s2_wb_ack_i = $random;
	s2_wb_err_i = $random;
compare();
end
 	$display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        // Finish simulation
        #(CLK_PERIOD * 10);
        $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
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
