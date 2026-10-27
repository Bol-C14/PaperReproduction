 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD_MB = 10; // Clock period for ckmb
    parameter CLK_PERIOD_DR = 10;  // Clock period for ckdr

    // Testbench signals
    reg ckmb;
    reg ckdr;
    reg reset;
    reg IO_Addr_Strobe;
    reg IO_Read_Strobe;
    reg IO_Write_Strobe;
    reg [31:0] IO_Address;
    reg [3:0] IO_Byte_Enable;
    reg [31:0] IO_Write_Data;
    reg [3:0] page;
    reg [2:0] dbg_out;
    reg [255:0] srdat;
    reg srdy;

    // Outputs from the adapter
    wire srd_ref, srd_dut;
    wire swr_ref, swr_dut;
    wire [33:5] sa_ref, sa_dut;
    wire [255:0] swdat_ref, swdat_dut;
    wire [31:0] smsk_ref, smsk_dut;
    wire IO_Ready_ref, IO_Ready_dut;
    wire [31:0] IO_Read_Data_ref, IO_Read_Data_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({srd_ref, swr_ref, sa_ref, swdat_ref, smsk_ref, IO_Ready_ref, IO_Read_Data_ref} === ({srd_ref, swr_ref, sa_ref, swdat_ref, smsk_ref, IO_Ready_ref, IO_Read_Data_ref} ^ {srd_dut, swr_dut, sa_dut, swdat_dut, smsk_dut, IO_Ready_dut, IO_Read_Data_dut} ^ {srd_ref, swr_ref, sa_ref, swdat_ref, smsk_ref, IO_Ready_ref, IO_Read_Data_ref}));

    // Instantiate the adapter module
    adapter_ref ref_model (
        .ckmb(ckmb),
        .ckdr(ckdr),
        .reset(reset),
        .srd_ref(srd_ref),
        .swr_ref(swr_ref),
        .sa_ref(sa_ref),
        .swdat_ref(swdat_ref),
        .smsk_ref(smsk_ref),
        .srdat(srdat),
        .srdy(srdy),
        .IO_Ready_ref(IO_Ready_ref),
        .IO_Addr_Strobe(IO_Addr_Strobe),
        .IO_Read_Strobe(IO_Read_Strobe),
        .IO_Write_Strobe(IO_Write_Strobe),
        .IO_Read_Data_ref(IO_Read_Data_ref),
        .IO_Address(IO_Address),
        .IO_Byte_Enable(IO_Byte_Enable),
        .IO_Write_Data(IO_Write_Data),
        .page(page),
        .dbg_out(dbg_out)
    );

    top dut (
        .ckmb(ckmb),
        .ckdr(ckdr),
        .reset(reset),
        .srd(srd_dut),
        .swr(swr_dut),
        .sa(sa_dut),
        .swdat(swdat_dut),
        .smsk(smsk_dut),
        .srdat(srdat),
        .srdy(srdy),
        .IO_Ready(IO_Ready_dut),
        .IO_Addr_Strobe(IO_Addr_Strobe),
        .IO_Read_Strobe(IO_Read_Strobe),
        .IO_Write_Strobe(IO_Write_Strobe),
        .IO_Read_Data(IO_Read_Data_dut),
        .IO_Address(IO_Address),
        .IO_Byte_Enable(IO_Byte_Enable),
        .IO_Write_Data(IO_Write_Data),
        .page(page),
        .dbg_out(dbg_out)
    );

    // Clock generation
    initial begin
        ckmb = 0;
        forever #(CLK_PERIOD_MB / 2) ckmb = ~ckmb;
    end

    initial begin
        ckdr = 0;
        forever #(CLK_PERIOD_DR / 2) ckdr = ~ckdr;
    end

    // Test procedure
    initial begin
        // Initialize signals
        reset = 1;
        IO_Addr_Strobe = 0;
        IO_Read_Strobe = 0;
        IO_Write_Strobe = 0;
        IO_Address = 0;
        IO_Byte_Enable = 4'b1111;
        IO_Write_Data = 32'hDEADBEEF;
        srdat = 256'h0;
        srdy = 0;
        page = 4'b0000;
        dbg_out = 3'b000;

        // Release reset
        #(CLK_PERIOD_MB * 2);
        reset = 0;

        // Test Write Operation
        @(posedge ckmb);
        IO_Addr_Strobe = 1;
        IO_Write_Strobe = 1;
        IO_Address = 32'h00000000; // Target address
        @(posedge ckmb);
        compare();

       // End Write Strobe
        IO_Write_Strobe = 0;
        IO_Addr_Strobe = 0;

        // Test Read Operation
        @(posedge ckmb);
        compare();
        srdat = 256'hAABBCCDDEEFF00112233445566778899; // Mock read data
        srdy = 1;       
        IO_Addr_Strobe = 1;
        IO_Read_Strobe = 1;
        IO_Address = 32'h00000000; // Target address
        @(posedge ckmb);
        compare();

        // End Read Strobe
        IO_Read_Strobe = 0;
        IO_Addr_Strobe = 0;
        srdy = 0;
        @(posedge ckmb);
        compare();

        repeat (15) begin
            IO_Addr_Strobe = $random;
            IO_Read_Strobe = $random;
            IO_Write_Strobe = $random;
            IO_Address = $random;
            IO_Byte_Enable = $random;
            IO_Write_Data = $random;
            srdat = {$random,$random,$random,$random,$random,$random,$random,$random};
            srdy = $random;
            page = $random;
            dbg_out = $random;
            @(posedge ckmb);
            compare();
        end
        
        for (integer i=0; i<8; i++) begin
            repeat (15) begin
                IO_Addr_Strobe = 1;
                IO_Read_Strobe = $random;
                IO_Write_Strobe = 1;
                IO_Address = $random;
                IO_Address[4:2] = i;
                IO_Byte_Enable = $random;
                IO_Write_Data = $random;
                srdat = {$random,$random,$random,$random,$random,$random,$random,$random};
                srdy = $random;
                page = $random;
                dbg_out = $random;
                @(posedge ckmb);
                compare();
        end
        end




        // Test reset condition
        reset = 1;
        @(posedge ckmb);
        reset = 0;
        @(posedge ckmb);
        compare();
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        // Finish simulation
        $finish;
    end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("reset = %h, srdat = %h, srdy = %h, IO_Addr_Strobe = %h, IO_Read_Strobe = %h, IO_Write_Strobe = %h, IO_Address = %h, IO_Byte_Enable = %h, IO_Write_Data = %h, page = %h, dbg_out = %h, srd_dut = %h, swr_dut = %h, sa_dut = %h, swdat_dut = %h, smsk_dut = %h, IO_Ready_dut = %h, IO_Read_Data_dut = %h, srd_ref = %h, swr_ref = %h, sa_ref = %h, swdat_ref = %h, smsk_ref = %h, IO_Ready_ref = %h, IO_Read_Data_ref = %h", reset, srdat, srdy, IO_Addr_Strobe, IO_Read_Strobe, IO_Write_Strobe, IO_Address, IO_Byte_Enable, IO_Write_Data, page, dbg_out, srd_dut, swr_dut, sa_dut, swdat_dut, smsk_dut, IO_Ready_dut, IO_Read_Data_dut, srd_ref, swr_ref, sa_ref, swdat_ref, smsk_ref, IO_Ready_ref, IO_Read_Data_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("reset = %h, srdat = %h, srdy = %h, IO_Addr_Strobe = %h, IO_Read_Strobe = %h, IO_Write_Strobe = %h, IO_Address = %h, IO_Byte_Enable = %h, IO_Write_Data = %h, page = %h, dbg_out = %h, srd_dut = %h, swr_dut = %h, sa_dut = %h, swdat_dut = %h, smsk_dut = %h, IO_Ready_dut = %h, IO_Read_Data_dut = %h, srd_ref = %h, swr_ref = %h, sa_ref = %h, swdat_ref = %h, smsk_ref = %h, IO_Ready_ref = %h, IO_Read_Data_ref = %h", reset, srdat, srdy, IO_Addr_Strobe, IO_Read_Strobe, IO_Write_Strobe, IO_Address, IO_Byte_Enable, IO_Write_Data, page, dbg_out, srd_dut, swr_dut, sa_dut, swdat_dut, smsk_dut, IO_Ready_dut, IO_Read_Data_dut, srd_ref, swr_ref, sa_ref, swdat_ref, smsk_ref, IO_Ready_ref, IO_Read_Data_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

