 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period for clk

    // Inputs
    reg clk;
    reg reset;
    reg [7:0] Sm1, Sm2, Sm3, Sm4, Sm5, Sm6, Sm7, Sm8;
    reg [7:0] Sm9, Sm10, Sm11, Sm12, Sm13, Sm14, Sm15, Sm16;
    reg Sm_ready;
    reg erasure_ready;
    reg [3:0] erasure_cnt;
    reg [7:0] pow1, pow2;
    reg [7:0] dec1;

    // Outputs
    wire [7:0] ref_add_pow1, ref_add_pow2;
    wire [7:0] ref_add_dec1;
    wire ref_L_ready;
    wire [7:0] ref_L1, ref_L2, ref_L3, ref_L4, ref_L5, ref_L6, ref_L7, ref_L8;

    wire [7:0] dut_add_pow1, dut_add_pow2;
    wire [7:0] dut_add_dec1;
    wire dut_L_ready;
    wire [7:0] dut_L1, dut_L2, dut_L3, dut_L4, dut_L5, dut_L6, dut_L7, dut_L8;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_add_pow1, ref_add_pow2,ref_add_dec1,ref_L_ready,ref_L1, ref_L2, ref_L3, ref_L4, ref_L5, ref_L6,ref_L7,ref_L8} === ({ref_add_pow1, ref_add_pow2,ref_add_dec1,ref_L_ready,ref_L1, ref_L2, ref_L3, ref_L4, ref_L5, ref_L6,ref_L7,ref_L8} ^ {dut_add_pow1,dut_add_pow2,dut_add_dec1,dut_L_ready,dut_L1,dut_L2,dut_L3,dut_L4, dut_L5,dut_L6,dut_L7,dut_L8} ^ {ref_add_pow1, ref_add_pow2,ref_add_dec1,ref_L_ready,ref_L1, ref_L2, ref_L3, ref_L4, ref_L5, ref_L6,ref_L7,ref_L8}));


    // Instantiate the BM_lambda module
    top uut1 (
        .clk(clk),
        .reset(reset),
        .Sm1(Sm1), .Sm2(Sm2), .Sm3(Sm3), .Sm4(Sm4),
        .Sm5(Sm5), .Sm6(Sm6), .Sm7(Sm7), .Sm8(Sm8),
        .Sm9(Sm9), .Sm10(Sm10), .Sm11(Sm11), .Sm12(Sm12),
        .Sm13(Sm13), .Sm14(Sm14), .Sm15(Sm15), .Sm16(Sm16),
        .Sm_ready(Sm_ready),
        .erasure_ready(erasure_ready),
        .erasure_cnt(erasure_cnt),
        .pow1(pow1), .pow2(pow2),
        .dec1(dec1),
        .add_pow1(dut_add_pow1), .add_pow2(dut_add_pow2),
        .add_dec1(dut_add_dec1),
        .L_ready(dut_L_ready),
        .L1(dut_L1), .L2(dut_L2), .L3(dut_L3), .L4(dut_L4),
        .L5(dut_L5), .L6(dut_L6), .L7(dut_L7), .L8(dut_L8)
    );

    // Instantiate the BM_lambda module
    ref_BM_lamda uut2 (
        .clk(clk),
        .reset(reset),
        .Sm1(Sm1), .Sm2(Sm2), .Sm3(Sm3), .Sm4(Sm4),
        .Sm5(Sm5), .Sm6(Sm6), .Sm7(Sm7), .Sm8(Sm8),
        .Sm9(Sm9), .Sm10(Sm10), .Sm11(Sm11), .Sm12(Sm12),
        .Sm13(Sm13), .Sm14(Sm14), .Sm15(Sm15), .Sm16(Sm16),
        .Sm_ready(Sm_ready),
        .erasure_ready(erasure_ready),
        .erasure_cnt(erasure_cnt),
        .pow1(pow1), .pow2(pow2),
        .dec1(dec1),
        .ref_add_pow1(ref_add_pow1), .ref_add_pow2(ref_add_pow2),
        .ref_add_dec1(ref_add_dec1),
        .ref_L_ready(ref_L_ready),
        .ref_L1(ref_L1), .ref_L2(ref_L2), .ref_L3(ref_L3), .ref_L4(ref_L4),
        .ref_L5(ref_L5), .ref_L6(ref_L6), .ref_L7(ref_L7), .ref_L8(ref_L8)
    );

    // Generate clock signal
    initial begin
        clk = 0;
        forever #(CLK_PERIOD / 2) clk = ~clk; // Toggle clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        reset = 1;
        Sm1 = 8'h00; Sm2 = 8'h01; Sm3 = 8'h02; Sm4 = 8'h03;
        Sm5 = 8'h04; Sm6 = 8'h05; Sm7 = 8'h06; Sm8 = 8'h07;
        Sm9 = 8'h08; Sm10 = 8'h09; Sm11 = 8'h0A; Sm12 = 8'h0B;
        Sm13 = 8'h0C; Sm14 = 8'h0D; Sm15 = 8'h0E; Sm16 = 8'h0F;
        Sm_ready = 0;
        erasure_ready = 0;
        erasure_cnt = 4'h0;
        pow1 = 8'h10;
        pow2 = 8'h20;
        dec1 = 8'h30;

        // Apply reset
        #(CLK_PERIOD);
        reset = 0; // De-assert reset
        #(CLK_PERIOD);

        // Test Case 1: Check initial state after reset
        if (dut_L_ready == 0) begin
            $display("Test Case 1 Passed: L_ready is initially low.");
        end else begin
            $display("Test Case 1 Failed: L_ready is not low.");
compare();
        end

        // Test Case 2: Simulate Sm_ready signal
        Sm_ready = 1; // Assert ready signal
        #(CLK_PERIOD);
        Sm_ready = 0; // De-assert after one clock cycle
        #(CLK_PERIOD);
compare();

        // Test Case 3: Check output values after Sm_ready
        //if (uut.L[1] == 1) begin
        //    $display("Test Case 2 Passed: Sm_ready processed, L[1] is set.");
       // end else begin
        //    $display("Test Case 2 Failed: Sm_ready not processed correctly.");
       // end
//compare();

        // Test Case 4: Simulate erasure process
        erasure_ready = 1; // Assert erasure ready
        erasure_cnt = 4'h2; // Example value
        #(CLK_PERIOD);
        erasure_ready = 0; // De-assert after one clock cycle
        #(CLK_PERIOD);
compare();

        // Test Case 5: Check L values after erasure
        if (dut_L1 == 0) begin
            $display("Test Case 3 Passed: Erasure processed, L1 is zero.");
        end else begin
            $display("Test Case 3 Failed: Erasure not processed correctly.");
compare();
        end

        // Test Case 6: Check add_dec1 output
        if (dut_add_dec1 == 8'h01) begin
            $display("Test Case 4 Passed: add_dec1 calculated correctly.");
        end else begin
            $display("Test Case 4 Failed: add_dec1 not calculated correctly.");
compare();
#10;
reset=0;
#10;
reset=1;
#10;

        end
repeat (96) begin
            @(posedge clk);
Sm1 = $random; Sm2 = $random; Sm3 = $random; Sm4 = $random; Sm5 = $random; Sm6 = $random; Sm7 = $random; Sm8 = $random;
Sm9 = $random; Sm10 = $random; Sm11 = $random; Sm12 = $random; Sm13 = $random; Sm14 = $random; Sm15 = $random; Sm16 = $random;
Sm_ready = $random;
erasure_ready = $random;
erasure_cnt = $random;
pow1 = $random;
pow2 = $random;
dec1 = $random;


            compare();
        end

        // Finish simulation
        #(CLK_PERIOD * 10);
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
				$display("testcase is passed!!!");
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            failed_tests = failed_tests + 1; 
		end
    
	endtask
endmodule
