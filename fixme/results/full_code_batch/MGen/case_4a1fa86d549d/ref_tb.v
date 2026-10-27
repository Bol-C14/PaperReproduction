`timescale 1ns / 1ps

module tb;
parameter ISIZ = 20;
parameter DSIZ = 12;
parameter WSIZ = 16;
// Inputs
    reg clk_i            ;
    reg rst_i            ;
    reg [1:0] int_i      ;
    reg [7:6] inte_i     ;
    reg [15:0] iwb_dat_i ;
    reg iwb_ack_i        ;
    reg [7:0] dwb_dat_i  ;
    reg dwb_ack_i        ;

    // Outputs
    wire wb_clk_o             ;
    wire wb_rst_o             ;
    wire [ISIZ-1:0] iwb_adr_o ;
    wire [15:0] iwb_dat_o     ;
    wire iwb_stb_o            ;
    wire iwb_we_o             ;
    wire [1:0] iwb_sel_o      ;
    wire [DSIZ-1:0] dwb_adr_o ;
    wire [7:0] dwb_dat_o      ;
    wire dwb_stb_o            ;
    wire dwb_we_o             ;

	wire wb_clk_o_ref             ;
	wire wb_rst_o_ref             ;
	wire [ISIZ-1:0] iwb_adr_o_ref ;
	wire [15:0] iwb_dat_o_ref     ;
	wire iwb_stb_o_ref            ;
	wire iwb_we_o_ref             ;
	wire [1:0] iwb_sel_o_ref      ;
	wire [DSIZ-1:0] dwb_adr_o_ref ;
	wire [7:0] dwb_dat_o_ref      ;
	wire dwb_stb_o_ref            ;
	wire dwb_we_o_ref             ;

    integer total_tests  = 0;
	integer failed_tests = 0;

    wire match;
	reg [127:0] ref_out;
	reg [127:0] dut_out;

	assign ref_out = {
		wb_clk_o_ref ,
		wb_rst_o_ref ,
		iwb_adr_o_ref,
		iwb_dat_o_ref,
		iwb_stb_o_ref,
		iwb_we_o_ref ,
		iwb_sel_o_ref,
		dwb_adr_o_ref,
		dwb_dat_o_ref,
		dwb_stb_o_ref,
        dwb_we_o_ref };

	assign dut_out = {
		wb_clk_o ,
		wb_rst_o ,
		iwb_adr_o,
		iwb_dat_o,
		iwb_stb_o,
		iwb_we_o ,
		iwb_sel_o,
		dwb_adr_o,
		dwb_dat_o,
		dwb_stb_o,
        dwb_we_o };

	assign match = (ref_out === ref_out^dut_out^ref_out);

    // Instantiate the module under test
    top #(
		.ISIZ(ISIZ),
		.DSIZ(DSIZ),
		.WSIZ(WSIZ)
	)
	dut (
        .clk_i     ( clk_i     ) ,
        .rst_i     ( rst_i     ) ,
        .int_i     ( int_i     ) ,
        .inte_i    ( inte_i    ) ,
        .wb_clk_o  ( wb_clk_o  ) ,
        .wb_rst_o  ( wb_rst_o  ) ,
        .iwb_adr_o ( iwb_adr_o ) ,
        .iwb_dat_o ( iwb_dat_o ) ,
        .iwb_stb_o ( iwb_stb_o ) ,
        .iwb_we_o  ( iwb_we_o  ) ,
        .iwb_sel_o ( iwb_sel_o ) ,
        .dwb_adr_o ( dwb_adr_o ) ,
        .dwb_dat_o ( dwb_dat_o ) ,
        .dwb_stb_o ( dwb_stb_o ) ,
        .dwb_we_o  ( dwb_we_o  ) ,
        .iwb_dat_i ( iwb_dat_i ) ,
        .iwb_ack_i ( iwb_ack_i ) ,
        .dwb_dat_i ( dwb_dat_i ) ,
        .dwb_ack_i ( dwb_ack_i )
    );


ae18_core_ref #(
		.ISIZ(ISIZ),
		.DSIZ(DSIZ),
		.WSIZ(WSIZ)
	)
	ref_uut (
        .iwb_dat_i     ( iwb_dat_i     ) ,
        .iwb_ack_i     ( iwb_ack_i     ) ,
        .dwb_dat_i     ( dwb_dat_i     ) ,
        .dwb_ack_i     ( dwb_ack_i     ) ,
        .int_i         ( int_i         ) ,
        .inte_i        ( inte_i        ) ,
        .clk_i         ( clk_i         ) ,
        .rst_i         ( rst_i         ) ,
        .wb_clk_o_ref  ( wb_clk_o_ref  ) ,
        .wb_rst_o_ref  ( wb_rst_o_ref  ) ,
        .iwb_adr_o_ref ( iwb_adr_o_ref ) ,
        .iwb_dat_o_ref ( iwb_dat_o_ref ) ,
        .iwb_stb_o_ref ( iwb_stb_o_ref ) ,
        .iwb_we_o_ref  ( iwb_we_o_ref  ) ,
        .iwb_sel_o_ref ( iwb_sel_o_ref ) ,
        .dwb_adr_o_ref ( dwb_adr_o_ref ) ,
        .dwb_dat_o_ref ( dwb_dat_o_ref ) ,
        .dwb_stb_o_ref ( dwb_stb_o_ref ) ,
        .dwb_we_o_ref  ( dwb_we_o_ref  )
    );


    // Clock generation
    initial begin
        clk_i = 0;
        forever #5 clk_i = ~clk_i;
    end

    // Test case execution
    initial begin

        rst_i     = 1;
		iwb_dat_i = 0;
		iwb_ack_i = 0;
        int_i     = 0;
        inte_i    = 0;
		dwb_dat_i = 0;
        dwb_ack_i = 0;
		#100 ;


		rst_i = 0;
		iwb_dat_i = 'd1;
		iwb_ack_i = 'd1;
        int_i     = 'd1;
        inte_i    = 'd1;
		dwb_dat_i = 'd1;
        dwb_ack_i = 'd1;
		#10;
		compare();
		#10;

		repeat(100) begin
		rst_i = 1;
		#20;
		rst_i = 0;
		#20;
		iwb_dat_i = $random;
		iwb_ack_i = $random;
        int_i     = $random;
        inte_i    = $random;
		dwb_dat_i = $random;
        dwb_ack_i = $random;
		#10;
		compare();
		#10;
		end

        int_i = 2'b01;
        inte_i = 2'b11;
        #100;
		compare();
		#10;

        int_i = 2'b00;
        inte_i = 2'b00;
        #100;
		compare();
		#10;

   		 iwb_dat_i = 16'h0001;
   		 iwb_ack_i = 1;
   		 #10;
   		 iwb_ack_i = 0;
   		 #50;
   		 iwb_dat_i = 16'h0002;
   		 iwb_ack_i = 1;
   		 #10;
   		 iwb_ack_i = 0;
   		 #100;


        #1000;
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $finish;
    end

    task compare;
        total_tests = total_tests + 1;
        if (match)                               
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
            end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            failed_tests = failed_tests + 1; 
		end
    
	  endtask




initial begin
      $fsdbDumpfile("sim.fsdb");
      $fsdbDumpvars();
	  $fsdbDumpMDA();
end
endmodule
