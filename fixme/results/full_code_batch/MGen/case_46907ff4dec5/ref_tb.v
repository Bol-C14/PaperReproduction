 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter io = 8;

    // Inputs
    reg clk_i;
    reg rst_i;
    reg cyc_i;
    reg stb_i;
    reg adr_i;
    reg we_i;
    reg [7:0] dat_i;
    
    // Outputs
    wire [7:0] dat_o_ref, dat_o_dut;
    wire ack_o_ref, ack_o_dut;
    wire [io:1] gpio_ref, gpio_dut;
    reg [io:1] en, gpio_reg;
    
    genvar i;
    generate
        for(i = 1; i<= io; i++) begin
            assign gpio_ref[i] = en[i] ? 'bz : gpio_reg[i];
        end
    endgenerate

    generate
        for(i = 1; i<= io; i++) begin
            assign gpio_dut[i] = en[i] ? 'bz : gpio_reg[i];
        end
    endgenerate

    wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

    assign match = ({dat_o_ref, ack_o_ref, gpio_ref} === ({dat_o_ref, ack_o_ref, gpio_ref} ^ {dat_o_dut, ack_o_dut, gpio_dut} ^ {dat_o_ref, ack_o_ref, gpio_ref}));



    // Instantiate the simple_gpio module
    simple_gpio_ref #(.io(io)) ref_model (
        .clk_i(clk_i),
        .rst_i(rst_i),
        .cyc_i(cyc_i),
        .stb_i(stb_i),
        .adr_i(adr_i),
        .we_i(we_i),
        .dat_i(dat_i),
        .dat_o_ref(dat_o_ref),
        .ack_o_ref(ack_o_ref),
        .gpio_ref(gpio_ref)
    );

    top #(.io(io)) dut (
        .clk_i(clk_i),
        .rst_i(rst_i),
        .cyc_i(cyc_i),
        .stb_i(stb_i),
        .adr_i(adr_i),
        .we_i(we_i),
        .dat_i(dat_i),
        .dat_o(dat_o_dut),
        .ack_o(ack_o_dut),
        .gpio(gpio_dut)
    );


    // Clock generation
    initial begin
        clk_i = 0;
        forever #5 clk_i = ~clk_i; // 100MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rst_i = 0;
        cyc_i = 0;
        stb_i = 0;
        adr_i = 0;
        we_i = 0;
        dat_i = 8'h00;

        // Release reset
        @(posedge clk_i);
        rst_i = 1;
        cyc_i = 1;
        stb_i = 1;
        we_i = 1;
        adr_i = 0;
        dat_i = 8'hFF;
        @(posedge clk_i);
        en = 8'hFF;
        compare();
        @(posedge clk_i);
        compare();

        repeat (30) begin
            adr_i = 1;
            dat_i = $random;
            @(posedge clk_i);
            compare();
        end

        adr_i = 0;
        dat_i = 8'h0;
        en = 8'h0;
        @(posedge clk_i);
        compare();
        
        we_i = 0;
        repeat (30) begin
            gpio_reg = $random;
            @(posedge clk_i);
            compare();
        end

        repeat (36) begin
            cyc_i = $random;
            stb_i = $random;
            we_i = $random;
            adr_i = $random;
            dat_i = $random;
            gpio_reg = $random;
            @(posedge clk_i);
            if (cyc_i && stb_i && we_i &&(~adr_i)) begin
                #1;
                en = dat_i;
            end
            compare();
        end

        rst_i = 0;
        @(posedge clk_i);
        en = 8'h0;
        @(posedge clk_i);
        compare();
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
            	$display("rst_i = %b, cyc_i = %b, stb_i = %b, we_i = %b, adr_i = %b, dat_i = %b, dat_o_dut = %b, ack_o_dut = %b, gpio_dut = %b, dat_o_ref = %b, ack_o_ref = %b, gpio_ref = %b", rst_i, cyc_i, stb_i, we_i, adr_i, dat_i, dat_o_dut, ack_o_dut, gpio_dut, dat_o_ref, ack_o_ref, gpio_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            $display("rst_i = %b, cyc_i = %b, stb_i = %b, we_i = %b, adr_i = %b, dat_i = %b, dat_o_dut = %b, ack_o_dut = %b, gpio_dut = %b, dat_o_ref = %b, ack_o_ref = %b, gpio_ref = %b", rst_i, cyc_i, stb_i, we_i, adr_i, dat_i, dat_o_dut, ack_o_dut, gpio_dut, dat_o_ref, ack_o_ref, gpio_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
