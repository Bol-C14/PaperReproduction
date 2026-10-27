 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period for 100 MHz
    parameter COLOR_DEPTH = 2'b01; // Example: 16bpp
    parameter PSEUDO_COLOR = 0; // Example: Not using pseudo color

    // Inputs
    reg clk;
    reg srst;
    reg [31:0] vdat_buffer_di;
    reg [1:0] ColorDepth;
    reg PseudoColor;
    reg vdat_buffer_empty;
    reg rgb_fifo_full;
    reg clut_ack;
    reg [23:0] clut_q;

    // Outputs
    wire vdat_buffer_rreq,ref_vdat_buffer_rreq;
    wire rgb_fifo_wreq,ref_rgb_fifo_wreq;
    wire [7:0] r, g, b,ref_r,ref_g,ref_b;
    wire clut_req,ref_clut_req;
    wire [7:0] clut_offs,ref_clut_offs;

wire       match;
integer total_tests = 0;
integer failed_tests = 0;
assign  match = ({ref_vdat_buffer_rreq, ref_rgb_fifo_wreq, ref_r, ref_g, ref_b, ref_clut_req, ref_clut_offs} === {vdat_buffer_rreq, rgb_fifo_wreq, r, g, b, clut_req, clut_offs});

    // Instantiate the vga_colproc module
    ref_vga_colproc ref_model (
        .clk(clk),
        .srst(srst),
        .vdat_buffer_di(vdat_buffer_di),
        .ColorDepth(ColorDepth),
        .PseudoColor(PseudoColor),
        .vdat_buffer_empty(vdat_buffer_empty),
        .ref_vdat_buffer_rreq(ref_vdat_buffer_rreq),
        .rgb_fifo_full(rgb_fifo_full),
        .ref_rgb_fifo_wreq(ref_rgb_fifo_wreq),
        .ref_r(ref_r),
        .ref_g(ref_g),
        .ref_b(ref_b),
        .ref_clut_req(ref_clut_req),
        .clut_ack(clut_ack),
        .ref_clut_offs(ref_clut_offs),
        .clut_q(clut_q)
    );

    top uut (
        .clk(clk),
        .srst(srst),
        .vdat_buffer_di(vdat_buffer_di),
        .ColorDepth(ColorDepth),
        .PseudoColor(PseudoColor),
        .vdat_buffer_empty(vdat_buffer_empty),
        .vdat_buffer_rreq(vdat_buffer_rreq),
        .rgb_fifo_full(rgb_fifo_full),
        .rgb_fifo_wreq(rgb_fifo_wreq),
        .r(r),
        .g(g),
        .b(b),
        .clut_req(clut_req),
        .clut_ack(clut_ack),
        .clut_offs(clut_offs),
        .clut_q(clut_q)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #(CLK_PERIOD / 2) clk = ~clk; // Toggle clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        srst = 1;
        vdat_buffer_di = 32'h0;
        ColorDepth = COLOR_DEPTH;
        PseudoColor = PSEUDO_COLOR;
        vdat_buffer_empty = 1;
        rgb_fifo_full = 0;
        clut_ack = 0;
        clut_q = 24'hFF_00_00; // Example CLUT data (red)

        // Release reset
        #(CLK_PERIOD);
        srst = 0;

        // Test Case 1: Request data from the vdat buffer
        vdat_buffer_empty = 0; // Buffer has data
        #(CLK_PERIOD);
        
        // Simulate writing data to the buffer
        vdat_buffer_di = 32'hA5A5A5A5; // Example data
        #(CLK_PERIOD);
        
        // Request data once the buffer is not empty
        #(CLK_PERIOD);
        if (!vdat_buffer_rreq) begin
            compare();
            $display("Test Case 1 Failed: Expected vdat_buffer_rreq = 1");
        end

        // Test Case 2: Processing in 8bpp mode with pseudo color
        ColorDepth = 2'b00; // 8bpp
        PseudoColor = 1;
        #(CLK_PERIOD);
        if (rgb_fifo_wreq !== 1) begin
            compare();
            $display("Test Case 2 Failed: Expected rgb_fifo_wreq = 1");
        end
        if (clut_req !== 1) begin
            compare();
            $display("Test Case 2 Failed: Expected clut_req = 1");
        end

        // Test Case 3: Check RGB output values
        #(CLK_PERIOD);
        if (r !== 8'hFF || g !== 8'h00 || b !== 8'h00) begin
            compare();
            $display("Test Case 3 Failed: Expected RGB = (FF, 00, 00), got (%h, %h, %h)", r, g, b);
        end

        // Test Case 4: Check color depth 16bpp
        ColorDepth = 2'b01; // 16bpp
        #(CLK_PERIOD);
        if (rgb_fifo_wreq !== 1) begin
            compare();
            $display("Test Case 4 Failed: Expected rgb_fifo_wreq = 1");
        end

        // Test Case 5: Resetting the module
        srst = 1; // Assert reset
        #(CLK_PERIOD);
        srst = 0; // Deassert reset
        if (vdat_buffer_rreq !== 0) begin
            compare();
            $display("Test Case 5 Failed: Expected vdat_buffer_rreq = 0 after reset");
        end

        // Test Case 6: Full RGB FIFO
        rgb_fifo_full = 1; // Simulate full FIFO
        #(CLK_PERIOD);
        if (vdat_buffer_rreq !== 0) begin
            compare();
            $display("Test Case 6 Failed: Expected vdat_buffer_rreq = 0 when rgb_fifo is full");
        end

        repeat(600) begin
            #10; // Wait for 10ns
            vdat_buffer_di = $random;
            ColorDepth = $random % 4;
            PseudoColor = $random % 2;
            vdat_buffer_empty = $random % 2;
            rgb_fifo_full = $random % 2;
            clut_ack = $random % 2;
            clut_q = $random;
            #20;
            compare();
        end

        // Finish simulation
        #(CLK_PERIOD * 10);
    $display("\033[1;34mAll tests completed.\033[0m");
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
            failed_tests = failed_tests + 1; 
		end
    
	endtask
endmodule
