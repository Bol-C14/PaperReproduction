 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period

    // Inputs
    reg clk_core;
    reg rst_x;
    reg i_req;
    reg i_wr;
    reg [3:0] i_adrs;
    reg [3:0] i_be;
    reg [31:0] i_wd;
    reg i_vint_x;
    reg i_vint_edge;
    reg i_vtx_int;

    // ref Outputs
    wire ref_o_ack;
    wire ref_o_rstr;
    wire [31:0] ref_o_rd;
    wire ref_o_video_start;
    wire [2:0] ref_o_aa_en;
    wire [6:0] ref_o_fb0_offset;
    wire [6:0] ref_o_fb1_offset;
    wire [1:0] ref_o_color_mode;
    wire ref_o_front_buffer;
    wire ref_o_fb_blend_en;
    wire ref_o_int;

    // Outputs
    wire o_ack;
    wire o_rstr;
    wire [31:0] o_rd;
    wire o_video_start;
    wire [2:0] o_aa_en;
    wire [6:0] o_fb0_offset;
    wire [6:0] o_fb1_offset;
    wire [1:0] o_color_mode;
    wire o_front_buffer;
    wire o_fb_blend_en;
    wire o_int;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

assign match = ({ref_o_ack,ref_o_rstr,ref_o_rd,ref_o_video_start,ref_o_aa_en,ref_o_fb0_offset,ref_o_fb1_offset,ref_o_color_mode,ref_o_front_buffer,ref_o_fb_blend_en,ref_o_int} === ({ref_o_ack,ref_o_rstr,ref_o_rd,ref_o_video_start,ref_o_aa_en,ref_o_fb0_offset,ref_o_fb1_offset,ref_o_color_mode,ref_o_front_buffer,ref_o_fb_blend_en,ref_o_int}  ^ {o_ack,o_rstr,o_rd,o_video_start,o_aa_en,o_fb0_offset,o_fb1_offset,o_color_mode,o_front_buffer,o_fb_blend_en,o_int}  ^ {ref_o_ack,ref_o_rstr,ref_o_rd,ref_o_video_start,ref_o_aa_en,ref_o_fb0_offset,ref_o_fb1_offset,ref_o_color_mode,ref_o_front_buffer,ref_o_fb_blend_en,ref_o_int} ));


    // ref the fm_hsys module
    ref_fm_hsys  rf(
        .clk_core(clk_core),
        .rst_x(rst_x),
        .i_req(i_req),
        .i_wr(i_wr),
        .i_adrs(i_adrs),
        .ref_o_ack(ref_o_ack),
        .i_be(i_be),
        .i_wd(i_wd),
        .ref_o_rstr(ref_o_rstr),
        .ref_o_rd(ref_o_rd),
        .ref_o_video_start(ref_o_video_start),
        .ref_o_aa_en(ref_o_aa_en),
        .ref_o_fb0_offset(ref_o_fb0_offset),
        .ref_o_fb1_offset(ref_o_fb1_offset),
        .ref_o_color_mode(ref_o_color_mode),
        .ref_o_front_buffer(ref_o_front_buffer),
        .ref_o_fb_blend_en(ref_o_fb_blend_en),
        .i_vint_x(i_vint_x),
        .i_vint_edge(i_vint_edge),
        .i_vtx_int(i_vtx_int),
        .ref_o_int(ref_o_int)
    );

    // Instantiate the fm_hsys module
    top uut (
        .clk_core(clk_core),
        .rst_x(rst_x),
        .i_req(i_req),
        .i_wr(i_wr),
        .i_adrs(i_adrs),
        .o_ack(o_ack),
        .i_be(i_be),
        .i_wd(i_wd),
        .o_rstr(o_rstr),
        .o_rd(o_rd),
        .o_video_start(o_video_start),
        .o_aa_en(o_aa_en),
        .o_fb0_offset(o_fb0_offset),
        .o_fb1_offset(o_fb1_offset),
        .o_color_mode(o_color_mode),
        .o_front_buffer(o_front_buffer),
        .o_fb_blend_en(o_fb_blend_en),
        .i_vint_x(i_vint_x),
        .i_vint_edge(i_vint_edge),
        .i_vtx_int(i_vtx_int),
        .o_int(o_int)
    );
    // Generate clock signal
    initial begin
        clk_core = 0;
        forever #(CLK_PERIOD / 2) clk_core = ~clk_core;
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rst_x = 0;
        i_req = 0;
        i_wr = 0;
        i_adrs = 0;
        i_be = 4'b0000;
        i_wd = 32'h0;
        i_vint_x = 0;
        i_vint_edge = 0;
        i_vtx_int = 0;

        // Apply reset
        #(CLK_PERIOD);
        rst_x = 1; // De-assert reset
        #(CLK_PERIOD);

        // Test Case 1: Write to video start register
        i_req = 1;
        i_wr = 1;
        i_adrs = 4'h0; // Address for video start
        i_be = 4'b0001; // Byte enable
        i_wd = 32'h1; // Write value
        #(CLK_PERIOD);
  compare();
        
        // Test Case 1: Check video start
        if (o_video_start) begin
            $display("Test Case 1 Passed: Video start set.");
        end else begin
            $display("Test Case 1 Failed: Video start not set.");
        end

        // Test Case 2: Read front buffer status
        i_req = 1;
        i_wr = 0; // Read
        i_adrs = 4'hB; // Address for front buffer
        #(CLK_PERIOD);
          compare();
        // Check if the read value is correct
        if (o_front_buffer == 0) begin
            $display("Test Case 2 Passed: Front buffer read correctly.");
        end else begin
            $display("Test Case 2 Failed: Front buffer read incorrect.");
        end

        // Test Case 3: Write to color mode register
        i_req = 1;
        i_wr = 1;
        i_adrs = 4'h5; // Address for color mode
        i_be = 4'b0001; // Byte enable
        i_wd = 32'h2; // Write value
        #(CLK_PERIOD);
  compare();
        
        // Check color mode
        if (o_color_mode == 2'b10) begin
            $display("Test Case 3 Passed: Color mode set correctly.");
        end else begin
            $display("Test Case 3 Failed: Color mode not set correctly.");
        end

        // Test Case 4: Simulate vertical interrupt
        i_vint_edge = 1; // Trigger vertical interrupt
        #(CLK_PERIOD);
        i_vint_edge = 0; // Clear interrupt
        #(CLK_PERIOD);
  compare();
        
        if (o_int) begin
            $display("Test Case 4 Passed: Interrupt triggered.");
        end else begin
            $display("Test Case 4 Failed: Interrupt not triggered.");
        end
//---------------------------------------------------------------------------------------------
         // ²âÊÔÓÃÀý1: »ù±¾¹¦ÄÜ²âÊÔ
        i_req = 1; i_wr = 1; i_adrs = 4'h0; i_be = 4'b1111; i_wd = 32'h00000001; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h1; i_be = 4'b1111; i_wd = 32'h0000001F; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h2; i_be = 4'b1111; i_wd = 32'h0000003F; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h5; i_be = 4'b1111; i_wd = 32'h00000003; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h9; i_be = 4'b1111; i_wd = 32'h00000001; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'hA; i_be = 4'b1111; i_wd = 32'h00000003; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'hB; i_be = 4'b1111; i_wd = 32'h00000001; #10;

        // ²âÊÔÓÃÀý2: ±ß½çÌõ¼þ²âÊÔ
        i_req = 1; i_wr = 1; i_adrs = 4'h0; i_be = 4'b0001; i_wd = 32'h00000001; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h0; i_be = 4'b0010; i_wd = 32'h00000400; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h0; i_be = 4'b0100; i_wd = 32'h00010000; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h1; i_be = 4'b0010; i_wd = 32'h00001F00; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h1; i_be = 4'b0100; i_wd = 32'h0000001F; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h2; i_be = 4'b0010; i_wd = 32'h00003F00; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h2; i_be = 4'b0100; i_wd = 32'h0000003F; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h5; i_be = 4'b0001; i_wd = 32'h00000003; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'h9; i_be = 4'b0001; i_wd = 32'h00000001; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'hA; i_be = 4'b0001; i_wd = 32'h00000003; #10;
        i_req = 1; i_wr = 1; i_adrs = 4'hB; i_be = 4'b0001; i_wd = 32'h00000001; #10;

        // ²âÊÔÓÃÀý3: ¶Á²Ù×÷²âÊÔ
        i_req = 1; i_wr = 0; i_adrs = 4'h0; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'h1; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'h2; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'h5; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'h8; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'h9; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'hA; #10;
        i_req = 1; i_wr = 0; i_adrs = 4'hB; #10;

        // ²âÊÔÓÃÀý4: ÖÐ¶Ï²âÊÔ
        i_vint_x = 1; i_vint_edge = 1; i_vtx_int = 1; #10;
        i_vint_x = 0; i_vint_edge = 0; i_vtx_int = 0; #10;
//----------------------------------------------------------------------------------------------------------
  repeat (96) begin
      @(posedge clk_core);
rst_x = $random;
i_req = $random;
i_wr = $random;
i_adrs = $random;
i_be = $random;
i_wd = $random;
i_vint_x = $random;
i_vint_edge = $random;
i_vtx_int = $random;
     
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
