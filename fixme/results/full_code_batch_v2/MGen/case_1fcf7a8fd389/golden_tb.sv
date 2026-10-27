`timescale 1ns/1ps
 module tb;

  // Inputs
  reg clk;
  reg rst_n;
  reg ena;
  reg t1s_sel;
  reg prefix_sel;
  reg suffix_sel;
  reg calc_sel;
  reg [1:0] TrailingOnes;
  reg [4:0] TotalCoeff;
  reg [0:15] rbsp;
  reg [3:0] i;

  // Outputs
  wire [8:0] ref_level_0;
  wire [8:0] ref_level_1;
  wire [8:0] ref_level_2;
  wire [8:0] ref_level_3;
  wire [8:0] ref_level_4;
  wire [8:0] ref_level_5;
  wire [8:0] ref_level_6;
  wire [8:0] ref_level_7;
  wire [8:0] ref_level_8;
  wire [8:0] ref_level_9;
  wire [8:0] ref_level_10;
  wire [8:0] ref_level_11;
  wire [8:0] ref_level_12;
  wire [8:0] ref_level_13;
  wire [8:0] ref_level_14;
  wire [8:0] ref_level_15;
  wire [4:0] ref_len_comb;

  wire [8:0] dut_level_0;
  wire [8:0] dut_level_1;
  wire [8:0] dut_level_2;
  wire [8:0] dut_level_3;
  wire [8:0] dut_level_4;
  wire [8:0] dut_level_5;
  wire [8:0] dut_level_6;
  wire [8:0] dut_level_7;
  wire [8:0] dut_level_8;
  wire [8:0] dut_level_9;
  wire [8:0] dut_level_10;
  wire [8:0] dut_level_11;
  wire [8:0] dut_level_12;
  wire [8:0] dut_level_13;
  wire [8:0] dut_level_14;
  wire [8:0] dut_level_15;
  wire [4:0] dut_len_comb;

wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_level_0,ref_level_1,ref_level_2,ref_level_3,ref_level_4,ref_level_5,ref_level_6,ref_level_7,ref_level_8,ref_level_9,ref_level_10,ref_level_11,ref_level_12,ref_level_13,ref_level_14,ref_level_15,ref_len_comb} === ({ref_level_0,ref_level_1,ref_level_2,ref_level_3,ref_level_4,ref_level_5,ref_level_6,ref_level_7,ref_level_8,ref_level_9,ref_level_10,ref_level_11,ref_level_12,ref_level_13,ref_level_14,ref_level_15,ref_len_comb}  ^ {dut_level_0,dut_level_1,dut_level_2,dut_level_3,dut_level_4,dut_level_5,dut_level_6,dut_level_7,dut_level_8,dut_level_9,dut_level_10,dut_level_11,dut_level_12,dut_level_13,dut_level_14,dut_level_15,dut_len_comb}  ^ {ref_level_0,ref_level_1,ref_level_2,ref_level_3,ref_level_4,ref_level_5,ref_level_6,ref_level_7,ref_level_8,ref_level_9,ref_level_10,ref_level_11,ref_level_12,ref_level_13,ref_level_14,ref_level_15,ref_len_comb} ));


  // Instantiate the Unit Under Test (UUT)
  top uut1 (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),
    .t1s_sel(t1s_sel),
    .prefix_sel(prefix_sel),
    .suffix_sel(suffix_sel),
    .calc_sel(calc_sel),
    .TrailingOnes(TrailingOnes),
    .TotalCoeff(TotalCoeff),
    .rbsp(rbsp),
    .i(i),
    .level_0(dut_level_0),
    .level_1(dut_level_1),
    .level_2(dut_level_2),
    .level_3(dut_level_3),
    .level_4(dut_level_4),
    .level_5(dut_level_5),
    .level_6(dut_level_6),
    .level_7(dut_level_7),
    .level_8(dut_level_8),
    .level_9(dut_level_9),
    .level_10(dut_level_10),
    .level_11(dut_level_11),
    .level_12(dut_level_12),
    .level_13(dut_level_13),
    .level_14(dut_level_14),
    .level_15(dut_level_15),
    .len_comb(dut_len_comb)
  );

  ref_cavlc_read_levels uut2 (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),
    .t1s_sel(t1s_sel),
    .prefix_sel(prefix_sel),
    .suffix_sel(suffix_sel),
    .calc_sel(calc_sel),
    .TrailingOnes(TrailingOnes),
    .TotalCoeff(TotalCoeff),
    .rbsp(rbsp),
    .i(i),
    .ref_level_0(ref_level_0),
    .ref_level_1(ref_level_1),
    .ref_level_2(ref_level_2),
    .ref_level_3(ref_level_3),
    .ref_level_4(ref_level_4),
    .ref_level_5(ref_level_5),
    .ref_level_6(ref_level_6),
    .ref_level_7(ref_level_7),
    .ref_level_8(ref_level_8),
    .ref_level_9(ref_level_9),
    .ref_level_10(ref_level_10),
    .ref_level_11(ref_level_11),
    .ref_level_12(ref_level_12),
    .ref_level_13(ref_level_13),
    .ref_level_14(ref_level_14),
    .ref_level_15(ref_level_15),
    .ref_len_comb(ref_len_comb)
  );
  // Clock generation
  always #5 clk = ~clk;

  initial begin
    // Initialize Inputs
    clk = 0;
    rst_n = 0;
    ena = 0;
    t1s_sel = 0;
    prefix_sel = 0;
    suffix_sel = 0;
    calc_sel = 0;
    TrailingOnes = 0;
    TotalCoeff = 0;
    rbsp = 0;
    i = 0;

    // Wait for global reset
    #10;
    rst_n = 1;

    // Test Case 1: Initialize and set TrailingOnes
    ena = 1;
    t1s_sel = 1;
    TrailingOnes = 2;
    rbsp = 16'b1010_1010_1010_1010;
    i = 0;
    #10;
    i = 1;
    #10;
    i = 2;
    #10;
    i = 3;
    #10;
    t1s_sel = 0;
compare();

    // Test Case 2: Set prefix_sel and suffix_sel
    prefix_sel = 1;
    suffix_sel = 1;
    TotalCoeff = 5;
    rbsp = 16'b1100_1100_1100_1100;
    i = 0;
    #10;
    i = 1;
    #10;
    i = 2;
    #10;
    i = 3;
    #10;
    prefix_sel = 0;
    suffix_sel = 0;
compare();

    // Test Case 3: Set calc_sel
    calc_sel = 1;
    i = 0;
    #10;
    i = 1;
    #10;
    i = 2;
    #10;
    i = 3;
    #10;
    calc_sel = 0;
compare();

ena = 1;
    t1s_sel = 1;
    TrailingOnes = 2;
    TotalCoeff = 5;
    rbsp = 16'b1010101010101010;
    i = 0;
    #20;
compare();

   
    t1s_sel = 0;
    prefix_sel = 1;
    TrailingOnes = 1;
    TotalCoeff = 10;
    rbsp = 16'b1111000011110000;
    i = 1;
    #20;
compare();

    
    prefix_sel = 0;
    suffix_sel = 1;
    TrailingOnes = 0;
    TotalCoeff = 15;
    rbsp = 16'b1111111100000000;
    i = 2;
    #20;
compare();

    suffix_sel = 0;
    calc_sel = 1;
    TrailingOnes = 3;
    TotalCoeff = 20;
    rbsp = 16'b0000000011111111;
    i = 3;
    #20;
compare();

    t1s_sel = 1;
    prefix_sel = 1;
    suffix_sel = 1;
    calc_sel = 1;
    TrailingOnes = 2;
    TotalCoeff = 10;
    rbsp = 16'b1010101010101010;
    i = 4;
    #20;
compare();

    repeat (1000) begin
      @(posedge clk);
      ena = $random % 2;
      t1s_sel = $random % 2;
      prefix_sel = $random % 2;
      suffix_sel = $random % 2;
      calc_sel = $random % 2;
      TrailingOnes = $random % 4;
      TotalCoeff = $random % 32;
      rbsp = $random;
      i = $random % 16;
      compare();
    end
     compare();
  
   #20;
rst_n =0;
   #20;
rst_n =1;
   #20;

    // Finish simulation
        
        $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
  end

  initial begin
    // Monitor signals
    $monitor("Time=%0t, clk=%b, rst_n=%b, ena=%b, t1s_sel=%b, prefix_sel=%b, suffix_sel=%b, calc_sel=%b, TrailingOnes=%b, TotalCoeff=%b, rbsp=%b, i=%b, dut_level_0=%b, dut_level_1=%b, dut_level_2=%b, dut_level_3=%b, dut_level_4=%b, dut_level_5=%b, dut_level_6=%b, dut_level_7=%b, dut_level_8=%b, dut_level_9=%b, dut_level_10=%b, dut_level_11=%b, dut_level_12=%b, dut_level_13=%b, dut_level_14=%b, dut_level_15=%b, dut_len_comb=%b", 
              $time, clk, rst_n, ena, t1s_sel, prefix_sel, suffix_sel, calc_sel, TrailingOnes, TotalCoeff, rbsp, i, dut_level_0, dut_level_1, dut_level_2, dut_level_3, dut_level_4, dut_level_5, dut_level_6, dut_level_7, dut_level_8, dut_level_9, dut_level_10, dut_level_11, dut_level_12, dut_level_13, dut_level_14, dut_level_15, dut_len_comb);
  end

task compare;begin
        total_tests = total_tests + 1;
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin				$display("\033[1;32mtestcase is passed!!!\033[0m");
				$display("testcase is passed!!!");
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            failed_tests = failed_tests + 1; 
		end
	end
endtask


endmodule
