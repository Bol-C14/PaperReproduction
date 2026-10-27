`timescale 1ns/1ps
 module tb;

  // Parameters
  parameter sdram_depth = 26;
  parameter sdram_columndepth = 9;

  // Inputs
  reg sys_clk;
  reg sdram_rst;
  reg [2:0] tim_rp;
  reg [2:0] tim_rcd;
  reg [10:0] tim_refi;
  reg [3:0] tim_rfc;
  reg stb;
  reg we;
  reg [sdram_depth-3-1:0] address;
  reg read_safe;
  reg write_safe;
  reg [3:0] precharge_safe;

  // Outputs
  wire ref_ack,ack;
  wire ref_read,read;
  wire ref_write,write;
  wire [3:0] ref_concerned_bank,concerned_bank;
  wire ref_sdram_cs_n,sdram_cs_n;
  wire ref_sdram_we_n,sdram_we_n;
  wire ref_sdram_cas_n,sdram_cas_n;
  wire ref_sdram_ras_n,sdram_ras_n;
  wire [12:0] ref_sdram_adr,sdram_adr;
  wire [1:0] ref_sdram_ba,sdram_ba;


    wire match;
    integer total_tests = 0;
    integer failed_tests = 0;

assign match =({ref_ack ,ref_read,ref_write,ref_concerned_bank,ref_sdram_cs_n,ref_sdram_we_n,ref_sdram_cas_n,ref_sdram_ras_n,ref_sdram_adr,ref_sdram_ba} === {ack,read,write,concerned_bank,sdram_cs_n,sdram_we_n,sdram_cas_n,sdram_ras_n,sdram_adr,sdram_ba});


  // Instantiate the Unit Under Test (UUT)
  top #(
    .sdram_depth(sdram_depth),
    .sdram_columndepth(sdram_columndepth)
  ) uut (
    .sys_clk(sys_clk),
    .sdram_rst(sdram_rst),
    .tim_rp(tim_rp),
    .tim_rcd(tim_rcd),
    .tim_refi(tim_refi),
    .tim_rfc(tim_rfc),
    .stb(stb),
    .we(we),
    .address(address),
    .ack(ack),
    .read(read),
    .write(write),
    .concerned_bank(concerned_bank),
    .read_safe(read_safe),
    .write_safe(write_safe),
    .precharge_safe(precharge_safe),
    .sdram_cs_n(sdram_cs_n),
    .sdram_we_n(sdram_we_n),
    .sdram_cas_n(sdram_cas_n),
    .sdram_ras_n(sdram_ras_n),
    .sdram_adr(sdram_adr),
    .sdram_ba(sdram_ba)
  );

  // Instantiate the Unit Under Test (UUT)
  ref_hpdmc_mgmt #(
    .sdram_depth(sdram_depth),
    .sdram_columndepth(sdram_columndepth)
  ) rf (
    .sys_clk(sys_clk),
    .sdram_rst(sdram_rst),
    .tim_rp(tim_rp),
    .tim_rcd(tim_rcd),
    .tim_refi(tim_refi),
    .tim_rfc(tim_rfc),
    .stb(stb),
    .we(we),
    .address(address),
    .ref_ack(ref_ack),
    .ref_read(ref_read),
    .ref_write(ref_write),
    .ref_concerned_bank(ref_concerned_bank),
    .read_safe(read_safe),
    .write_safe(write_safe),
    .precharge_safe(precharge_safe),
    .ref_sdram_cs_n(ref_sdram_cs_n),
    .ref_sdram_we_n(ref_sdram_we_n),
    .ref_sdram_cas_n(ref_sdram_cas_n),
    .ref_sdram_ras_n(ref_sdram_ras_n),
    .ref_sdram_adr(ref_sdram_adr),
    .ref_sdram_ba(ref_sdram_ba)
  );


  // Clock generation
  always #5 sys_clk = ~sys_clk;

  initial begin
    // Initialize Inputs
    sys_clk = 0;
    sdram_rst = 0;
    tim_rp = 3'd3;
    tim_rcd = 3'd3;
    tim_refi = 11'd1000;
    tim_rfc = 4'd5;
    stb = 0;
    we = 0;
    address = 0;
    read_safe = 1;
    write_safe = 1;
    precharge_safe = 4'b1111;

    // Wait for global reset
    #10;

    // Test Case 1: Reset the module
    sdram_rst = 1;
    #10;
    sdram_rst = 0;
 compare();
    #10;

    // Test Case 2: Write operation
    stb = 1;
    we = 1;
    address = 23'h000001;
    #10;
    stb = 0;
    we = 0;
 compare();
    #10;

    // Test Case 3: Read operation
    stb = 1;
    we = 0;
    address = 23'h000002;
    #10;
    stb = 0;
 compare();
    #10;


repeat (96) begin
            @(posedge sys_clk);
	  tim_rp = $random;
	  tim_rcd = $random;
	  tim_refi = $random;
	  tim_rfc = $random;
	  stb = $random;
	  we = $random;
	  //address = $random ;
	  read_safe = $random;
	  write_safe = $random;
	  precharge_safe = $random;

  // Inputs
  //reg [sdram_depth-3-1:0] address;

            #10;
            compare();
        end

    // Finish simulation
        $display("All tests passed: design passed");
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
				$display("ack = %h,read = %h, write = %h,concerned_bank = %h,sdram_cs_n = %h, sdram_we_n = %h,sdram_cas_n = %h,sdram_ras_n = %h,sdram_adr = %h,sdram_ba = %h,",ack,read,write,concerned_bank,sdram_cs_n,sdram_we_n,sdram_cas_n,sdram_ras_n,sdram_adr,sdram_ba);
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
			$display("ack = %h,read = %h, write = %h,concerned_bank = %h,sdram_cs_n = %h, sdram_we_n = %h,sdram_cas_n = %h,sdram_ras_n = %h,sdram_adr = %h,sdram_ba = %h,",ack,read,write,concerned_bank,sdram_cs_n,sdram_we_n,sdram_cas_n,sdram_ras_n,sdram_adr,sdram_ba);
			failed_tests = failed_tests + 1; 
           
		end
    
	endtask


endmodule
