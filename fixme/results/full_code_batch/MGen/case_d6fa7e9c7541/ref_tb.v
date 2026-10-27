`timescale 1ns / 1ps

module tb;

// Parameters
parameter ARST_LVL = 1'b0;      // asynchronous reset level
parameter INIT_ENA = 1'b1;      // COP Enabled after reset
parameter SERV_WD_0 = 16'h5555; // First Service Word
parameter SERV_WD_1 = 16'haaaa; // Second Service Word
parameter COUNT_SIZE = 16;      // Main counter size
parameter SINGLE_CYCLE = 1'b0;  // No bus wait state added
parameter DWIDTH = 16;          // Data bus width

// Inputs
reg wb_clk_i;
reg wb_rst_i;
reg arst_i;
reg por_reset_i;
reg startup_osc_i;
reg stop_mode_i;
reg wait_mode_i;
reg debug_mode_i;
reg scantestmode;
reg [2:0] wb_adr_i;
reg [DWIDTH-1:0] wb_dat_i;
reg wb_we_i;
reg wb_stb_i;
reg wb_cyc_i;
reg [1:0] wb_sel_i;

// Outputs or inout
wire [DWIDTH-1:0] dut_wb_dat_o, ref_wb_dat_o;
wire dut_wb_ack_o, ref_wb_ack_o;
wire dut_cop_rst_o, ref_cop_rst_o;
wire dut_cop_irq_o, ref_cop_irq_o;

    wire       match;
    integer    total_tests = 0;
    integer    failed_tests = 0;

    assign match = ({ref_wb_dat_o, ref_wb_ack_o, ref_cop_rst_o, ref_cop_irq_o} === {dut_wb_dat_o, dut_wb_ack_o, dut_cop_rst_o, dut_cop_irq_o});

// Instantiate the Unit Under Test (UUT)
ref_cop_top #(
    .ARST_LVL(ARST_LVL),
    .INIT_ENA(INIT_ENA),
    .SERV_WD_0(SERV_WD_0),
    .SERV_WD_1(SERV_WD_1),
    .COUNT_SIZE(COUNT_SIZE),
    .SINGLE_CYCLE(SINGLE_CYCLE),
    .DWIDTH(DWIDTH)
) ref_model (
    .wb_clk_i(wb_clk_i),
    .wb_rst_i(wb_rst_i),
    .arst_i(arst_i),
    .por_reset_i(por_reset_i),
    .startup_osc_i(startup_osc_i),
    .stop_mode_i(stop_mode_i),
    .wait_mode_i(wait_mode_i),
    .debug_mode_i(debug_mode_i),
    .scantestmode(scantestmode),
    .wb_adr_i(wb_adr_i),
    .wb_dat_i(wb_dat_i),
    .wb_we_i(wb_we_i),
    .wb_stb_i(wb_stb_i),
    .wb_cyc_i(wb_cyc_i),
    .wb_sel_i(wb_sel_i),
    .ref_wb_dat_o(ref_wb_dat_o),
    .ref_wb_ack_o(ref_wb_ack_o),
    .ref_cop_rst_o(ref_cop_rst_o),
    .ref_cop_irq_o(ref_cop_irq_o)
);

top #(
    .ARST_LVL(ARST_LVL),
    .INIT_ENA(INIT_ENA),
    .SERV_WD_0(SERV_WD_0),
    .SERV_WD_1(SERV_WD_1),
    .COUNT_SIZE(COUNT_SIZE),
    .SINGLE_CYCLE(SINGLE_CYCLE),
    .DWIDTH(DWIDTH)
) dut (
    .wb_clk_i(wb_clk_i),
    .wb_rst_i(wb_rst_i),
    .arst_i(arst_i),
    .por_reset_i(por_reset_i),
    .startup_osc_i(startup_osc_i),
    .stop_mode_i(stop_mode_i),
    .wait_mode_i(wait_mode_i),
    .debug_mode_i(debug_mode_i),
    .scantestmode(scantestmode),
    .wb_adr_i(wb_adr_i),
    .wb_dat_i(wb_dat_i),
    .wb_we_i(wb_we_i),
    .wb_stb_i(wb_stb_i),
    .wb_cyc_i(wb_cyc_i),
    .wb_sel_i(wb_sel_i),
    .wb_dat_o(dut_wb_dat_o),
    .wb_ack_o(dut_wb_ack_o),
    .cop_rst_o(dut_cop_rst_o),
    .cop_irq_o(dut_cop_irq_o)
);

// clk toggle generate
always #5 wb_clk_i = ~wb_clk_i;

initial begin
    // Initialize Inputs
    wb_clk_i = 0;
    wb_rst_i = 0;
    arst_i = 0;
    por_reset_i = 1;
    startup_osc_i = 0;
    stop_mode_i = 0;
    wait_mode_i = 0;
    debug_mode_i = 0;
    scantestmode = 0;
    wb_adr_i = 0;
    wb_dat_i = 0;
    wb_we_i = 0;
    wb_stb_i = 0;
    wb_cyc_i = 0;
    wb_sel_i = 0;

    // Initial stimulus
    #100;
    arst_i = 1;
    por_reset_i = 0;
    wb_rst_i = 1;
    wb_dat_i = {DWIDTH{1'b1}};
    #100;
    wb_rst_i = 0;
    arst_i = 1;
    por_reset_i = 1;
    #100;

    // Wait 100 ns for global reset to finish
    #100;


   // Test Case 1: System Health Monitoring via Timeout
    // Configure the COP timeout value
    wb_adr_i = 3'b000;
    wb_dat_i = 16'h0001; // Small timeout value for test
    wb_we_i = 1;
    wb_cyc_i = 1;
    wb_stb_i = 1;
    #10;
    wb_cyc_i = 0;
    wb_stb_i = 0;
    wb_we_i = 0;
    #10;
       compare();



    // Test Case 2: Interrupt Generation on Threshold
    wb_adr_i = 3'b001;
    wb_dat_i = 16'h0002; // Set interrupt threshold
    wb_we_i = 1;
    wb_cyc_i = 1;
    wb_stb_i = 1;
    #10;
    wb_cyc_i = 0;
    wb_stb_i = 0;
    wb_we_i = 0;
    #10;
       compare();

    // Test Case 3: COP Disable and Re-enable
    wb_adr_i = 3'b010;
    wb_dat_i = 16'h0000; // Disable COP
    wb_we_i = 1;
    wb_cyc_i = 1;
    wb_stb_i = 1;
    #10;
    wb_cyc_i = 0;
    wb_stb_i = 0;
    wb_we_i = 0;
    #10;
       compare();

    wb_adr_i = 3'b010;
    wb_dat_i = 16'h0001; // Re-enable COP
    wb_we_i = 1;
    wb_cyc_i = 1;
    wb_stb_i = 1;
    #10;
    wb_cyc_i = 0;
    wb_stb_i = 0;
    wb_we_i = 0;
    #10;
       compare();



    // Add stimulus here
    for (integer i = 0; i < 988; i++) begin
    startup_osc_i = $random;
    stop_mode_i = $random;
    wait_mode_i = $random;
    debug_mode_i = $random;
    scantestmode = $random;
        wb_cyc_i = $random;
        wb_stb_i = $random;
        wb_we_i = $random;
        wb_adr_i = $random;
        wb_dat_i = $random;
        wb_sel_i = $random;
        #20;
       compare();
    end


    // Toggle reset to simulate a reset event

    for (integer i = 0; i < 8; i++) begin
         {arst_i, por_reset_i, wb_rst_i} = i;
            #100;
       compare();
    end

    arst_i = 0;
    por_reset_i = 0;
    wb_rst_i = 0;
     #100;

        $display("\033[1;34mAll tests completed.\033[0m");
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
