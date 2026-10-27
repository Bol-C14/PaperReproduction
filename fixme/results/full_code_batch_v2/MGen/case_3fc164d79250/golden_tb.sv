`timescale 1ns / 1ps

module tb;

    // Parameters
    parameter DP_HAZARDS_WIDTH = 8;
    parameter REG_ADDR_WIDTH = 5;

    // Inputs
    reg [DP_HAZARDS_WIDTH-1:0] DP_Hazards;
    reg [REG_ADDR_WIDTH-1:0] ID_Rs;
    reg [REG_ADDR_WIDTH-1:0] ID_Rt;
    reg [REG_ADDR_WIDTH-1:0] EX_Rs;
    reg [REG_ADDR_WIDTH-1:0] EX_Rt;
    reg [REG_ADDR_WIDTH-1:0] EX_RtRd;
    reg [REG_ADDR_WIDTH-1:0] MEM_RtRd;
    reg [REG_ADDR_WIDTH-1:0] WB_RtRd;
    reg EX_Link;
    reg EX_RegWrite;
    reg MEM_RegWrite;
    reg WB_RegWrite;
    reg MEM_MemRead;
    reg MEM_MemWrite;        
    reg InstMem_Read;
    reg InstMem_Ready;
    reg Mfc0;                
    reg IF_Exception_Stall;
    reg ID_Exception_Stall;
    reg EX_Exception_Stall;
    reg EX_ALU_Stall;
    reg M_Stall_Controller;  

    // Outputs
    wire IF_Stall_ref, IF_Stall_dut;
    wire ID_Stall_ref, ID_Stall_dut;
    wire EX_Stall_ref, EX_Stall_dut;
    wire M_Stall_ref, M_Stall_dut;
    wire WB_Stall_ref, WB_Stall_dut;
    wire [1:0] ID_RsFwdSel_ref, ID_RsFwdSel_dut;
    wire [1:0] ID_RtFwdSel_ref, ID_RtFwdSel_dut;
    wire [1:0] EX_RsFwdSel_ref, EX_RsFwdSel_dut;
    wire [1:0] EX_RtFwdSel_ref, EX_RtFwdSel_dut;
    wire M_WriteDataFwdSel_ref, M_WriteDataFwdSel_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({IF_Stall_ref, ID_Stall_ref, EX_Stall_ref, M_Stall_ref, WB_Stall_ref, ID_RsFwdSel_ref, ID_RtFwdSel_ref, EX_RsFwdSel_ref, EX_RtFwdSel_ref, M_WriteDataFwdSel_ref} === ({IF_Stall_ref, ID_Stall_ref, EX_Stall_ref, M_Stall_ref, WB_Stall_ref, ID_RsFwdSel_ref, ID_RtFwdSel_ref, EX_RsFwdSel_ref, EX_RtFwdSel_ref, M_WriteDataFwdSel_ref} ^ {IF_Stall_dut, ID_Stall_dut, EX_Stall_dut, M_Stall_dut, WB_Stall_dut, ID_RsFwdSel_dut, ID_RtFwdSel_dut, EX_RsFwdSel_dut, EX_RtFwdSel_dut, M_WriteDataFwdSel_dut} ^ {IF_Stall_ref, ID_Stall_ref, EX_Stall_ref, M_Stall_ref, WB_Stall_ref, ID_RsFwdSel_ref, ID_RtFwdSel_ref, EX_RsFwdSel_ref, EX_RtFwdSel_ref, M_WriteDataFwdSel_ref}));

    // Instantiate the Hazard_Detection module
    Hazard_Detection_ref ref_model (
        .DP_Hazards(DP_Hazards),
        .ID_Rs(ID_Rs),
        .ID_Rt(ID_Rt),
        .EX_Rs(EX_Rs),
        .EX_Rt(EX_Rt),
        .EX_RtRd(EX_RtRd),
        .MEM_RtRd(MEM_RtRd),
        .WB_RtRd(WB_RtRd),
        .EX_Link(EX_Link),
        .EX_RegWrite(EX_RegWrite),
        .MEM_RegWrite(MEM_RegWrite),
        .WB_RegWrite(WB_RegWrite),
        .MEM_MemRead(MEM_MemRead),
        .MEM_MemWrite(MEM_MemWrite),        
        .InstMem_Read(InstMem_Read),
        .InstMem_Ready(InstMem_Ready),
        .Mfc0(Mfc0),                
        .IF_Exception_Stall(IF_Exception_Stall),
        .ID_Exception_Stall(ID_Exception_Stall),
        .EX_Exception_Stall(EX_Exception_Stall),
        .EX_ALU_Stall(EX_ALU_Stall),
        .M_Stall_Controller(M_Stall_Controller),  
        .IF_Stall_ref(IF_Stall_ref),
        .ID_Stall_ref(ID_Stall_ref),
        .EX_Stall_ref(EX_Stall_ref),
        .M_Stall_ref(M_Stall_ref),
        .WB_Stall_ref(WB_Stall_ref),
        .ID_RsFwdSel_ref(ID_RsFwdSel_ref),
        .ID_RtFwdSel_ref(ID_RtFwdSel_ref),
        .EX_RsFwdSel_ref(EX_RsFwdSel_ref),
        .EX_RtFwdSel_ref(EX_RtFwdSel_ref),
        .M_WriteDataFwdSel_ref(M_WriteDataFwdSel_ref)
    );

    top dut (
        .DP_Hazards(DP_Hazards),
        .ID_Rs(ID_Rs),
        .ID_Rt(ID_Rt),
        .EX_Rs(EX_Rs),
        .EX_Rt(EX_Rt),
        .EX_RtRd(EX_RtRd),
        .MEM_RtRd(MEM_RtRd),
        .WB_RtRd(WB_RtRd),
        .EX_Link(EX_Link),
        .EX_RegWrite(EX_RegWrite),
        .MEM_RegWrite(MEM_RegWrite),
        .WB_RegWrite(WB_RegWrite),
        .MEM_MemRead(MEM_MemRead),
        .MEM_MemWrite(MEM_MemWrite),        
        .InstMem_Read(InstMem_Read),
        .InstMem_Ready(InstMem_Ready),
        .Mfc0(Mfc0),                
        .IF_Exception_Stall(IF_Exception_Stall),
        .ID_Exception_Stall(ID_Exception_Stall),
        .EX_Exception_Stall(EX_Exception_Stall),
        .EX_ALU_Stall(EX_ALU_Stall),
        .M_Stall_Controller(M_Stall_Controller),  
        .IF_Stall(IF_Stall_dut),
        .ID_Stall(ID_Stall_dut),
        .EX_Stall(EX_Stall_dut),
        .M_Stall(M_Stall_dut),
        .WB_Stall(WB_Stall_dut),
        .ID_RsFwdSel(ID_RsFwdSel_dut),
        .ID_RtFwdSel(ID_RtFwdSel_dut),
        .EX_RsFwdSel(EX_RsFwdSel_dut),
        .EX_RtFwdSel(EX_RtFwdSel_dut),
        .M_WriteDataFwdSel(M_WriteDataFwdSel_dut)
    );

    // Test procedure
    initial begin
        // Initialize inputs
        DP_Hazards = 8'b00000000;
        ID_Rs = 5'b00000;
        ID_Rt = 5'b00000;
        EX_Rs = 5'b00000;
        EX_Rt = 5'b00000;
        EX_RtRd = 5'b00000;
        MEM_RtRd = 5'b00000;
        WB_RtRd = 5'b00000;
        EX_Link = 0;
        EX_RegWrite = 0;
        MEM_RegWrite = 0;
        WB_RegWrite = 0;
        MEM_MemRead = 0;
        MEM_MemWrite = 0;        
        InstMem_Read = 0;
        InstMem_Ready = 0;
        Mfc0 = 0;                
        IF_Exception_Stall = 0;
        ID_Exception_Stall = 0;
        EX_Exception_Stall = 0;
        EX_ALU_Stall = 0;
        M_Stall_Controller = 0;  

        // Test Case 1: No hazards

        // Test Case 2: ID hazard with EX_RegWrite
        #10;
        DP_Hazards = 8'b11000000; // WantRsByID and NeedRsByID
        ID_Rs = 5'b00001;
        EX_RtRd = 5'b00001;
        EX_RegWrite = 1;
        
        #10;
        compare();

        // Test Case 3: Memory hazard with MEM_RegWrite
        DP_Hazards = 8'b00110000; // WantRtByID and NeedRtByID
        ID_Rt = 5'b00010;
        MEM_RtRd = 5'b00010;
        MEM_RegWrite = 1;
        MEM_MemRead = 1;

        #10;
        compare();

        // Test Case 4: EX hazard with EX_RegWrite

        DP_Hazards = 8'b00001100; // WantRsByEX and NeedRsByEX
        EX_Rs = 5'b00011;
        EX_RtRd = 5'b00011;
        EX_RegWrite = 1;

        #10;
        compare();

        // Test Case 5: Forwarding from MEM
        #10;
        DP_Hazards = 8'b00000001; // WantRtByEX
        MEM_RtRd = 5'b00010;
        MEM_RegWrite = 1;

        #10;
        compare();

        // Test Case 6: Exception stalls
        #10;
        IF_Exception_Stall = 1;
        ID_Exception_Stall = 1;

        #10;
        compare();
        ID_Rs = 1;
        EX_Rs = 1;
        EX_Rt = 1;
        MEM_RtRd = 1;
        DP_Hazards = 8'b11111111;
        MEM_MemRead = 0;
        MEM_MemWrite = 0; 
        EX_RegWrite = 1;
        MEM_RegWrite = 1;
        WB_RtRd = 0;

        #10;
        compare();
        MEM_MemRead = 1;

        #10;
        compare();





        repeat (93) begin
            DP_Hazards = $random;
            ID_Rs = $random;
            ID_Rt = $random;
            EX_Rs = $random;
            EX_Rt = $random;
            EX_RtRd = $random;
            MEM_RtRd = $random;
            WB_RtRd = $random;
            EX_Link = $random;
            EX_RegWrite = $random;
            MEM_RegWrite = $random;
            WB_RegWrite = $random;
            MEM_MemRead = $random;
            MEM_MemWrite = $random;        
            InstMem_Read = $random;
            InstMem_Ready = $random;
            Mfc0 = $random;                
            IF_Exception_Stall = $random;
            ID_Exception_Stall = $random;
            EX_Exception_Stall = $random;
            EX_ALU_Stall = $random;
            M_Stall_Controller = $random;  
            #10;
            compare();
        end


        // Finish simulation
        #10;
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
//				$display("testcase is passed!!!");
            	$display("DP_Hazards = %h, ID_Rs = %h, ID_Rt = %h, EX_Rs = %h, EX_Rt = %h, EX_RtRd = %h, MEM_RtRd = %h, WB_RtRd = %h, EX_Link = %h, EX_RegWrite = %h, MEM_RegWrite = %h, WB_RegWrite = %h, MEM_MemRead = %h, MEM_MemWrite = %h, InstMem_Read = %h, InstMem_Ready = %h, Mfc0 = %h, IF_Exception_Stall = %h, ID_Exception_Stall = %h, EX_Exception_Stall = %h, EX_ALU_Stall = %h, M_Stall_Controller = %h, IF_Stall_dut = %h, ID_Stall_dut = %h, EX_Stall_dut = %h, M_Stall_dut = %h, WB_Stall_dut = %h, ID_RsFwdSel_dut = %h, ID_RtFwdSel_dut = %h, EX_RsFwdSel_dut = %h, EX_RtFwdSel_dut = %h, M_WriteDataFwdSel_dut = %h, IF_Stall_ref = %h, ID_Stall_ref = %h, EX_Stall_ref = %h, M_Stall_ref = %h, WB_Stall_ref = %h, ID_RsFwdSel_ref = %h, ID_RtFwdSel_ref = %h, EX_RsFwdSel_ref = %h, EX_RtFwdSel_ref = %h, M_WriteDataFwdSel_ref = %h", DP_Hazards, ID_Rs, ID_Rt, EX_Rs, EX_Rt, EX_RtRd, MEM_RtRd, WB_RtRd, EX_Link, EX_RegWrite, MEM_RegWrite, WB_RegWrite, MEM_MemRead, MEM_MemWrite, InstMem_Read, InstMem_Ready, Mfc0, IF_Exception_Stall, ID_Exception_Stall, EX_Exception_Stall, EX_ALU_Stall, M_Stall_Controller, IF_Stall_dut, ID_Stall_dut, EX_Stall_dut, M_Stall_dut, WB_Stall_dut, ID_RsFwdSel_dut, ID_RtFwdSel_dut, EX_RsFwdSel_dut, EX_RtFwdSel_dut, M_WriteDataFwdSel_dut, IF_Stall_ref, ID_Stall_ref, EX_Stall_ref, M_Stall_ref, WB_Stall_ref, ID_RsFwdSel_ref, ID_RtFwdSel_ref, EX_RsFwdSel_ref, EX_RtFwdSel_ref, M_WriteDataFwdSel_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("DP_Hazards = %h, ID_Rs = %h, ID_Rt = %h, EX_Rs = %h, EX_Rt = %h, EX_RtRd = %h, MEM_RtRd = %h, WB_RtRd = %h, EX_Link = %h, EX_RegWrite = %h, MEM_RegWrite = %h, WB_RegWrite = %h, MEM_MemRead = %h, MEM_MemWrite = %h, InstMem_Read = %h, InstMem_Ready = %h, Mfc0 = %h, IF_Exception_Stall = %h, ID_Exception_Stall = %h, EX_Exception_Stall = %h, EX_ALU_Stall = %h, M_Stall_Controller = %h, IF_Stall_dut = %h, ID_Stall_dut = %h, EX_Stall_dut = %h, M_Stall_dut = %h, WB_Stall_dut = %h, ID_RsFwdSel_dut = %h, ID_RtFwdSel_dut = %h, EX_RsFwdSel_dut = %h, EX_RtFwdSel_dut = %h, M_WriteDataFwdSel_dut = %h, IF_Stall_ref = %h, ID_Stall_ref = %h, EX_Stall_ref = %h, M_Stall_ref = %h, WB_Stall_ref = %h, ID_RsFwdSel_ref = %h, ID_RtFwdSel_ref = %h, EX_RsFwdSel_ref = %h, EX_RtFwdSel_ref = %h, M_WriteDataFwdSel_ref = %h", DP_Hazards, ID_Rs, ID_Rt, EX_Rs, EX_Rt, EX_RtRd, MEM_RtRd, WB_RtRd, EX_Link, EX_RegWrite, MEM_RegWrite, WB_RegWrite, MEM_MemRead, MEM_MemWrite, InstMem_Read, InstMem_Ready, Mfc0, IF_Exception_Stall, ID_Exception_Stall, EX_Exception_Stall, EX_ALU_Stall, M_Stall_Controller, IF_Stall_dut, ID_Stall_dut, EX_Stall_dut, M_Stall_dut, WB_Stall_dut, ID_RsFwdSel_dut, ID_RtFwdSel_dut, EX_RsFwdSel_dut, EX_RtFwdSel_dut, M_WriteDataFwdSel_dut, IF_Stall_ref, ID_Stall_ref, EX_Stall_ref, M_Stall_ref, WB_Stall_ref, ID_RsFwdSel_ref, ID_RtFwdSel_ref, EX_RsFwdSel_ref, EX_RtFwdSel_ref, M_WriteDataFwdSel_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
