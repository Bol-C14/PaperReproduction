 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter W = 8;
    parameter D = 8;

    // Inputs
    reg rst;
    reg clk;
    reg [W-1:0] d_in;
    reg up_rl;
    reg up_kc;
    reg up_kf;
    reg up_pms;
    reg up_dt1;
    reg up_tl;
    reg up_ks;
    reg up_amsen;
    reg up_dt2;
    reg up_d1l;
    reg up_kon;
    reg [1:0] op;
    reg [2:0] ch;
    reg csm;
    reg flag_A;

reg [255:0] ref_output;
reg [255:0] dut_output;



    // Outputs
    wire busy,ref_busy;
    wire [1:0] rl_out,ref_rl_out;
    wire [2:0] fb_out,ref_fb_out;
    wire [2:0] con_out,ref_con_out;
    wire [6:0] kc_out,ref_kc_out;
    wire [5:0] kf_out,ref_kf_out;
    wire [2:0] pms_out,ref_pms_out;
    wire [1:0] ams_out,ref_ams_out;
    wire [2:0] dt1_out,ref_dt1_out;
    wire [3:0] mul_out,ref_mul_out;
    wire [6:0] tl_out,ref_tl_out;
    wire [1:0] ks_out,ref_ks_out;
    wire [4:0] ar_out,ref_ar_out;
    wire       amsen_out,ref_amsen_out;
    wire [4:0] d1r_out,ref_d1r_out;
    wire [1:0] dt2_out,ref_dt2_out;
    wire [4:0] d2r_out,ref_d2r_out;
    wire [3:0] d1l_out,ref_d1l_out;
    wire [3:0] rr_out,ref_rr_out;
    wire       kon_out,ref_kon_out;
    wire       koff_out,ref_koff_out;
    wire [1:0] cur_op,ref_cur_op;
    reg        zero,ref_zero;

    wire       match;

    integer total_tests = 0;
    integer failed_tests = 0;
    integer test_case = 0;
    integer test_passed = 1;


	assign ref_output= {ref_busy,ref_rl_out,ref_fb_out,ref_con_out,ref_kc_out,ref_kf_out,ref_pms_out,ref_ams_out,ref_dt1_out,ref_mul_out,ref_tl_out,ref_ks_out,ref_ar_out,
                     ref_amsen_out,ref_d1r_out,ref_dt2_out,ref_d2r_out,ref_d1l_out,ref_rr_out,ref_kon_out,ref_koff_out,ref_cur_op,ref_zero};
	assign dut_output = {busy,rl_out,fb_out,con_out,kc_out,kf_out,pms_out,ams_out,dt1_out,mul_out,tl_out,ks_out,ar_out,amsen_out,d1r_out,dt2_out,d2r_out,d1l_out,rr_out,kon_out,koff_out,cur_op,zero};



    assign match = (ref_output === ref_output ^ dut_output ^ ref_output);


    // Instantiate the jt51_reg module
    top #(
        .W(W),
        .D(D)
    ) uut (
        .rst(rst),
        .clk(clk),
        .d_in(d_in),
        .up_rl(up_rl),
        .up_kc(up_kc),
        .up_kf(up_kf),
        .up_pms(up_pms),
        .up_dt1(up_dt1),
        .up_tl(up_tl),
        .up_ks(up_ks),
        .up_amsen(up_amsen),
        .up_dt2(up_dt2),
        .up_d1l(up_d1l),
        .up_kon(up_kon),
        .op(op),
        .ch(ch),
        .csm(csm),
        .flag_A(flag_A),
        .busy(busy),
        .rl_out(rl_out),
        .fb_out(fb_out),
        .con_out(con_out),
        .kc_out(kc_out),
        .kf_out(kf_out),
        .pms_out(pms_out),
        .ams_out(ams_out),
        .dt1_out(dt1_out),
        .mul_out(mul_out),
        .tl_out(tl_out),
        .ks_out(ks_out),
        .ar_out(ar_out),
        .amsen_out(amsen_out),
        .d1r_out(d1r_out),
        .dt2_out(dt2_out),
        .d2r_out(d2r_out),
        .d1l_out(d1l_out),
        .rr_out(rr_out),
        .kon_out(kon_out),
        .koff_out(koff_out),
        .cur_op(cur_op),
        .zero(zero)
    );

    ref_jt51_reg #(
        .W(W),
        .D(D)
    ) ref_model (
        .rst(rst),
        .clk(clk),
        .d_in(d_in),
        .up_rl(up_rl),
        .up_kc(up_kc),
        .up_kf(up_kf),
        .up_pms(up_pms),
        .up_dt1(up_dt1),
        .up_tl(up_tl),
        .up_ks(up_ks),
        .up_amsen(up_amsen),
        .up_dt2(up_dt2),
        .up_d1l(up_d1l),
        .up_kon(up_kon),
        .op(op),
        .ch(ch),
        .csm(csm),
        .flag_A(flag_A),
        .ref_busy(ref_busy),
        .ref_rl_out(ref_rl_out),
        .ref_fb_out(ref_fb_out),
        .ref_con_out(ref_con_out),
        .ref_kc_out(ref_kc_out),
        .ref_kf_out(ref_kf_out),
        .ref_pms_out(ref_pms_out),
        .ref_ams_out(ref_ams_out),
        .ref_dt1_out(ref_dt1_out),
        .ref_mul_out(ref_mul_out),
        .ref_tl_out(ref_tl_out),
        .ref_ks_out(ref_ks_out),
        .ref_ar_out(ref_ar_out),
        .ref_d1r_out(ref_ar_out),
        .ref_dt2_out(ref_dt2_out),
        .ref_d2r_out(ref_d2r_out),
        .ref_d1l_out(ref_d1l_out),
        .ref_rr_out(ref_rr_out),
        .ref_kon_out(ref_kon_out),
        .ref_koff_out(ref_koff_out),
        .ref_cur_op(ref_cur_op),
        .ref_zero(ref_zero)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rst      = 1;
        d_in     = 0;
        up_rl    = 0;
        up_kc    = 0;
        up_kf    = 0;
        up_pms   = 0;
        up_dt1   = 0;
        up_tl    = 0;
        up_ks    = 0;
        up_amsen = 0;
        up_dt2   = 0;
        up_d1l   = 0;
        up_kon   = 0;
        op       = 0;
        ch       = 0;
        csm      = 0;
        flag_A   = 0;
		

        // Release reset
        #10;
        rst = 0;
		#10;
		d_in     = 1; 
        up_rl    = 1; 
        up_kc    = 1; 
        up_kf    = 1; 
        up_pms   = 1; 
        up_dt1   = 1; 
        up_tl    = 1; 
        up_ks    = 1; 
        up_amsen = 1; 
        up_dt2   = 1; 
        up_d1l   = 1; 
        up_kon   = 1; 
        op       = 1; 
        ch       = 1; 
        csm      = 1; 
        flag_A   = 1; 
		#10;
        compare();
		#10;


		repeat(100) begin
		rst = 1;
		#10;
		rst = 0;
		d_in     = $random;
		up_rl    = $random;
		up_kc    = $random;
		up_kf    = $random;
		up_pms   = $random;
		up_dt1   = $random;
		up_tl    = $random;
		up_ks    = $random;
		up_amsen = $random;
		up_dt2   = $random;
		up_d1l   = $random;
		up_kon   = $random;
		op       = $random;
		ch       = $random;
		csm      = $random;
		flag_A   = $random;
		#10;
		compare();
		#10;
		end
		#1000;
		
		
		
		
		
        #10;
        d_in = 8'hAA; // Sample data
        up_kc = 1;    // Enable update for kc
        #10;
        up_kc = 0;    // Disable update
        #10;
        compare();
		#10;

        #10;
        d_in = 8'hBB; // New data
        up_rl = 1;    // Enable update for rl
        up_kf = 1;    // Enable update for kf
        #10;
        up_rl = 0;    // Disable update
        up_kf = 0;    // Disable update
        #10;
        compare();
		#10;

        #10;
        up_kon = 1; // Trigger kon
        #10;
        up_kon = 0; // End kon trigger
        #10;
        compare();
		#10;

        #10;
        rst = 1; // Assert reset
        #10;
        rst = 0; // Release reset
        #10;
        compare();
		#10;



        #10;
        up_rl = 1; up_kc = 1; up_kf = 1; up_pms = 1; up_dt1 = 1; up_tl = 1; up_ks = 1; up_amsen = 1; up_dt2 = 1; up_d1l = 1; up_kon = 1;
        d_in = 8'hFF; // Set all outputs to maximum or expected value
        #10;
        up_rl = 0; up_kc = 0; up_kf = 0; up_pms = 0; up_dt1 = 0; up_tl = 0; up_ks = 0; up_amsen = 0; up_dt2 = 0; up_d1l = 0; up_kon = 0;
        #10;
        compare();
		#10;

        #10;
        d_in = 8'h00; // Test zero value
        up_kc = 1;    // Enable update for kc
        #10;
        up_kc = 0;    // Disable update
        #10;
        compare();
		#10;


		csm = 1;
        flag_A = 1;
        #20; 
        flag_A = 0;        
        #620; 
        csm = 0;

        #10;
        d_in = 8'b0000_1100; 
        up_dt1 = 1; 
        #10; 
        up_dt1 = 0;

        #10;
        d_in = 8'b0000_0000; 
        up_dt1 = 1; 
        #10; 
        up_dt1 = 0;

        #10;
        d_in = 8'b0000_0100; 
        up_dt1 = 1; 
        #10; 
        up_dt1 = 0;

        #10;
        d_in = 8'b0000_1000; 
        up_dt1 = 1; 
        #10; 
        up_dt1 = 0;




 
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
		end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
			$display("ref_output = %h,dut_output = %h\n",ref_output,dut_output);
            failed_tests = failed_tests + 1; 
		end
    
	endtask


    initial begin
        $dumpfile("sim.fsdb");
		/* omitted diagnostic FSDB output: $fsdbDumpMDA(); */
		/* omitted diagnostic FSDB output: $fsdbDumpvars(); */
	  	/* omitted diagnostic FSDB output: $fsdbDumpMDA(); */

    end

endmodule
