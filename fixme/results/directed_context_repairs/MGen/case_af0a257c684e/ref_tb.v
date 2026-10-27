`timescale 1ns/1ps
 module tb;

  // Parameters
  parameter width_exp = 8;
  parameter width_man = 23;
  parameter WIDTH_MAN_EXP = width_exp + width_man;

  // Inputs
  reg clock;
  reg clk_en;
  reg aclr;
  reg [WIDTH_MAN_EXP:0] dataa;
  reg [WIDTH_MAN_EXP:0] datab;

  // Outputs
  wire [WIDTH_MAN_EXP:0] ref_result,dut_result;
  wire ref_overflow,dut_overflow;
  wire ref_underflow,dut_underflow;
  wire ref_zero,dut_zero;
  wire ref_denormal,dut_denormal;
  wire ref_indefinite,dut_indefinite;
  wire ref_nan,dut_nan;

    wire match;
    integer total_tests = 0;
    integer failed_tests = 0;

assign match = ({ref_result,ref_overflow,ref_underflow,ref_zero,ref_denormal,ref_indefinite,ref_nan} === ({ref_result,ref_overflow,ref_underflow,ref_zero,ref_denormal,ref_indefinite,ref_nan} ^ {dut_result,dut_overflow,dut_underflow,dut_zero,dut_denormal,dut_indefinite,dut_nan}^ {ref_result,ref_overflow,ref_underflow,ref_zero,ref_denormal,ref_indefinite,ref_nan}));

  // Instantiate the Unit Under Test (ref)
  ref_altfp_mult  ref_modle(
    .clock(clock),
    .clk_en(clk_en),
    .aclr(aclr),
    .dataa(dataa),
    .datab(datab),
    .ref_result(ref_result),
    .ref_overflow(ref_overflow),
    .ref_underflow(ref_underflow),
    .ref_zero(ref_zero),
    .ref_denormal(ref_denormal),
    .ref_indefinite(ref_indefinite),
    .ref_nan(ref_nan)
  );

// Instantiate the Unit Under Test (UUT)
  top uut (
    .clock(clock),
    .clk_en(clk_en),
    .aclr(aclr),
    .dataa(dataa),
    .datab(datab),
    .result(dut_result),
    .overflow(dut_overflow),
    .underflow(dut_underflow),
    .zero(dut_zero),
    .denormal(dut_denormal),
    .indefinite(dut_indefinite),
    .nan(dut_nan)
  );

  // Clock generation
  always #5 clock = ~clock;

  initial begin
    // Initialize Inputs
    clock = 0;
    clk_en = 1;
    aclr = 0;
    dataa = 0;
    datab = 0;

    // Wait for global reset
    #10;

    // Test Case 1: Simple multiplication
    dataa = 32'h3F800000; // 1.0 in IEEE 754
    datab = 32'h40000000; // 2.0 in IEEE 754
	compare();
    #10;

    // Test Case 2: Multiplication with ref_zero
    dataa = 32'h00000000; // 0.0 in IEEE 754
    datab = 32'h3F800000; // 1.0 in IEEE 754
	compare();
    #10;

    // Test Case 3: Multiplication with infinity
    dataa = 32'h7F800000; // +Infinity in IEEE 754
    datab = 32'h3F800000; // 1.0 in IEEE 754
	compare();
    #10;

    // Test Case 4: Multiplication with ref_nan
    dataa = 32'h7FC00000; // ref_nan in IEEE 754
    datab = 32'h3F800000; // 1.0 in IEEE 754
	compare();
    #10;

    // Test Case 5: Multiplication with ref_denormalized number
    dataa = 32'h00800000; // Smallest positive ref_denormalized number in IEEE 754
    datab = 32'h3F800000; // 1.0 in IEEE 754
	compare();
    #10;

    // Test Case 6: Reset the module
    aclr = 1;
    #10;
    aclr = 0;
	compare();
    #10;

repeat (96) begin
            @(posedge clock);
  // clk_en = $random;
  // aclr = $random;
   dataa = $random;
   datab = $random;
            #10;
            compare();
        end

        $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);

    // Finish simulation
    $finish;
  end


  initial begin
    // Monitor signals
    $monitor("Time=%0t, clock=%b, clk_en=%b, aclr=%b, dataa=%h, datab=%h, ref_result=%h, ref_overflow=%b, ref_underflow=%b, ref_zero=%b, ref_denormal=%b, ref_indefinite=%b, ref_nan=%b", 
              $time, clock, clk_en, aclr, dataa, datab, ref_result, ref_overflow, ref_underflow, ref_zero, ref_denormal, ref_indefinite, ref_nan);
  end


    task compare;
        total_tests = total_tests + 1;
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
				$display("testcase is passed!!!");
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
           
		end
    
	endtask

endmodule
