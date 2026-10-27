 `timescale 1ns / 1ps

module tb;

// Inputs
reg [6:0] q;

// Outputs
wire [63:0] e_ref, e_dut;

wire match;

integer total_tests = 0;
integer failed_tests = 0;

assign match = (e_ref === (e_ref ^ e_dut ^ e_ref));


// Instantiate the Unit Under Test (UUT)
sparc_exu_ecc_dec_ref ref_model (
    .q(q),
    .e_ref(e_ref)
);

top dut (
    .q(q),
    .e(e_dut)
);

integer i = 0;

initial begin
    // Initialize Inputs
    q = 7'b0;
    #10;
    // Apply test vectors
    for (i = 0; i <129; i++) begin
        q = i;
        #10;
        compare();
    end
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
//				$display("testcase is passed!!!");
            	$display("q = %h, e_dut = %h, e_ref = %h", q, e_dut, e_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("q = %h, e_dut = %h, e_ref = %h", q, e_dut, e_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask


endmodule

