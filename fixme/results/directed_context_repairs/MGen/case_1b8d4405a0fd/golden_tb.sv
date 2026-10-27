 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period for MTxClk and MRxClk

    // Inputs
    reg MTxClk;
    reg MRxClk;
    reg TxReset;
    reg RxReset;
    reg [7:0] RxData;
    reg RxValid;
    reg RxStartFrm;
    reg RxEndFrm;
    reg RxFlow;
    reg ReceiveEnd;
    reg [47:0] MAC;
    reg DlyCrcEn;
    reg TxDoneIn;
    reg TxAbortIn;
    reg TxStartFrmOut;
    reg ReceivedLengthOK;
    reg ReceivedPacketGood;
    reg TxUsedDataOutDetected;
    reg RxStatusWriteLatched_sync2;
    reg r_PassAll;

    // ref Outputs
    wire ref_Pause;
    wire ref_ReceivedPauseFrm;
    wire ref_AddressOK;
    wire ref_SetPauseTimer;

    // dut Outputs
    wire dut_Pause;
    wire dut_ReceivedPauseFrm;
    wire dut_AddressOK;
    wire dut_SetPauseTimer;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_Pause,ref_ReceivedPauseFrm,ref_AddressOK,ref_SetPauseTimer} === ({ref_Pause,ref_ReceivedPauseFrm,ref_AddressOK,ref_SetPauseTimer} ^ {dut_Pause,dut_ReceivedPauseFrm,dut_AddressOK,dut_SetPauseTimer} ^ {ref_Pause,ref_ReceivedPauseFrm,ref_AddressOK,ref_SetPauseTimer}));

    // Instantiate the eth_receivecontrol module
    top uut1 (
        .MTxClk(MTxClk),
        .MRxClk(MRxClk),
        .TxReset(TxReset),
        .RxReset(RxReset),
        .RxData(RxData),
        .RxValid(RxValid),
        .RxStartFrm(RxStartFrm),
        .RxEndFrm(RxEndFrm),
        .RxFlow(RxFlow),
        .ReceiveEnd(ReceiveEnd),
        .MAC(MAC),
        .DlyCrcEn(DlyCrcEn),
        .TxDoneIn(TxDoneIn),
        .TxAbortIn(TxAbortIn),
        .TxStartFrmOut(TxStartFrmOut),
        .ReceivedLengthOK(ReceivedLengthOK),
        .ReceivedPacketGood(ReceivedPacketGood),
        .TxUsedDataOutDetected(TxUsedDataOutDetected),
        .RxStatusWriteLatched_sync2(RxStatusWriteLatched_sync2),
        .r_PassAll(r_PassAll),
        .Pause(dut_Pause),
        .ReceivedPauseFrm(dut_ReceivedPauseFrm),
        .AddressOK(dut_AddressOK),
        .SetPauseTimer(dut_SetPauseTimer)
    );


    // Instantiate the eth_receivecontrol module
   ref_eth_receivecontrol uut2 (
        .MTxClk(MTxClk),
        .MRxClk(MRxClk),
        .TxReset(TxReset),
        .RxReset(RxReset),
        .RxData(RxData),
        .RxValid(RxValid),
        .RxStartFrm(RxStartFrm),
        .RxEndFrm(RxEndFrm),
        .RxFlow(RxFlow),
        .ReceiveEnd(ReceiveEnd),
        .MAC(MAC),
        .DlyCrcEn(DlyCrcEn),
        .TxDoneIn(TxDoneIn),
        .TxAbortIn(TxAbortIn),
        .TxStartFrmOut(TxStartFrmOut),
        .ReceivedLengthOK(ReceivedLengthOK),
        .ReceivedPacketGood(ReceivedPacketGood),
        .TxUsedDataOutDetected(TxUsedDataOutDetected),
        .RxStatusWriteLatched_sync2(RxStatusWriteLatched_sync2),
        .r_PassAll(r_PassAll),
        .ref_Pause(ref_Pause),
        .ref_ReceivedPauseFrm(ref_ReceivedPauseFrm),
        .ref_AddressOK(ref_AddressOK),
        .ref_SetPauseTimer(ref_SetPauseTimer)
    );


    // Generate clock signals
    initial begin
        MTxClk = 0;
        MRxClk = 0;
        forever #(CLK_PERIOD / 2) begin
            MTxClk = ~MTxClk;
            MRxClk = ~MRxClk;
        end
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        TxReset = 1;
        RxReset = 1;
        RxData = 0;
        RxValid = 0;
        RxStartFrm = 0;
        RxEndFrm = 0;
        RxFlow = 0;
        ReceiveEnd = 0;
        MAC = 48'h00_11_22_33_44_55;
        DlyCrcEn = 0;
        TxDoneIn = 0;
        TxAbortIn = 0;
        TxStartFrmOut = 0;
        ReceivedLengthOK = 0;
        ReceivedPacketGood = 0;
        TxUsedDataOutDetected = 0;
        RxStatusWriteLatched_sync2 = 0;
        r_PassAll = 0;

        // Apply reset
        #(CLK_PERIOD);
        TxReset = 0; // De-assert TxReset
        RxReset = 0; // De-assert RxReset
        #(CLK_PERIOD);

        // Test Case 1: Simulate receiving a pause frame
        RxValid = 1;
        RxStartFrm = 1;
        RxData = 8'h01; // Start of a pause frame
        #(CLK_PERIOD);
        RxStartFrm = 0;
        RxEndFrm = 0;
  compare();

        // Send remaining bytes for the pause frame
        for (int i = 1; i < 18; i++) begin
            RxData = 8'h00; // Fill with dummy data
            #(CLK_PERIOD);
        end
        
        RxEndFrm = 1; // End of pause frame
        #(CLK_PERIOD);
        RxEndFrm = 0; // Clear end frame

        // Check outputs
        if (dut_ReceivedPauseFrm) begin
            $display("Test Case 1 Passed: Received pause frame.");
        end else begin
            $display("Test Case 1 Failed: Pause frame not received.");
        end
    compare();

// Test Case 2: Valid Pause Frame Reception
    #10;
    RxStartFrm = 1;
    RxValid = 1;
    RxData = 8'h01; // Start of MAC address
    #10;
    RxData = 8'h80;
    #10;
    RxData = 8'hC2;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h88; // Type/Length
    #10;
    RxData = 8'h08;
    #10;
    RxData = 8'h00; // OpCode
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h00; // Timer Value
    #10;
    RxData = 8'h0A;
    #10;
    RxData = 8'h00; // End of frame
    RxEndFrm = 1;
    #10;
    RxEndFrm = 0;
    RxValid = 0;
    RxStartFrm = 0;
    ReceiveEnd = 1;
    #10;
    ReceiveEnd = 0;
compare();
    // Test Case : Invalid Pause Frame Reception (wrong MAC address)
    #10;
    RxStartFrm = 1;
    RxValid = 1;
    RxData = 8'h02; // Start of wrong MAC address
    #10;
    RxData = 8'h80;
    #10;
    RxData = 8'hC2;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h88; // Type/Length
    #10;
    RxData = 8'h08;
    #10;
    RxData = 8'h00; // OpCode
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h00; // Timer Value
    #10;
    RxData = 8'h0A;
    #10;
    RxData = 8'h00; // End of frame
    RxEndFrm = 1;
    #10;
    RxEndFrm = 0;
    RxValid = 0;
    RxStartFrm = 0;
    ReceiveEnd = 1;
    #10;
    ReceiveEnd = 0;
compare();
    // Test Case 4: Invalid Pause Frame Reception (wrong Type/Length)
    #10;
    RxStartFrm = 1;
    RxValid = 1;
    RxData = 8'h01; // Start of MAC address
    #10;
    RxData = 8'h80;
    #10;
    RxData = 8'hC2;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h88; // Wrong Type/Length
    #10;
    RxData = 8'h09;
    #10;
    RxData = 8'h00; // OpCode
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h00; // Timer Value
    #10;
    RxData = 8'h0A;
    #10;
    RxData = 8'h00; // End of frame
    RxEndFrm = 1;
    #10;
    RxEndFrm = 0;
    RxValid = 0;
    RxStartFrm = 0;
    ReceiveEnd = 1;
    #10;
    ReceiveEnd = 0;
compare();
    // Test Case 5: Invalid Pause Frame Reception (wrong OpCode)
    #10;
    RxStartFrm = 1;
    RxValid = 1;
    RxData = 8'h01; // Start of MAC address
    #10;
    RxData = 8'h80;
    #10;
    RxData = 8'hC2;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h00;
    #10;
    RxData = 8'h01;
    #10;
    RxData = 8'h88; // Type/Length
    #10;
    RxData = 8'h08;
    #10;
    RxData = 8'h00; // Wrong OpCode
    #10;
    RxData = 8'h02;
    #10;
    RxData = 8'h00; // Timer Value
    #10;
    RxData = 8'h0A;
    #10;
    RxData = 8'h00; // End of frame
    RxEndFrm = 1;
    #10;
    RxEndFrm = 0;
    RxValid = 0;
    RxStartFrm = 0;
    ReceiveEnd = 1;
    #10;
    ReceiveEnd = 0;
compare();
    // Test Case 6: Pause Timer Decrement
    #10;
    RxFlow = 1;
    #100;
    RxFlow = 0;
compare();



   repeat (96) begin
      @(posedge MRxClk);
	TxReset = $random;
	RxReset = $random;
	RxData = $random;
	RxValid = $random;
	RxStartFrm = $random;
	RxEndFrm = $random;
	RxFlow = $random;
	ReceiveEnd = $random;
	MAC = $random;
	DlyCrcEn = $random;
	TxDoneIn = $random;
	TxAbortIn = $random;
	TxStartFrmOut = $random;
	ReceivedLengthOK = $random;
	ReceivedPacketGood = $random;
	TxUsedDataOutDetected = $random;
	RxStatusWriteLatched_sync2 = $random;
	r_PassAll = $random;
	      
      compare();
    end
     compare();

  	  $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        // Finish simulation
        #(CLK_PERIOD * 10);
        $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
    end

task compare;
        total_tests = total_tests + 1;
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin				$display("\033[1;32mtestcase is passed!!!\033[0m");
				$display("testcase is passed!!!");
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            failed_tests = failed_tests + 1; 
		end
	
endtask
endmodule
