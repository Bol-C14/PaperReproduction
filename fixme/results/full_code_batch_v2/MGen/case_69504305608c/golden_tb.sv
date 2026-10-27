`timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // 100 MHz clock

    // Inputs
    reg MTxClk;
    reg TxReset;
    reg TxUsedDataIn;
    reg TxUsedDataOut;
    reg TxDoneIn;
    reg TxAbortIn;
    reg TxStartFrmIn;
    reg TPauseRq;
    reg TxUsedDataOutDetected;
    reg TxFlow;
    reg DlyCrcEn;
    reg [15:0] TxPauseTV;
    reg [47:0] MAC;

    // Outputs
    wire ref_TxCtrlStartFrm,dut_TxCtrlStartFrm;
    wire ref_TxCtrlEndFrm,dut_TxCtrlEndFrm;
    wire ref_SendingCtrlFrm,dut_SendingCtrlFrm;
    wire ref_CtrlMux,dut_CtrlMux;
    wire [7:0] ref_ControlData,dut_ControlData;
    wire ref_WillSendControlFrame,dut_WillSendControlFrame;
    wire ref_BlockTxDone,dut_BlockTxDone;

    wire match;

    integer total_tests = 0;
    integer failed_tests = 0;

assign match = ({ref_TxCtrlStartFrm,ref_TxCtrlEndFrm,ref_SendingCtrlFrm,ref_CtrlMux,ref_ControlData,ref_WillSendControlFrame,ref_BlockTxDone} === ({ref_TxCtrlStartFrm,ref_TxCtrlEndFrm,ref_SendingCtrlFrm,ref_CtrlMux,ref_ControlData,ref_WillSendControlFrame,ref_BlockTxDone} ^ {dut_TxCtrlStartFrm,dut_TxCtrlEndFrm,dut_SendingCtrlFrm,dut_CtrlMux,dut_ControlData,dut_WillSendControlFrame,dut_BlockTxDone} ^ {ref_TxCtrlStartFrm,ref_TxCtrlEndFrm,ref_SendingCtrlFrm,ref_CtrlMux,ref_ControlData,ref_WillSendControlFrame,ref_BlockTxDone}));

    // Instantiate the eth_transmitcontrol module
    ref_eth_transmitcontrol ref_modle(
        .MTxClk(MTxClk),
        .TxReset(TxReset),
        .TxUsedDataIn(TxUsedDataIn),
        .TxUsedDataOut(TxUsedDataOut),
        .TxDoneIn(TxDoneIn),
        .TxAbortIn(TxAbortIn),
        .TxStartFrmIn(TxStartFrmIn),
        .TPauseRq(TPauseRq),
        .TxUsedDataOutDetected(TxUsedDataOutDetected),
        .TxFlow(TxFlow),
        .DlyCrcEn(DlyCrcEn),
        .TxPauseTV(TxPauseTV),
        .MAC(MAC),
        .ref_TxCtrlStartFrm(ref_TxCtrlStartFrm),
        .ref_TxCtrlEndFrm(ref_TxCtrlEndFrm),
        .ref_SendingCtrlFrm(ref_SendingCtrlFrm),
        .ref_CtrlMux(ref_CtrlMux),
        .ref_ControlData(ref_ControlData),
        .ref_WillSendControlFrame(ref_WillSendControlFrame),
        .ref_BlockTxDone(ref_BlockTxDone)
    );

    top uut (
        .MTxClk(MTxClk),
        .TxReset(TxReset),
        .TxUsedDataIn(TxUsedDataIn),
        .TxUsedDataOut(TxUsedDataOut),
        .TxDoneIn(TxDoneIn),
        .TxAbortIn(TxAbortIn),
        .TxStartFrmIn(TxStartFrmIn),
        .TPauseRq(TPauseRq),
        .TxUsedDataOutDetected(TxUsedDataOutDetected),
        .TxFlow(TxFlow),
        .DlyCrcEn(DlyCrcEn),
        .TxPauseTV(TxPauseTV),
        .MAC(MAC),
        .TxCtrlStartFrm(dut_TxCtrlStartFrm),
        .TxCtrlEndFrm(dut_TxCtrlEndFrm),
        .SendingCtrlFrm(dut_SendingCtrlFrm),
        .CtrlMux(dut_CtrlMux),
        .ControlData(dut_ControlData),
        .WillSendControlFrame(dut_WillSendControlFrame),
        .BlockTxDone(dut_BlockTxDone)
    );
    // Clock generation
    initial begin
        MTxClk = 0;
        forever #(CLK_PERIOD / 2) MTxClk = ~MTxClk; // Toggle clock
    end

    // Reference model to verify DUT outputs
    //reg ref_WillSendControlFrame;
   // reg ref_TxCtrlEndFrm;
    //reg ref_SendingCtrlFrm;
    //reg [7:0] ref_ControlData;

    //always @(posedge MTxClk) begin
      //  if (!TxReset) begin
      //      ref_WillSendControlFrame <= 0;
       ///     ref_TxCtrlEndFrm <= 0;
       //     ref_SendingCtrlFrm <= 0;
       //     ref_ControlData <= 0;
       // end else begin
        //    if (TPauseRq && TxStartFrmIn) begin
       //         ref_WillSendControlFrame <= 1;
        //        ref_SendingCtrlFrm <= 1;
       //     end
        //    if (TxDoneIn) begin
        //        ref_TxCtrlEndFrm <= 1;
        //        ref_SendingCtrlFrm <= 0;
         //   end
         //   if (TxAbortIn) begin
        //        ref_SendingCtrlFrm <= 0;
        ////    end
         //   if (TxUsedDataIn) begin
         ///       ref_ControlData <= 8'h01; // Example control data
         //   end
       // end
   // end

    // Test Procedure
    initial begin
        // Initialize inputs
        TxReset = 1;
        TxUsedDataIn = 0;
        TxUsedDataOut = 0;
        TxDoneIn = 0;
        TxAbortIn = 0;
        TxStartFrmIn = 0;
        TPauseRq = 0;
        TxUsedDataOutDetected = 0;
        TxFlow = 0;
        DlyCrcEn = 0;
        TxPauseTV = 16'h0000;
        MAC = 48'h00_11_22_33_44_55;

        // Wait for a clock cycle
        #(CLK_PERIOD * 2);

        // Test Case 1: Reset the module
 	@(posedge MTxClk);
        TxReset = 0;
        #(CLK_PERIOD);
        TxReset = 1; // Assert reset
        #(CLK_PERIOD);
        TxReset = 0; // Deassert reset
	compare();

        // Test Case 2: Start Control Frame Transmission
	@(posedge MTxClk);
        TxFlow = 1;
        TPauseRq = 1;
        #(CLK_PERIOD);
        TxStartFrmIn = 1; // Start frame input
        #(CLK_PERIOD);
        TxStartFrmIn = 0;
	compare();

        // Wait for a clock cycle
        #(CLK_PERIOD * 5);

        // Check outputs
        if (dut_WillSendControlFrame !== ref_WillSendControlFrame) begin
            $display("Test Case 2 Failed: Expected WillSendControlFrame = %b, got %b", ref_WillSendControlFrame,dut_WillSendControlFrame);
        end

        // Test Case 3: End Control Frame Transmission
	@(posedge MTxClk);
        TxDoneIn = 1; // Indicate transmission done
        #(CLK_PERIOD);
        TxDoneIn = 0;
	compare();

        // Wait for a clock cycle
        #(CLK_PERIOD * 2);

        // Check outputs
        if (dut_TxCtrlEndFrm !== ref_TxCtrlEndFrm) begin
            $display("Test Case 3 Failed: Expected TxCtrlEndFrm = %b, got %b", dut_TxCtrlEndFrm, ref_TxCtrlEndFrm);
        end

        // Test Case 4: Control Frame Sending State
	@(posedge MTxClk);
        if (dut_SendingCtrlFrm !== ref_SendingCtrlFrm) begin
            $display("Test Case 4 Failed: Expected SendingCtrlFrm = %b, got %b", dut_SendingCtrlFrm, ref_SendingCtrlFrm);
        end
	compare();

        // Test Case 5: Abort Transmission
	@(posedge MTxClk);
        TxAbortIn = 1; // Abort the transmission
        #(CLK_PERIOD);
        TxAbortIn = 0;
	compare();

        // Wait for a clock cycle
        #(CLK_PERIOD * 2);

        // Check outputs after abort
        if (dut_SendingCtrlFrm !== ref_SendingCtrlFrm) begin
            $display("Test Case 5 Failed: Expected SendingCtrlFrm = %b after abort, got %b", dut_SendingCtrlFrm, ref_SendingCtrlFrm);
        end

        // Test Case 6: Check ControlData output
	@(posedge MTxClk);
        TxUsedDataIn = 1; // Simulate data input
        #(CLK_PERIOD);
        if (dut_ControlData !== ref_ControlData) begin
            $display("Test Case 6 Failed: Expected ControlData = %h, got %h", ref_ControlData, dut_ControlData);
        end
	compare();

repeat (96) begin
            @(negedge MTxClk);
     TxUsedDataIn = $random;
     TxUsedDataOut = $random;
     TxDoneIn = $random;
     TxAbortIn = $random;
     TxStartFrmIn = $random;
     TPauseRq = $random;
     TxUsedDataOutDetected = $random;
     TxFlow = $random;
     DlyCrcEn = $random;
     TxPauseTV = $random ;
     MAC = {$random,$random};
            #10;
            compare();
        end
	$display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        // Finish simulation
        #(CLK_PERIOD * 10);
        $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
    end

    task compare;
        total_tests = total_tests + 1;
        //wait (o_valid_dut == 1);
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
				$display("testcase is passed!!!");
            	//$display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            //$display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

endmodule
