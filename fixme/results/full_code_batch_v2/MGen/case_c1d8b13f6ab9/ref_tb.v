 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter ADDRESS_WIDTH = 32;
    parameter AUX_WIDTH = 1;

    // Inputs
    reg i_clk;
    reg i_rst;
    reg i_ce;
    reg i_stalled_n;
    reg [ADDRESS_WIDTH-1:0] i_pc;
    reg [AUX_WIDTH-1:0] i_aux;
    reg i_wb_ack;
    reg i_wb_stall;
    reg i_wb_err;
    reg [31:0] i_wb_data;

    // Outputs
    wire [31:0] o_i_ref, o_i_dut;
    wire [ADDRESS_WIDTH-1:0] o_pc_ref, o_pc_dut;
    wire [AUX_WIDTH-1:0] o_aux_ref, o_aux_dut;
    wire o_valid_ref, o_valid_dut;
    wire o_illegal_ref, o_illegal_dut;
    wire o_wb_cyc_ref, o_wb_cyc_dut;
    wire o_wb_stb_ref, o_wb_stb_dut;
    wire o_wb_we_ref, o_wb_we_dut;
    wire [ADDRESS_WIDTH-1:0] o_wb_addr_ref, o_wb_addr_dut;
    wire [31:0] o_wb_data_ref, o_wb_data_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({o_i_ref, o_pc_ref, o_aux_ref, o_valid_ref, o_illegal_ref, o_wb_cyc_ref, o_wb_stb_ref, o_wb_we_ref, o_wb_addr_ref, o_wb_data_ref} === ({o_i_ref, o_pc_ref, o_aux_ref, o_valid_ref, o_illegal_ref, o_wb_cyc_ref, o_wb_stb_ref, o_wb_we_ref, o_wb_addr_ref, o_wb_data_ref} ^ {o_i_dut, o_pc_dut, o_aux_dut, o_valid_dut, o_illegal_dut, o_wb_cyc_dut, o_wb_stb_dut, o_wb_we_dut, o_wb_addr_dut, o_wb_data_dut} ^ {o_i_ref, o_pc_ref, o_aux_ref, o_valid_ref, o_illegal_ref, o_wb_cyc_ref, o_wb_stb_ref, o_wb_we_ref, o_wb_addr_ref, o_wb_data_ref}));

    // Instantiate the prefetch module
    prefetch_ref #(.ADDRESS_WIDTH(ADDRESS_WIDTH), .AUX_WIDTH(AUX_WIDTH)) ref_model (
        .i_clk(i_clk),
        .i_rst(i_rst),
        .i_ce(i_ce),
        .i_stalled_n(i_stalled_n),
        .i_pc(i_pc),
        .i_aux(i_aux),
        .o_i_ref(o_i_ref),
        .o_pc_ref(o_pc_ref),
        .o_aux_ref(o_aux_ref),
        .o_valid_ref(o_valid_ref),
        .o_illegal_ref(o_illegal_ref),
        .o_wb_cyc_ref(o_wb_cyc_ref),
        .o_wb_stb_ref(o_wb_stb_ref),
        .o_wb_we_ref(o_wb_we_ref),
        .o_wb_addr_ref(o_wb_addr_ref),
        .o_wb_data_ref(o_wb_data_ref),
        .i_wb_ack(i_wb_ack),
        .i_wb_stall(i_wb_stall),
        .i_wb_err(i_wb_err),
        .i_wb_data(i_wb_data)
    );

    top #(.ADDRESS_WIDTH(ADDRESS_WIDTH), .AUX_WIDTH(AUX_WIDTH)) dut (
        .i_clk(i_clk),
        .i_rst(i_rst),
        .i_ce(i_ce),
        .i_stalled_n(i_stalled_n),
        .i_pc(i_pc),
        .i_aux(i_aux),
        .o_i(o_i_dut),
        .o_pc(o_pc_dut),
        .o_aux(o_aux_dut),
        .o_valid(o_valid_dut),
        .o_illegal(o_illegal_dut),
        .o_wb_cyc(o_wb_cyc_dut),
        .o_wb_stb(o_wb_stb_dut),
        .o_wb_we(o_wb_we_dut),
        .o_wb_addr(o_wb_addr_dut),
        .o_wb_data(o_wb_data_dut),
        .i_wb_ack(i_wb_ack),
        .i_wb_stall(i_wb_stall),
        .i_wb_err(i_wb_err),
        .i_wb_data(i_wb_data)
    );

    // Clock generation
    initial begin
        i_clk = 0;
        forever #5 i_clk = ~i_clk; // 100MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        i_rst = 1;
        i_ce = 0;
        i_stalled_n = 1;
        i_pc = 0;
        i_aux = 0;
        i_wb_ack = 0;
        i_wb_stall = 0;
        i_wb_err = 0;
        i_wb_data = 32'hABCD1234; // Example data

        // Release reset
        #10;
        i_rst = 0;

        // Test Case 1: Basic Fetch
        #10; 
        i_ce = 1; 
        i_pc = 32'h00000010; // Set program counter
        #10;
        i_wb_ack = 1; // Acknowledge the fetch
        #10;
        i_wb_ack = 0; // Deassert acknowledge

        // Check outputs
        #10;
        compare();

        // Test Case 2: Illegal Access
        #10;
        i_wb_err = 1; // Simulate an error
        #10;
        i_wb_ack = 1; // Acknowledge with error
        #10;
        i_wb_ack = 0; 
        #10;
        compare();

        // Test Case 3: Stalling
        #10;
        i_stalled_n = 0; // Simulate stall condition
        #10;
        compare();

        // Test Case 4: Resume after Stall
        #10;
        i_stalled_n = 1; // Release stall
        #10;
        i_wb_ack = 1; // Acknowledge fetch
        #10;
        i_wb_ack = 0; 
        #10;
        compare();

        repeat (94) begin
            i_stalled_n = $random;
            i_pc = $random;
            i_aux = $random;
            i_wb_ack = $random;
            i_wb_stall = $random;
            i_wb_err = $random;
            i_wb_data = $random;
            #10;
            compare();
        end

        i_ce = 0;
        compare();
        i_rst = 1;
        #20;
        compare();

        // Finish simulation
        #10;
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
            	$display("i_rst = %h, i_ce = %h, i_stalled_n = %h, i_pc = %h, i_aux = %h, i_wb_ack = %h, i_wb_stall = %h, i_wb_err = %h, i_wb_data = %h, o_i_dut = %h, o_pc_dut = %h, o_aux_dut = %h, o_valid_dut = %h, o_illegal_dut = %h, o_wb_cyc_dut = %h, o_wb_stb_dut = %h, o_wb_we_dut = %h, o_wb_addr_dut = %h, o_wb_data_dut = %h, o_i_ref = %h, o_pc_ref = %h, o_aux_ref = %h, o_valid_ref = %h, o_illegal_ref = %h, o_wb_cyc_ref = %h, o_wb_stb_ref = %h, o_wb_we_ref = %h, o_wb_addr_ref = %h, o_wb_data_ref = %h", i_rst, i_ce, i_stalled_n, i_pc, i_aux, i_wb_ack, i_wb_stall, i_wb_err, i_wb_data, o_i_dut, o_pc_dut, o_aux_dut, o_valid_dut, o_illegal_dut, o_wb_cyc_dut, o_wb_stb_dut, o_wb_we_dut, o_wb_addr_dut, o_wb_data_dut, o_i_ref, o_pc_ref, o_aux_ref, o_valid_ref, o_illegal_ref, o_wb_cyc_ref, o_wb_stb_ref, o_wb_we_ref, o_wb_addr_ref, o_wb_data_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("i_rst = %h, i_ce = %h, i_stalled_n = %h, i_pc = %h, i_aux = %h, i_wb_ack = %h, i_wb_stall = %h, i_wb_err = %h, i_wb_data = %h, o_i_dut = %h, o_pc_dut = %h, o_aux_dut = %h, o_valid_dut = %h, o_illegal_dut = %h, o_wb_cyc_dut = %h, o_wb_stb_dut = %h, o_wb_we_dut = %h, o_wb_addr_dut = %h, o_wb_data_dut = %h, o_i_ref = %h, o_pc_ref = %h, o_aux_ref = %h, o_valid_ref = %h, o_illegal_ref = %h, o_wb_cyc_ref = %h, o_wb_stb_ref = %h, o_wb_we_ref = %h, o_wb_addr_ref = %h, o_wb_data_ref = %h", i_rst, i_ce, i_stalled_n, i_pc, i_aux, i_wb_ack, i_wb_stall, i_wb_err, i_wb_data, o_i_dut, o_pc_dut, o_aux_dut, o_valid_dut, o_illegal_dut, o_wb_cyc_dut, o_wb_stb_dut, o_wb_we_dut, o_wb_addr_dut, o_wb_data_dut, o_i_ref, o_pc_ref, o_aux_ref, o_valid_ref, o_illegal_ref, o_wb_cyc_ref, o_wb_stb_ref, o_wb_we_ref, o_wb_addr_ref, o_wb_data_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

