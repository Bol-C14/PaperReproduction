`timescale 1ns/1ps

module tb;

  // Inputs
  reg i_data_clk;
  reg i_ce;
  reg i_trigger;
  reg [31:0] i_data;
  reg i_wb_clk;
  reg i_wb_cyc;
  reg i_wb_stb;
  reg i_wb_we;
  reg i_wb_addr;
  reg [31:0] i_wb_data;

  // Outputs
  wire o_wb_ack_ref, o_wb_ack_dut;
  wire o_wb_stall_ref, o_wb_stall_dut;
  wire [31:0] o_wb_data_ref, o_wb_data_dut;
  wire o_interrupt_ref, o_interrupt_dut;

    wire match;

    integer total_tests = 0;
	  integer failed_tests = 0;

    assign match = ({o_wb_ack_ref, o_wb_stall_ref, o_wb_data_ref, o_interrupt_ref} === {o_wb_ack_dut, o_wb_stall_dut, o_wb_data_dut, o_interrupt_dut});

  // Instantiate the Unit Under Test (UUT)
  wbscopc_ref ref_model (
    .i_data_clk(i_data_clk),
    .i_ce(i_ce),
    .i_trigger(i_trigger),
    .i_data(i_data[31:0]),
    .i_wb_clk(i_wb_clk),
    .i_wb_cyc(i_wb_cyc),
    .i_wb_stb(i_wb_stb),
    .i_wb_we(i_wb_we),
    .i_wb_addr(i_wb_addr),
    .i_wb_data(i_wb_data),
    .o_wb_ack_ref(o_wb_ack_ref),
    .o_wb_stall_ref(o_wb_stall_ref),
    .o_wb_data_ref(o_wb_data_ref),
    .o_interrupt_ref(o_interrupt_ref)
  );

  top dut (
    .i_data_clk(i_data_clk),
    .i_ce(i_ce),
    .i_trigger(i_trigger),
    .i_data(i_data[31:0]),
    .i_wb_clk(i_wb_clk),
    .i_wb_cyc(i_wb_cyc),
    .i_wb_stb(i_wb_stb),
    .i_wb_we(i_wb_we),
    .i_wb_addr(i_wb_addr),
    .i_wb_data(i_wb_data),
    .o_wb_ack(o_wb_ack_dut),
    .o_wb_stall(o_wb_stall_dut),
    .o_wb_data(o_wb_data_dut),
    .o_interrupt(o_interrupt_dut)
  );

  // Clock generation
  always #5 i_data_clk = ~i_data_clk;
  always #5 i_wb_clk = ~i_wb_clk;


  
  initial begin
    i_data_clk = 0;
    i_ce = 0;
    i_trigger = 0;
    i_data = 0;
    i_wb_clk = 0;
    i_wb_cyc = 0;
    i_wb_stb = 0;
    i_wb_we = 0;
    i_wb_addr = 0;
    i_wb_data = 0;
    #10;

    repeat (200) begin
      i_ce = $random;
      i_trigger = $random;
      i_data = $random;
      i_wb_cyc = $random;
      i_wb_stb = $random;
      i_wb_we = $random;
      i_wb_addr = $random;
      i_wb_data = $random;
      #300000;
      compare();
    end

    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
  end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("i_ce = %h, i_triggeri_ce = %h, i_datai_ce = %h, i_wb_cyci_ce = %h, i_wb_stbi_ce = %h, i_wb_wei_ce = %h, i_wb_addri_ce = %h, i_wb_datai_ce = %h, o_wb_ack_duti_ce = %h, o_wb_stall_duti_ce = %h, o_wb_data_duti_ce = %h, o_interrupt_duti_ce = %h, o_wb_ack_refi_ce = %h, o_wb_stall_refi_ce = %h, o_wb_data_refi_ce = %h, o_interrupt_refi_ce = %h", i_ce, i_trigger, i_data, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, o_wb_ack_dut, o_wb_stall_dut, o_wb_data_dut, o_interrupt_dut, o_wb_ack_ref, o_wb_stall_ref, o_wb_data_ref, o_interrupt_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("i_ce = %h, i_triggeri_ce = %h, i_datai_ce = %h, i_wb_cyci_ce = %h, i_wb_stbi_ce = %h, i_wb_wei_ce = %h, i_wb_addri_ce = %h, i_wb_datai_ce = %h, o_wb_ack_duti_ce = %h, o_wb_stall_duti_ce = %h, o_wb_data_duti_ce = %h, o_interrupt_duti_ce = %h, o_wb_ack_refi_ce = %h, o_wb_stall_refi_ce = %h, o_wb_data_refi_ce = %h, o_interrupt_refi_ce = %h", i_ce, i_trigger, i_data, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, o_wb_ack_dut, o_wb_stall_dut, o_wb_data_dut, o_interrupt_dut, o_wb_ack_ref, o_wb_stall_ref, o_wb_data_ref, o_interrupt_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask


    initial begin
        /* omitted diagnostic FSDB output: $fsdbDumpfile("sim.fsdb"); */
        /* omitted diagnostic FSDB output: $fsdbDumpvars(); */
    end


endmodule
