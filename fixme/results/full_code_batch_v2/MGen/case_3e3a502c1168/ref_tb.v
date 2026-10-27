 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter address_bit = 9;
    parameter data_bit = 38;

    // Inputs
    reg clk;
    reg rst;
    reg datavalid;
    reg A, B, C, D, fp, fn;
    reg [address_bit-1:0] p, hp, np, tp;
    reg [data_bit-1:0] dp, dd;

    // Outputs
    wire h_we_ref, h_we_dut, t_we_ref, t_we_dut, n_we_ref, n_we_dut, d_we_ref, d_we_dut;
    wire [address_bit-1:0] h_waddr_ref, h_waddr_dut, t_waddr_ref, t_waddr_dut, n_waddr_ref, n_waddr_dut, d_waddr_ref, d_waddr_dut;
    wire [address_bit-1:0] h_wdata_ref, h_wdata_dut, t_wdata_ref, t_wdata_dut, n_wdata_ref, n_wdata_dut;
    wire [data_bit-1:0] d_wdata_ref, d_wdata_dut;
    wire HCN_ref, HCN_dut, DAC_ref, DAC_dut, DMG_ref, DMG_dut, CLR_ref, CLR_dut, O_ref, O_dut;
    wire EOC_ref, EOC_dut;

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({h_we_ref, t_we_ref, n_we_ref, d_we_ref, h_waddr_ref, t_waddr_ref, n_waddr_ref, d_waddr_ref, h_wdata_ref, t_wdata_ref, n_wdata_ref, d_wdata_ref, HCN_ref, DAC_ref, DMG_ref, CLR_ref, O_ref, EOC_ref} === ({h_we_ref, t_we_ref, n_we_ref, d_we_ref, h_waddr_ref, t_waddr_ref, n_waddr_ref, d_waddr_ref, h_wdata_ref, t_wdata_ref, n_wdata_ref, d_wdata_ref, HCN_ref, DAC_ref, DMG_ref, CLR_ref, O_ref, EOC_ref} ^ {h_we_dut, t_we_dut, n_we_dut, d_we_dut, h_waddr_dut, t_waddr_dut, n_waddr_dut, d_waddr_dut, h_wdata_dut, t_wdata_dut, n_wdata_dut, d_wdata_dut, HCN_dut, DAC_dut, DMG_dut, CLR_dut, O_dut, EOC_dut} ^ {h_we_ref, t_we_ref, n_we_ref, d_we_ref, h_waddr_ref, t_waddr_ref, n_waddr_ref, d_waddr_ref, h_wdata_ref, t_wdata_ref, n_wdata_ref, d_wdata_ref, HCN_ref, DAC_ref, DMG_ref, CLR_ref, O_ref, EOC_ref}));

    // Instantiate the equivalence_resolver module
    equivalence_resolver_ref #(
        .address_bit(address_bit),
        .data_bit(data_bit)
    ) ref_model (
        .clk(clk),
        .rst(rst),
        .datavalid(datavalid),
        .A(A),
        .B(B),
        .C(C),
        .D(D),
        .fp(fp),
        .fn(fn),
        .p(p),
        .hp(hp),
        .np(np),
        .tp(tp),
        .dp(dp),
        .dd(dd),
        .h_we_ref(h_we_ref),
        .t_we_ref(t_we_ref),
        .n_we_ref(n_we_ref),
        .d_we_ref(d_we_ref),
        .h_waddr_ref(h_waddr_ref),
        .t_waddr_ref(t_waddr_ref),
        .n_waddr_ref(n_waddr_ref),
        .d_waddr_ref(d_waddr_ref),
        .h_wdata_ref(h_wdata_ref),
        .t_wdata_ref(t_wdata_ref),
        .n_wdata_ref(n_wdata_ref),
        .d_wdata_ref(d_wdata_ref),
        .HCN_ref(HCN_ref),
        .DAC_ref(DAC_ref),
        .DMG_ref(DMG_ref),
        .CLR_ref(CLR_ref),
        .EOC_ref(EOC_ref),
        .O_ref(O_ref)
    );

    top #(
        .address_bit(address_bit),
        .data_bit(data_bit)
    ) dut (
        .clk(clk),
        .rst(rst),
        .datavalid(datavalid),
        .A(A),
        .B(B),
        .C(C),
        .D(D),
        .fp(fp),
        .fn(fn),
        .p(p),
        .hp(hp),
        .np(np),
        .tp(tp),
        .dp(dp),
        .dd(dd),
        .h_we(h_we_dut),
        .t_we(t_we_dut),
        .n_we(n_we_dut),
        .d_we(d_we_dut),
        .h_waddr(h_waddr_dut),
        .t_waddr(t_waddr_dut),
        .n_waddr(n_waddr_dut),
        .d_waddr(d_waddr_dut),
        .h_wdata(h_wdata_dut),
        .t_wdata(t_wdata_dut),
        .n_wdata(n_wdata_dut),
        .d_wdata(d_wdata_dut),
        .HCN(HCN_dut),
        .DAC(DAC_dut),
        .DMG(DMG_dut),
        .CLR(CLR_dut),
        .EOC(EOC_dut),
        .O(O_dut)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100 MHz clock
    end

    // Test procedure
    initial begin
        // Initialize inputs
        rst = 1;
        datavalid = 0;
        A = 0; B = 0; C = 0; D = 0; fp = 0; fn = 0;
        p = 9'b0; hp = 9'b0; np = 9'b0; tp = 9'b0;
        dp = 38'b0; dd = 38'b0;

        // Reset the module
        #10;
        rst = 0;

        // Test Case 1: Check basic functionality with Ec condition
        #10;
        datavalid = 1;
        C = 1; D = 0; // Ec = 1
        #10; // Wait for processing
        datavalid = 0; // Disable data valid
        #20; // Wait for some cycles
        compare();

        // Test Case 2: Check O condition
        #10;
        datavalid = 1;
        A = 1; B = 1; C = 1; D = 1; // O = 1
        #10;
        datavalid = 0;
        #20; // Wait for some cycles
        compare();

        // Test Case 3: Check Ep condition
        #10;
        datavalid = 1;
        fp = 1; // Ep = 1
        #10;
        datavalid = 0;
        #20; // Wait for some cycles
        compare();

        #10;
        A = 1;
        B = 0;
        C = 0;
        D = 1;
        fp = 1;
        np = 1;
        p =1;
        #20;
        compare();
        
        datavalid = 1;
        repeat (512) begin
            C = 1; D = 0;
            #10;
            B = 1; D = 1; A = 0; C = 0;
            #10;
        end
        compare();

        


        repeat (93) begin
            datavalid = 1;
            A = $random;
            B = $random;
            C = $random;
            D = $random;
            p = $random;
            hp = $random;
            np = $random;
            tp = $random;
            dp = {$random,$random};
            fp = $random;
            fn = $random;
            dd = {$random,$random};
            #10;
            compare();
        end

        // Test Case 4: Check reset functionality
        #10;
        compare();
        rst = 1; // Assert reset
        #10;
        rst = 0; // Release reset
        #10;
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
            	$display("rst = %h, datavalid = %h, A = %h, B = %h, C = %h, D = %h, p = %h, hp = %h, np = %h, tp = %h, dp = %h, fp = %h, fn = %h, dd = %h, h_we_dut = %h, t_we_dut = %h, n_we_dut = %h, d_we_dut = %h, h_waddr_dut = %h, t_waddr_dut = %h, n_waddr_dut = %h, d_waddr_dut = %h, h_wdata_dut = %h, t_wdata_dut = %h, n_wdata_dut = %h, d_wdata_dut = %h, HCN_dut = %h, DAC_dut = %h, DMG_dut = %h, CLR_dut = %h, O_dut = %h, EOC_dut = %h, h_we_ref = %h, t_we_ref = %h, n_we_ref = %h, d_we_ref = %h, h_waddr_ref = %h, t_waddr_ref = %h, n_waddr_ref = %h, d_waddr_ref = %h, h_wdata_ref = %h, t_wdata_ref = %h, n_wdata_ref = %h, d_wdata_ref = %h, HCN_ref = %h, DAC_ref = %h, DMG_ref = %h, CLR_ref = %h, O_ref = %h, EOC_ref = %h", rst, datavalid, A, B, C, D, p, hp, np, tp, dp, fp, fn, dd, h_we_dut, t_we_dut, n_we_dut, d_we_dut, h_waddr_dut, t_waddr_dut, n_waddr_dut, d_waddr_dut, h_wdata_dut, t_wdata_dut, n_wdata_dut, d_wdata_dut, HCN_dut, DAC_dut, DMG_dut, CLR_dut, O_dut, EOC_dut, h_we_ref, t_we_ref, n_we_ref, d_we_ref, h_waddr_ref, t_waddr_ref, n_waddr_ref, d_waddr_ref, h_wdata_ref, t_wdata_ref, n_wdata_ref, d_wdata_ref, HCN_ref, DAC_ref, DMG_ref, CLR_ref, O_ref, EOC_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("rst = %h, datavalid = %h, A = %h, B = %h, C = %h, D = %h, p = %h, hp = %h, np = %h, tp = %h, dp = %h, fp = %h, fn = %h, dd = %h, h_we_dut = %h, t_we_dut = %h, n_we_dut = %h, d_we_dut = %h, h_waddr_dut = %h, t_waddr_dut = %h, n_waddr_dut = %h, d_waddr_dut = %h, h_wdata_dut = %h, t_wdata_dut = %h, n_wdata_dut = %h, d_wdata_dut = %h, HCN_dut = %h, DAC_dut = %h, DMG_dut = %h, CLR_dut = %h, O_dut = %h, EOC_dut = %h, h_we_ref = %h, t_we_ref = %h, n_we_ref = %h, d_we_ref = %h, h_waddr_ref = %h, t_waddr_ref = %h, n_waddr_ref = %h, d_waddr_ref = %h, h_wdata_ref = %h, t_wdata_ref = %h, n_wdata_ref = %h, d_wdata_ref = %h, HCN_ref = %h, DAC_ref = %h, DMG_ref = %h, CLR_ref = %h, O_ref = %h, EOC_ref = %h", rst, datavalid, A, B, C, D, p, hp, np, tp, dp, fp, fn, dd, h_we_dut, t_we_dut, n_we_dut, d_we_dut, h_waddr_dut, t_waddr_dut, n_waddr_dut, d_waddr_dut, h_wdata_dut, t_wdata_dut, n_wdata_dut, d_wdata_dut, HCN_dut, DAC_dut, DMG_dut, CLR_dut, O_dut, EOC_dut, h_we_ref, t_we_ref, n_we_ref, d_we_ref, h_waddr_ref, t_waddr_ref, n_waddr_ref, d_waddr_ref, h_wdata_ref, t_wdata_ref, n_wdata_ref, d_wdata_ref, HCN_ref, DAC_ref, DMG_ref, CLR_ref, O_ref, EOC_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

