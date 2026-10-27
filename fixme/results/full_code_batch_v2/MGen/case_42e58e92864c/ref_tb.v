`timescale 1ns/1ps
 module tb;

  // Inputs
  reg i_clk;
  reg i_select;
  reg [31:0] i_write_data;
  reg i_write_enable;
  reg [3:0] i_byte_enable;
  reg i_data_access;
  reg i_exclusive;
  reg [31:0] i_address;
  reg i_cache_req;
  reg [31:0] i_wb_dat;
  reg i_wb_ack;
  reg i_wb_err;

  // Outputs
  wire o_stall_ref, o_stall_dut;
  wire [31:0] o_wb_adr_ref, o_wb_adr_dut;
  wire [3:0] o_wb_sel_ref, o_wb_sel_dut;
  wire o_wb_we_ref, o_wb_we_dut;
  wire [31:0] o_wb_dat_ref, o_wb_dat_dut;
  wire o_wb_cyc_ref, o_wb_cyc_dut;
  wire o_wb_stb_ref, o_wb_stb_dut;


  wire match;

  integer total_tests = 0;
	integer failed_tests = 0;

  assign match = ({o_stall_ref, o_wb_adr_ref, o_wb_sel_ref, o_wb_we_ref, o_wb_dat_ref, o_wb_cyc_ref, o_wb_stb_ref} === ({o_stall_dut, o_wb_adr_dut, o_wb_sel_dut, o_wb_we_dut, o_wb_dat_dut, o_wb_cyc_dut, o_wb_stb_dut} ^ {o_stall_ref, o_wb_adr_ref, o_wb_sel_ref, o_wb_we_ref, o_wb_dat_ref, o_wb_cyc_ref, o_wb_stb_ref} ^ {o_stall_ref, o_wb_adr_ref, o_wb_sel_ref, o_wb_we_ref, o_wb_dat_ref, o_wb_cyc_ref, o_wb_stb_ref}));

  // Instantiate the Unit Under Test (UUT)
  a23_wishbone_ref ref_model (
    .i_clk(i_clk),
    .i_select(i_select),
    .i_write_data(i_write_data),
    .i_write_enable(i_write_enable),
    .i_byte_enable(i_byte_enable),
    .i_data_access(i_data_access),
    .i_exclusive(i_exclusive),
    .i_address(i_address),
    .o_stall_ref(o_stall_ref),
    .i_cache_req(i_cache_req),
    .o_wb_adr_ref(o_wb_adr_ref),
    .o_wb_sel_ref(o_wb_sel_ref),
    .o_wb_we_ref(o_wb_we_ref),
    .i_wb_dat(i_wb_dat),
    .o_wb_dat_ref(o_wb_dat_ref),
    .o_wb_cyc_ref(o_wb_cyc_ref),
    .o_wb_stb_ref(o_wb_stb_ref),
    .i_wb_ack(i_wb_ack),
    .i_wb_err(i_wb_err)
  );

  top dut (
    .i_clk(i_clk),
    .i_select(i_select),
    .i_write_data(i_write_data),
    .i_write_enable(i_write_enable),
    .i_byte_enable(i_byte_enable),
    .i_data_access(i_data_access),
    .i_exclusive(i_exclusive),
    .i_address(i_address),
    .o_stall(o_stall_dut),
    .i_cache_req(i_cache_req),
    .o_wb_adr(o_wb_adr_dut),
    .o_wb_sel(o_wb_sel_dut),
    .o_wb_we(o_wb_we_dut),
    .i_wb_dat(i_wb_dat),
    .o_wb_dat(o_wb_dat_dut),
    .o_wb_cyc(o_wb_cyc_dut),
    .o_wb_stb(o_wb_stb_dut),
    .i_wb_ack(i_wb_ack),
    .i_wb_err(i_wb_err)
  );

  // Clock generation
  always #5 i_clk = ~i_clk;

  initial begin
    // Initialize Inputs
    i_clk = 0;
    i_select = 0;
    i_write_data = 0;
    i_write_enable = 0;
    i_byte_enable = 0;
    i_data_access = 0;
    i_exclusive = 0;
    i_address = 0;
    i_cache_req = 0;
    i_wb_dat = 0;
    i_wb_ack = 0;
    i_wb_err = 0;

    // Wait for global reset
    #10;

    // Test Case 1: Write request
    i_select = 1;
    i_write_enable = 1;
    i_write_data = 32'hA5A5A5A5;
    i_byte_enable = 4'b1111;
    i_address = 32'hA5A5A5A5;
    #10;
    i_wb_ack = 1;
    #10;
    compare();
    i_wb_ack = 0;
    i_select = 0;
    #10;
    compare();

    // Test Case 2: Read request
    i_select = 1;
    i_write_enable = 0;
    i_address = 32'h5A5A5A5A;
    #10;
    i_wb_ack = 1;
    i_wb_dat = 32'h5A5A5A5A;
    #10;
    compare();
    i_wb_ack = 0;
    i_select = 0;
    #10;
    compare();

    // Test Case 3: Cache write request
    i_cache_req = 1;
    i_write_enable = 1;
    i_write_data = 32'hB5B5B5B5;
    i_byte_enable = 4'b1111;
    i_address = 32'h00000000;
    #10;
    compare();
    i_wb_ack = 1;
    #10;
    compare();
    i_wb_ack = 0;
    i_cache_req = 0;
    #10;
    compare();

    // Test Case 4: Cache read request
    i_cache_req = 1;
    i_write_enable = 0;
    i_address = 32'hFFFFFFFF;
    #10;
    compare();
    i_wb_ack = 1;
    i_wb_dat = 32'hC5C5C5C5;
    compare();
    #10;
    i_wb_ack = 0;
    i_cache_req = 0;
    #10;
    compare();

    repeat (190) begin
      i_select = $random;
      i_write_data = $random;
      i_write_enable = $random;
      i_byte_enable = $random;
      i_data_access = $random;
      i_exclusive = $random;
      i_address = $random;
      i_cache_req = $random;
      i_wb_dat = $random;
      i_wb_ack = $random;
      i_wb_err = $random;
      #10;
      compare();  
    end

    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);


    // Finish simulation
    $finish;
  end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("i_select = %h, i_write_data = %h, i_write_enable = %h, i_byte_enable = %h, i_data_access = %h, i_exclusive = %h, i_address = %h, i_cache_req = %h, i_wb_dat = %h, i_wb_ack = %h, i_wb_err = %h, o_stall_dut = %h, o_wb_adr_dut = %h, o_wb_sel_dut = %h, o_wb_we_dut = %h, o_wb_dat_dut = %h, o_wb_cyc_dut = %h, o_wb_stb_dut = %h, o_stall_ref = %h, o_wb_adr_ref = %h, o_wb_sel_ref = %h, o_wb_we_ref = %h, o_wb_dat_ref = %h, o_wb_cyc_ref = %h, o_wb_stb_ref = %h", i_select, i_write_data, i_write_enable, i_byte_enable, i_data_access, i_exclusive, i_address, i_cache_req, i_wb_dat, i_wb_ack, i_wb_err, o_stall_dut, o_wb_adr_dut, o_wb_sel_dut, o_wb_we_dut, o_wb_dat_dut, o_wb_cyc_dut, o_wb_stb_dut, o_stall_ref, o_wb_adr_ref, o_wb_sel_ref, o_wb_we_ref, o_wb_dat_ref, o_wb_cyc_ref, o_wb_stb_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("i_select = %h, i_write_data = %h, i_write_enable = %h, i_byte_enable = %h, i_data_access = %h, i_exclusive = %h, i_address = %h, i_cache_req = %h, i_wb_dat = %h, i_wb_ack = %h, i_wb_err = %h, o_stall_dut = %h, o_wb_adr_dut = %h, o_wb_sel_dut = %h, o_wb_we_dut = %h, o_wb_dat_dut = %h, o_wb_cyc_dut = %h, o_wb_stb_dut = %h, o_stall_ref = %h, o_wb_adr_ref = %h, o_wb_sel_ref = %h, o_wb_we_ref = %h, o_wb_dat_ref = %h, o_wb_cyc_ref = %h, o_wb_stb_ref = %h", i_select, i_write_data, i_write_enable, i_byte_enable, i_data_access, i_exclusive, i_address, i_cache_req, i_wb_dat, i_wb_ack, i_wb_err, o_stall_dut, o_wb_adr_dut, o_wb_sel_dut, o_wb_we_dut, o_wb_dat_dut, o_wb_cyc_dut, o_wb_stb_dut, o_stall_ref, o_wb_adr_ref, o_wb_sel_ref, o_wb_we_ref, o_wb_dat_ref, o_wb_cyc_ref, o_wb_stb_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end


endmodule

