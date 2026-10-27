 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter AWIDTH = 3;
    parameter RAM_DEPTH = (1 << AWIDTH);
    parameter ALMOST_EMPTY_THRESH = 1;
    parameter ALMOST_FULL_THRESH = RAM_DEPTH - 2;

    // Inputs
    reg wclk;
    reg wrst_n;
    reg wen;
    reg rclk;
    reg rrst_n;
    reg ren;

    // Outputs
    wire wfull_ref, wfull_dut;
    wire walmost_full_ref, walmost_full_dut;
    wire mem_wen_ref, mem_wen_dut;
    wire [AWIDTH:0] mem_waddr_ref, mem_waddr_dut;
    wire rempty_ref, rempty_dut;
    wire ralmost_empty_ref, ralmost_empty_dut;
    wire mem_ren_ref, mem_ren_dut;
    wire [AWIDTH:0] mem_raddr_ref, mem_raddr_dut;
    wire wr_match, rd_match;
    
    integer total_tests = 0;
	integer failed_tests = 0;

    assign wr_match = ({wfull_ref, walmost_full_ref, mem_wen_ref, mem_waddr_ref} === ({wfull_ref, walmost_full_ref, mem_wen_ref, mem_waddr_ref} ^ {wfull_dut, walmost_full_dut, mem_wen_dut, mem_waddr_dut} ^ {wfull_ref, walmost_full_ref, mem_wen_ref, mem_waddr_ref}));

    assign rd_match = ({rempty_ref, ralmost_empty_ref, mem_ren_ref, mem_raddr_ref} === ({rempty_ref, ralmost_empty_ref, mem_ren_ref, mem_raddr_ref} ^ {rempty_dut, ralmost_empty_dut, mem_ren_dut, mem_raddr_dut} ^ {rempty_ref, ralmost_empty_ref, mem_ren_ref, mem_raddr_ref}));



    // Instantiate the generic_fifo_ctrl module
    generic_fifo_ctrl_ref #(
        .AWIDTH(AWIDTH),
        .RAM_DEPTH(RAM_DEPTH),
        .ALMOST_EMPTY_THRESH(ALMOST_EMPTY_THRESH),
        .ALMOST_FULL_THRESH(ALMOST_FULL_THRESH)
    ) ref_model (
        .wclk(wclk),
        .wrst_n(wrst_n),
        .wen(wen),
        .wfull_ref(wfull_ref),
        .walmost_full_ref(walmost_full_ref),
        .mem_wen_ref(mem_wen_ref),
        .mem_waddr_ref(mem_waddr_ref),
        .rclk(rclk),
        .rrst_n(rrst_n),
        .ren(ren),
        .rempty_ref(rempty_ref),
        .ralmost_empty_ref(ralmost_empty_ref),
        .mem_ren_ref(mem_ren_ref),
        .mem_raddr_ref(mem_raddr_ref)
    );

    top #(
        .AWIDTH(AWIDTH),
        .RAM_DEPTH(RAM_DEPTH),
        .ALMOST_EMPTY_THRESH(ALMOST_EMPTY_THRESH),
        .ALMOST_FULL_THRESH(ALMOST_FULL_THRESH)
    ) dut (
        .wclk(wclk),
        .wrst_n(wrst_n),
        .wen(wen),
        .wfull(wfull_dut),
        .walmost_full(walmost_full_dut),
        .mem_wen(mem_wen_dut),
        .mem_waddr(mem_waddr_dut),
        .rclk(rclk),
        .rrst_n(rrst_n),
        .ren(ren),
        .rempty(rempty_dut),
        .ralmost_empty(ralmost_empty_dut),
        .mem_ren(mem_ren_dut),
        .mem_raddr(mem_raddr_dut)
    );

    // Clock generation
    initial begin
        wclk = 0;
        rclk = 0;
        forever #5 wclk = ~wclk; // Write clock
    end

    initial begin
        forever #7 rclk = ~rclk; // Read clock
    end

    // Test procedure
    initial begin
        // Initialize inputs
        wrst_n = 0;
        wclk = 0;
        wen = 0;
        rclk = 0;
        rrst_n = 0;
        ren = 0;

        // Reset the module
        #100;
        wrst_n = 1;
        rrst_n = 1;
        repeat (20) begin
            wen = 1;
            @(posedge wclk);
            wr_compare();
        end
        @(posedge wclk);
        wen = 0;
        repeat (20) begin
            ren = 1;
            @(posedge rclk);
            rd_compare();
        end
        fork
            repeat (30) begin
                wen = $random;
                @(posedge wclk);
                wr_compare();
            end
            repeat (30) begin
                ren = $random;
                @(posedge rclk);
                rd_compare();
            end
        join
        #10;
        wrst_n = 0;
        rrst_n = 0;
        #10;
        wrst_n = 1;
        rrst_n = 1;
        #10;
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
    end


    task rd_compare;
        total_tests = total_tests + 1;

        if (rd_match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("rrst_n = %b, ren = %b, rempty_dut = %b, ralmost_empty_dut = %b, mem_ren_dut = %b, mem_raddr_dut = %b, rempty_ref = %b, ralmost_empty_ref = %b, mem_ren_ref = %b, mem_raddr_ref = %b", rrst_n, ren, rempty_dut, ralmost_empty_dut, mem_ren_dut, mem_raddr_dut, rempty_ref, ralmost_empty_ref, mem_ren_ref, mem_raddr_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("rrst_n = %b, ren = %b, rempty_dut = %b, ralmost_empty_dut = %b, mem_ren_dut = %b, mem_raddr_dut = %b, rempty_ref = %b, ralmost_empty_ref = %b, mem_ren_ref = %b, mem_raddr_ref = %b", rrst_n, ren, rempty_dut, ralmost_empty_dut, mem_ren_dut, mem_raddr_dut, rempty_ref, ralmost_empty_ref, mem_ren_ref, mem_raddr_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    task wr_compare;
        total_tests = total_tests + 1;

        if (wr_match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("wrst_n = %b, wen = %b, wfull_dut = %b, walmost_full_dut = %b, mem_wen_dut = %b, mem_waddr_dut = %b, wfull_ref = %b, walmost_full_ref = %b, mem_wen_ref = %b, mem_waddr_ref = %b", wrst_n, wen, wfull_dut, walmost_full_dut, mem_wen_dut, mem_waddr_dut, wfull_ref, walmost_full_ref, mem_wen_ref, mem_waddr_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("wrst_n = %b, wen = %b, wfull_dut = %b, walmost_full_dut = %b, mem_wen_dut = %b, mem_waddr_dut = %b, wfull_ref = %b, walmost_full_ref = %b, mem_wen_ref = %b, mem_waddr_ref = %b", wrst_n, wen, wfull_dut, walmost_full_dut, mem_wen_dut, mem_waddr_dut, wfull_ref, walmost_full_ref, mem_wen_ref, mem_waddr_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask



endmodule
