 `timescale 1ns / 1ps

module tb_omsp_watchdog;

    // Parameters
    parameter WDTCTL = 9'h120;

    // Inputs
    reg aclk_en;
    reg dbg_freeze;
    reg mclk;
    reg nmi;
    reg nmie;
    reg [7:0] per_addr;
    reg [15:0] per_din;
    reg per_en;
    reg [1:0] per_wen;
    reg puc;
    reg smclk_en;

    // Outputs
    wire nmi_evt_ref, nmi_evt_dut;
    wire [15:0] per_dout_ref, per_dout_dut;
    wire wdtifg_set_ref, wdtifg_set_dut;
    wire wdtpw_error_ref, wdtpw_error_dut;
    wire wdttmsel_ref, wdttmsel_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({nmi_evt_ref, per_dout_ref, wdtifg_set_ref, wdtpw_error_ref, wdttmsel_ref} === ({nmi_evt_ref, per_dout_ref, wdtifg_set_ref, wdtpw_error_ref, wdttmsel_ref} ^ {nmi_evt_dut, per_dout_dut, wdtifg_set_dut, wdtpw_error_dut, wdttmsel_dut} ^ {nmi_evt_ref, per_dout_ref, wdtifg_set_ref, wdtpw_error_ref, wdttmsel_ref}));

    // Instantiate the omsp_watchdog module
    omsp_watchdog_ref ref_model (
        .nmi_evt_ref(nmi_evt_ref),
        .per_dout_ref(per_dout_ref),
        .wdtifg_set_ref(wdtifg_set_ref),
        .wdtpw_error_ref(wdtpw_error_ref),
        .wdttmsel_ref(wdttmsel_ref),
        .aclk_en(aclk_en),
        .dbg_freeze(dbg_freeze),
        .mclk(mclk),
        .nmi(nmi),
        .nmie(nmie),
        .per_addr(per_addr),
        .per_din(per_din),
        .per_en(per_en),
        .per_wen(per_wen),
        .puc(puc),
        .smclk_en(smclk_en)
    );

    top dut (
        .nmi_evt(nmi_evt_dut),
        .per_dout(per_dout_dut),
        .wdtifg_set(wdtifg_set_dut),
        .wdtpw_error(wdtpw_error_dut),
        .wdttmsel(wdttmsel_dut),
        .aclk_en(aclk_en),
        .dbg_freeze(dbg_freeze),
        .mclk(mclk),
        .nmi(nmi),
        .nmie(nmie),
        .per_addr(per_addr),
        .per_din(per_din),
        .per_en(per_en),
        .per_wen(per_wen),
        .puc(puc),
        .smclk_en(smclk_en)
    );

    // Clock generation
    initial begin
        mclk = 0;
        forever #5 mclk = ~mclk; // 100MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        aclk_en = 0;
        dbg_freeze = 0;
        nmi = 0;
        nmie = 0;
        per_addr = 0;
        per_din = 0;
        per_en = 0;
        per_wen = 0;
        puc = 0;
        smclk_en = 0;

        // Test Case 1: Write to WDTCTL
        #10;
        per_en = 1;
        per_wen = 2'b11; // Write enable for both bytes
        per_addr = WDTCTL[7:0]; // Address for WDTCTL
        per_din = 16'h5A69; // Valid write value
        #10;
        per_en = 0;
        
        // Check outputs after write
        #10;
        compare();

        // Test Case 2: Trigger NMI event
        nmie = 1; // Enable NMI interrupt
        nmi = 1; // Trigger NMI
        #10;
        nmi = 0; // Deassert NMI

        // Check NMI event
        #10;
        compare();

        // Test Case 3: Write password error
        #10;
        per_en = 1;
        per_wen = 2'b11; // Write enable for both bytes
        per_addr = WDTCTL[7:0]; // Address for WDTCTL
        per_din = 16'h0000; // Incorrect write value
        #10;
        per_en = 0;

        // Check password error flag
        #10;
        compare();


        // Test Case 4: Clear watchdog counter
        #10;
        per_en = 1;
        per_wen = 2'b11; // Write enable for both bytes
        per_addr = WDTCTL[7:0]; // Address for WDTCTL
        per_din = 16'hD7; // Set clear bit
        #10;
        per_en = 0;

        // Check watchdog counter reset
        #10;
        compare();



        // Test Case 5: Watchdog timer increment
        smclk_en = 1; // Enable SMCLK
        #10;
            
        repeat (80) begin
            aclk_en = $random;
            dbg_freeze = $random;
            nmi = $random;
            nmie = $random;
            per_addr = 8'b10010000;
            per_din = $random;
            per_en = $random;
            per_wen = $random;
            puc = $random;
            smclk_en = $random;
            #10;
            compare();
        end

        repeat (16) begin
            aclk_en = $random;
            dbg_freeze = $random;
            nmi = $random;
            nmie = $random;
            per_addr = $random;
            per_din = $random;
            per_en = $random;
            per_wen = $random;
            puc = $random;
            smclk_en = $random;
            #10;
            compare();
        end


        // Finish simulation
        #10;
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
        $finish;
    end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("aclk_en = %b, dbg_freeze = %b, nmi = %b, nmie = %b, per_addr = %b, per_din = %b, per_en = %b, per_wen = %b, puc = %b, smclk_en = %b, nmi_evt_dut = %b, per_dout_dut = %b, wdtifg_set_dut = %b, wdtpw_error_dut = %b, wdttmsel_dut = %b, nmi_evt_ref = %b, per_dout_ref = %b, wdtifg_set_ref = %b, wdtpw_error_ref = %b, wdttmsel_ref = %b", aclk_en, dbg_freeze, nmi, nmie, per_addr, per_din, per_en, per_wen, puc, smclk_en, nmi_evt_dut, per_dout_dut, wdtifg_set_dut, wdtpw_error_dut, wdttmsel_dut, nmi_evt_ref, per_dout_ref, wdtifg_set_ref, wdtpw_error_ref, wdttmsel_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("aclk_en = %b, dbg_freeze = %b, nmi = %b, nmie = %b, per_addr = %b, per_din = %b, per_en = %b, per_wen = %b, puc = %b, smclk_en = %b, nmi_evt_dut = %b, per_dout_dut = %b, wdtifg_set_dut = %b, wdtpw_error_dut = %b, wdttmsel_dut = %b, nmi_evt_ref = %b, per_dout_ref = %b, wdtifg_set_ref = %b, wdtpw_error_ref = %b, wdttmsel_ref = %b", aclk_en, dbg_freeze, nmi, nmie, per_addr, per_din, per_en, per_wen, puc, smclk_en, nmi_evt_dut, per_dout_dut, wdtifg_set_dut, wdtpw_error_dut, wdttmsel_dut, nmi_evt_ref, per_dout_ref, wdtifg_set_ref, wdtpw_error_ref, wdttmsel_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end


endmodule
