`timescale 1ns/1ps
module tb;

// Parameters
parameter GSHARE_WIDTH = 4;
parameter PHT_LEN = 16;

// Inputs
reg clk;
reg reset;
reg [31:0] pc;
reg [31:0] prev_pc;
reg prev_branch_in;
reg prev_taken;

// Outputs
wire cur_pred_ref, cur_pred_dut;

wire match;

integer total_tests = 0;
integer failed_tests = 0;

assign match = (cur_pred_ref === (cur_pred_ref ^ cur_pred_dut ^ cur_pred_ref));

// Instantiate the gshare module
gshare_ref #(
    .GSHARE_WIDTH(GSHARE_WIDTH),
    .PHT_LEN(PHT_LEN)
) ref_model (
    .clk(clk),
    .reset(reset),
    .pc(pc),
    .prev_pc(prev_pc),
    .prev_branch_in(prev_branch_in),
    .prev_taken(prev_taken),
    .cur_pred_ref(cur_pred_ref)
);

top #(
    .GSHARE_WIDTH(GSHARE_WIDTH),
    .PHT_LEN(PHT_LEN)
) dut (
    .clk(clk),
    .reset(reset),
    .pc(pc),
    .prev_pc(prev_pc),
    .prev_branch_in(prev_branch_in),
    .prev_taken(prev_taken),
    .cur_pred(cur_pred_dut)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk; // 10 time units period
end

// Test sequence
initial begin
    // Initialize signals
    reset = 1;
    pc = 32'd0;
    prev_pc = 32'd0;
    prev_branch_in = 0;
    prev_taken = 0;

    // Apply reset
    #10 reset = 0;
    #10 reset = 1;
    #10 reset = 0;

    // Test case 1: No branches initially
    #10 pc = 32'd100;
    #10 pc = 32'd200;
    #10 pc = 32'd300;
    compare();


    // Test case 2: A branch is taken
    #10 prev_pc = 32'd300;
    prev_branch_in = 1;
    prev_taken = 1;
    pc = 32'd300;
    #10 
    compare();

    // Test case 3: Another branch is taken
    prev_pc = 32'd400;
    prev_branch_in = 1;
    prev_taken = 1;
    pc = 32'd400;
    #10 
    compare();

    // Test case 4: A branch is not taken
    prev_pc = 32'd500;
    prev_branch_in = 1;
    prev_taken = 0;
    pc = 32'd500;
    #10
    compare();


    // Test case 5: A branch is taken again
    prev_pc = 32'd600;
    prev_branch_in = 1;
    prev_taken = 1;
    pc = 32'd600;
    #10
    compare();

    // Test case 6: A branch is not taken again
    prev_pc = 32'd700;
    prev_branch_in = 1;
    prev_taken = 0;
    pc = 32'd700;
    #10
    compare();

    // Test case 7: A branch is taken again
    prev_pc = 32'd800;
    prev_branch_in = 1;
    prev_taken = 1;
    pc = 32'd800;
    #10 
    compare();

    // Test case 8: A branch is not taken again
    prev_pc = 32'd900;
    prev_branch_in = 1;
    prev_taken = 0;
    pc = 32'd9000;
    #10
    compare();
    #10
    compare();
    #10;
    compare();

    repeat (90) begin
        prev_pc = $random;
        prev_branch_in = $random;
        prev_taken = $random;
        pc = $random;
        #10
        compare();
    end


    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish; // End the simulation
end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("pc = %b, prev_pc = %b, prev_branch_in = %b, prev_taken = %b, cur_pred_dut = %b, cur_pred_ref = %b", pc, prev_pc, prev_branch_in, prev_taken, cur_pred_dut, cur_pred_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("pc = %b, prev_pc = %b, prev_branch_in = %b, prev_taken = %b, cur_pred_dut = %b, cur_pred_ref = %b", pc, prev_pc, prev_branch_in, prev_taken, cur_pred_dut, cur_pred_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
