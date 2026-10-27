 `timescale 1ns/1ns

module tb;

    // Signal Declarations
    reg clk;
    reg rst_n;
    reg [3:0] in_m;
    wire [3:0] out_m_ref, out_m_dut;
    wire goods_ref, goods_dut;
    wire match;
    reg [3:0] m[3:0];
    reg [1:0] index;

    initial begin
    m[0] = 1;
    m[1] = 2;
    m[2] = 5;
    end
    
    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({goods_ref, out_m_ref} === ({goods_ref, out_m_ref} ^ {goods_dut, out_m_dut} ^ {goods_ref, out_m_ref}));
    // Instantiate the DUT (Device Under Test)

    FSM_ref ref_model (
        .clk(clk),
        .rst_n(rst_n),
        .in_m(in_m),
        .goods_ref(goods_ref),
        .out_m_ref(out_m_ref)
    );
    top dut (
        .clk(clk),
        .rst_n(rst_n),
        .in_m(in_m),
        .goods(goods_dut),
        .out_m(out_m_dut)
    );

    // Clock Generation
    always #20 clk = ~clk;  // Clock toggles every 20 ns

    // Initialization Block
    initial begin
        rst_n = 1'b0;
        clk = 1'b0;
        #50 rst_n = 1'b1;  // Release reset after 50 ns
    end

    // Testbench Stimulus
    initial begin
        in_m = 4'b0000;
        #50;
        @(posedge clk);
        repeat(100) begin
            index = $urandom_range(0,2);
            in_m = m[index];
            @(posedge clk);
            compare();
        end
        repeat(100) begin
            in_m = $random;
            @(posedge clk);
            compare();
        end

        @(posedge clk);
        rst_n = 0;
        @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $finish;  // Stop simulation
    end

    // VCD Dump for Waveform Viewing
    initial begin
        $dumpfile("tb.vcd");
        $dumpvars(0, tb);
    end

    task compare;
        total_tests = total_tests + 1;

        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	$display("rst_n = %b, in_m = %b, goods_dut = %b, out_m_dut = %b, goods_ref = %b, out_m_ref = %b", rst_n, in_m, goods_dut, out_m_dut, goods_ref, out_m_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("rst_n = %b, in_m = %b, goods_dut = %b, out_m_dut = %b, goods_ref = %b, out_m_ref = %b", rst_n, in_m, goods_dut, out_m_dut, goods_ref, out_m_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask


endmodule

