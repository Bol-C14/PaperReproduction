 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter IW = 24;

    // Testbench signals
    reg rDLY;
    reg [15:0] rIMM;
    reg [10:0] rALT;
    reg [5:0] rOPC;
    reg [4:0] rRD, rRA, rRB;
    reg [31:2] rPC;
    reg rBRA;
    reg rMSR_IE;
    reg [31:0] xIREG;
    reg dwb_ack_i, iwb_ack_i, fsl_ack_i;
    reg gclk, grst, gena;

    // Outputs
    wire [1:0] rMXDST_ref, rMXDST_dut;
    wire [1:0] rMXSRC_ref, rMXSRC_dut, rMXTGT_ref, rMXTGT_dut, rMXALT_ref, rMXALT_dut;
    wire [2:0] rMXALU_ref, rMXALU_dut;   
    wire [4:0] rRW_ref, rRW_dut;
    wire dwb_stb_o_ref, dwb_stb_o_dut;
    wire dwb_wre_o_ref, dwb_wre_o_dut;
    wire fsl_stb_o_ref, fsl_stb_o_dut;
    wire fsl_wre_o_ref, fsl_wre_o_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({rMXDST_ref, rMXSRC_ref, rMXTGT_ref, rMXALT_ref, rMXALU_ref, rRW_ref, dwb_stb_o_ref, dwb_wre_o_ref, fsl_stb_o_ref, fsl_wre_o_ref} === ({rMXDST_ref, rMXSRC_ref, rMXTGT_ref, rMXALT_ref, rMXALU_ref, rRW_ref, dwb_stb_o_ref, dwb_wre_o_ref, fsl_stb_o_ref, fsl_wre_o_ref} ^ {rMXDST_dut, rMXSRC_dut, rMXTGT_dut, rMXALT_dut, rMXALU_dut, rRW_dut, dwb_stb_o_dut, dwb_wre_o_dut, fsl_stb_o_dut, fsl_wre_o_dut} ^ {rMXDST_ref, rMXSRC_ref, rMXTGT_ref, rMXALT_ref, rMXALU_ref, rRW_ref, dwb_stb_o_ref, dwb_wre_o_ref, fsl_stb_o_ref, fsl_wre_o_ref}));

    // Instantiate the aeMB_ctrl module
    aeMB_ctrl_ref ref_model (
        .rMXDST_ref(rMXDST_ref),
        .rMXSRC_ref(rMXSRC_ref),
        .rMXTGT_ref(rMXTGT_ref),
        .rMXALT_ref(rMXALT_ref),
        .rMXALU_ref(rMXALU_ref),   
        .rRW_ref(rRW_ref),
        .dwb_stb_o_ref(dwb_stb_o_ref),
        .dwb_wre_o_ref(dwb_wre_o_ref),
        .fsl_stb_o_ref(fsl_stb_o_ref),
        .fsl_wre_o_ref(fsl_wre_o_ref),
        .rDLY(rDLY),
        .rIMM(rIMM),
        .rALT(rALT),
        .rOPC(rOPC),
        .rRD(rRD),
        .rRA(rRA),
        .rRB(rRB),
        .rPC(rPC),
        .rBRA(rBRA),
        .rMSR_IE(rMSR_IE),
        .xIREG(xIREG),   
        .dwb_ack_i(dwb_ack_i),
        .iwb_ack_i(iwb_ack_i),
        .fsl_ack_i(fsl_ack_i),   
        .gclk(gclk),
        .grst(grst),
        .gena(gena)
    );
    top dut (
        .rMXDST(rMXDST_dut),
        .rMXSRC(rMXSRC_dut),
        .rMXTGT(rMXTGT_dut),
        .rMXALT(rMXALT_dut),
        .rMXALU(rMXALU_dut),   
        .rRW(rRW_dut),
        .dwb_stb_o(dwb_stb_o_dut),
        .dwb_wre_o(dwb_wre_o_dut),
        .fsl_stb_o(fsl_stb_o_dut),
        .fsl_wre_o(fsl_wre_o_dut),
        .rDLY(rDLY),
        .rIMM(rIMM),
        .rALT(rALT),
        .rOPC(rOPC),
        .rRD(rRD),
        .rRA(rRA),
        .rRB(rRB),
        .rPC(rPC),
        .rBRA(rBRA),
        .rMSR_IE(rMSR_IE),
        .xIREG(xIREG),   
        .dwb_ack_i(dwb_ack_i),
        .iwb_ack_i(iwb_ack_i),
        .fsl_ack_i(fsl_ack_i),   
        .gclk(gclk),
        .grst(grst),
        .gena(gena)
    );

    // Clock generation
    initial begin
        gclk = 0;
        forever #5 gclk = ~gclk; // 100 MHz clock
    end

    // Test procedure
    initial begin
        // Initialize signals
        grst = 1;
        gena = 0;
        rDLY = 0;
        rIMM = 0;
        rALT = 0;
        rOPC = 0;
        rRD = 0;
        rRA = 0;
        rRB = 0;
        rPC = 0;
        rBRA = 0;
        rMSR_IE = 0;
        xIREG = 0;
        dwb_ack_i = 0;
        iwb_ack_i = 0;
        fsl_ack_i = 0;

        // Release reset
        #10;
        grst = 0;

        // Test Case 1: Test with different OPC values
        @(posedge gclk);
        rOPC = 6'o55; // RTD instruction
        rRD = 5'b00001; // Register 1
        rRA = 5'b00010; // Register 2
        rRB = 5'b00011; // Register 3
        xIREG = {rOPC, rRD, rRA, rRB, rALT}; // Set values
        gena = 1; // Enable
        // Wait for a clock cycle
        @(posedge gclk);
        compare();

        // Test Case 2: Test with BCC instruction
        rOPC = 6'o47; // BCC instruction
        xIREG = {rOPC, rRD, rRA, rRB, rALT};
        // Wait for a clock cycle
        @(posedge gclk);
        compare();

        // Test Case 3: Test with STR instruction
        rOPC = 6'o54; // STR instruction
        rBRA = 0; // No branch
        xIREG = {rOPC, rRD, rRA, rRB, rALT};
        // Wait for a clock cycle
        @(posedge gclk);
        compare();

        // Test Case 4: Check DWB signals
        rOPC = 6'o44;
        dwb_ack_i = 1; // Simulate DWB acknowledgment
        @(posedge gclk);
        compare();

        // Test Case 5: Check FSL signals
        fsl_ack_i = 1; // Simulate FSL acknowledgment
        @(posedge gclk);
        compare();

        rRA = 5'b11111;
        rOPC = 6'o46;
        @(posedge gclk);
        compare();
        rOPC = 6'o33;
        rRB = 5'b01111;

        @(posedge gclk);
        compare();

        iwb_ack_i = 1;
        fsl_ack_i = 0;
        rRB = 5'b11111;
        @(posedge gclk);
        @(posedge gclk);
        compare();        


        repeat (690) begin
            gena = $random;
            rDLY = $random;
            rIMM = $random;
            rALT = $random;
            rOPC = $random;
            rRD = $random;
            rRA = $random;
            rRB = $random;
            rPC = $random;
            rBRA = $random;
            rMSR_IE = $random;
            xIREG = $random;
            dwb_ack_i = $random;
            iwb_ack_i = $random;
            fsl_ack_i = $random;
            @(posedge gclk);
            compare();
        end

        // Test Case 6: Check default reset behavior
        grst = 1;
        @(posedge gclk);
        compare();
        @(posedge gclk);
        compare();        

        // Finish simulation
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
            	$display("grst = %h, gena = %h, rDLY = %h, rIMM = %h, rALT = %h, rOPC = %h, rRD = %h, rRA = %h, rRB = %h, rPC = %h, rBRA = %h, rMSR_IE = %h, xIREG = %h, dwb_ack_i = %h, iwb_ack_i = %h, fsl_ack_i = %h, rMXDST_dut = %h, rMXSRC_dut = %h, rMXTGT_dut = %h, rMXALT_dut = %h, rMXALU_dut = %h, rRW_dut = %h, dwb_stb_o_dut = %h, dwb_wre_o_dut = %h, fsl_stb_o_dut = %h, fsl_wre_o_dut = %h, rMXDST_ref = %h, rMXSRC_ref = %h, rMXTGT_ref = %h, rMXALT_ref = %h, rMXALU_ref = %h, rRW_ref = %h, dwb_stb_o_ref = %h, dwb_wre_o_ref = %h, fsl_stb_o_ref = %h, fsl_wre_o_ref = %h", grst, gena, rDLY, rIMM, rALT, rOPC, rRD, rRA, rRB, rPC, rBRA, rMSR_IE, xIREG, dwb_ack_i, iwb_ack_i, fsl_ack_i, rMXDST_dut, rMXSRC_dut, rMXTGT_dut, rMXALT_dut, rMXALU_dut, rRW_dut, dwb_stb_o_dut, dwb_wre_o_dut, fsl_stb_o_dut, fsl_wre_o_dut, rMXDST_ref, rMXSRC_ref, rMXTGT_ref, rMXALT_ref, rMXALU_ref, rRW_ref, dwb_stb_o_ref, dwb_wre_o_ref, fsl_stb_o_ref, fsl_wre_o_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("grst = %h, gena = %h, rDLY = %h, rIMM = %h, rALT = %h, rOPC = %h, rRD = %h, rRA = %h, rRB = %h, rPC = %h, rBRA = %h, rMSR_IE = %h, xIREG = %h, dwb_ack_i = %h, iwb_ack_i = %h, fsl_ack_i = %h, rMXDST_dut = %h, rMXSRC_dut = %h, rMXTGT_dut = %h, rMXALT_dut = %h, rMXALU_dut = %h, rRW_dut = %h, dwb_stb_o_dut = %h, dwb_wre_o_dut = %h, fsl_stb_o_dut = %h, fsl_wre_o_dut = %h, rMXDST_ref = %h, rMXSRC_ref = %h, rMXTGT_ref = %h, rMXALT_ref = %h, rMXALU_ref = %h, rRW_ref = %h, dwb_stb_o_ref = %h, dwb_wre_o_ref = %h, fsl_stb_o_ref = %h, fsl_wre_o_ref = %h", grst, gena, rDLY, rIMM, rALT, rOPC, rRD, rRA, rRB, rPC, rBRA, rMSR_IE, xIREG, dwb_ack_i, iwb_ack_i, fsl_ack_i, rMXDST_dut, rMXSRC_dut, rMXTGT_dut, rMXALT_dut, rMXALU_dut, rRW_dut, dwb_stb_o_dut, dwb_wre_o_dut, fsl_stb_o_dut, fsl_wre_o_dut, rMXDST_ref, rMXSRC_ref, rMXTGT_ref, rMXALT_ref, rMXALU_ref, rRW_ref, dwb_stb_o_ref, dwb_wre_o_ref, fsl_stb_o_ref, fsl_wre_o_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

