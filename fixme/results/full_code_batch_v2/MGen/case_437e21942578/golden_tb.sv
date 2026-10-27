`timescale 1ns / 1ps
`define P 20 // clock period

module tb;

	// Inputs
	reg clk;
	reg reset;
	reg [28:0] rom_q;

	// Outputs
	wire [8:0] rom_addr_ref, rom_addr_dut;
	wire [5:0] ram_a_addr_ref, ram_a_addr_dut;
	wire [5:0] ram_b_addr_ref, ram_b_addr_dut;
	wire ram_b_w_ref, ram_b_w_dut;
	wire [10:0] pe_ref, pe_dut;
	wire done_ref, done_dut;

	wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({rom_addr_ref, ram_a_addr_ref, ram_b_addr_ref, ram_b_w_ref, pe_ref, done_ref} === ({rom_addr_ref, ram_a_addr_ref, ram_b_addr_ref, ram_b_w_ref, pe_ref, done_ref} ^ {rom_addr_dut, ram_a_addr_dut, ram_b_addr_dut, ram_b_w_dut, pe_dut, done_dut} ^ {rom_addr_ref, ram_a_addr_ref, ram_b_addr_ref, ram_b_w_ref, pe_ref, done_ref}));

	// Instantiate the Unit Under Test (UUT)
	FSM_ref ref_model (
		.clk(clk), 
		.reset(reset), 
		.rom_addr_ref(rom_addr_ref), 
		.rom_q(rom_q), 
		.ram_a_addr_ref(ram_a_addr_ref), 
		.ram_b_addr_ref(ram_b_addr_ref), 
		.ram_b_w_ref(ram_b_w_ref), 
		.pe_ref(pe_ref), 
		.done_ref(done_ref)
	);

	top dut (
		.clk(clk), 
		.reset(reset), 
		.rom_addr(rom_addr_dut), 
		.rom_q(rom_q), 
		.ram_a_addr(ram_a_addr_dut), 
		.ram_b_addr(ram_b_addr_dut), 
		.ram_b_w(ram_b_w_dut), 
		.pe(pe_dut), 
		.done(done_dut)
	);

	initial begin
		// Initialize Inputs
		clk = 0;
		reset = 0;

		// Wait 100 ns for global reset to finish
		#100;
        
		// Add stimulus here
        #(`P/2); reset = 1; #(`P); reset = 0;

		repeat (24) begin
            reset = 1;
            #(`P);
            reset = 0;
			rom_q = $random;
			#(`P);
            compare();
			#(`P);
            compare();
			#(`P);
            compare();
			#(`P*260);
			compare();
		end

        reset = 1;
        #(`P);
        reset = 0;
        #(`P*1000000);
        compare();
        #(`P*2200000);
        compare();

        #(`P);
        reset = 1;
        #(`P);
        reset = 0;
		rom_q = $random;
		rom_q[14:6] = 0;
		#(`P*10000);
		compare();
        reset = 1;
        #(`P);
        reset = 0;
        #(`P);
        compare();


		$display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
	end
    
    initial  forever #(`P/2) clk = ~clk;
    
    /* rom code format 
     * wire [5:0] dest, src1, src2, times; wire [1:0] op;
     * assign {dest, src1, op, times, src2} = rom_q;
     */
   // parameter ADD=2'd0, SUB=2'd1, CUBIC=2'd2, MULT=2'd3;

    //always @ (posedge clk)
    //    case(rom_addr)
    //    0: rom_q <= {6'd10, 6'd11, ADD, 6'd1, 6'd12};
    //    1: rom_q <= {6'd20, 6'd21, SUB, 6'd1, 6'd22};
    //    2: rom_q <= {6'd30, 6'd31, CUBIC, 6'd5, 6'd32};
    //    3: rom_q <= {6'd40, 6'd41, MULT, 6'd33, 6'd42};
    //    default: rom_q <= 0;
    //    endcase

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("reset = %h, rom_q = %h, rom_addr_dut = %h, ram_a_addr_dut = %h, ram_b_addr_dut = %h, ram_b_w_dut = %h, pe_dut = %h, done_dut = %h, rom_addr_ref = %h, ram_a_addr_ref = %h, ram_b_addr_ref = %h, ram_b_w_ref = %h, pe_ref, done_ref = %h", reset, rom_q, rom_addr_dut, ram_a_addr_dut, ram_b_addr_dut, ram_b_w_dut, pe_dut, done_dut, rom_addr_ref, ram_a_addr_ref, ram_b_addr_ref, ram_b_w_ref, pe_ref, done_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("reset = %h, rom_q = %h, rom_addr_dut = %h, ram_a_addr_dut = %h, ram_b_addr_dut = %h, ram_b_w_dut = %h, pe_dut = %h, done_dut = %h, rom_addr_ref = %h, ram_a_addr_ref = %h, ram_b_addr_ref = %h, ram_b_w_ref = %h, pe_ref, done_ref = %h", reset, rom_q, rom_addr_dut, ram_a_addr_dut, ram_b_addr_dut, ram_b_w_dut, pe_dut, done_dut, rom_addr_ref, ram_a_addr_ref, ram_b_addr_ref, ram_b_w_ref, pe_ref, done_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end


endmodule
