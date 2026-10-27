////_____________________________________________________________________________________________________
`timescale 1ns/1ps

module tb();

reg       i_clk;
reg       clock;
reg       clk0_i;
reg       clk1_i;
reg       clk2_i;
reg       clk3_i;
reg       clk4_i;
reg       clk5_i;
reg       clk6_i;
reg       clk7_i;

reg       rst0_i;
reg       rst1_i;
reg       rst2_i;
reg       rst3_i;
reg       rst4_i;
reg       rst5_i;
reg       rst6_i;
reg       rst7_i;

reg       enable;
reg [2:0] select;

wire ref_clk_o,dut_clk_o;

real  launch_b2;
real  launch_b3;
real  launch_b4;
real  launch_b8;

real  actual_b2;
real  actual_b3;
real  actual_b4;
real  actual_b8;

real  expect_b2;
real  expect_b3;
real  expect_b4;
real  expect_b8;

   wire match;

    integer total_tests = 0;
	integer failed_tests = 0;

assign match = (ref_clk_o === (ref_clk_o ^ dut_clk_o ^ ref_clk_o));

integer passes;

    ref_clock_switch8_basic  u1(
        .ref_clk_o(ref_clk_o),
        .rst0_i(rst0_i),
        .clk0_i(clk0_i),
        .rst1_i(rst1_i),
        .clk1_i(clk1_i),
        .rst2_i(rst2_i),
        .clk2_i(clk2_i),
        .rst3_i(rst3_i),
        .clk3_i(clk3_i),
        .rst4_i(rst4_i),
        .clk4_i(clk4_i),
        .rst5_i(rst5_i),
        .clk5_i(clk5_i),
        .rst6_i(rst6_i),
        .clk6_i(clk6_i),
        .rst7_i(rst7_i),
        .clk7_i(clk7_i),
        .enable(enable),
        .select(select)
    );

    top u2(
        .clk_o(dut_clk_o),
        .rst0_i(rst0_i),
        .clk0_i(clk0_i),
        .rst1_i(rst1_i),
        .clk1_i(clk1_i),
        .rst2_i(rst2_i),
        .clk2_i(clk2_i),
        .rst3_i(rst3_i),
        .clk3_i(clk3_i),
        .rst4_i(rst4_i),
        .clk4_i(clk4_i),
        .rst5_i(rst5_i),
        .clk5_i(clk5_i),
        .rst6_i(rst6_i),
        .clk6_i(clk6_i),
        .rst7_i(rst7_i),
        .clk7_i(clk7_i),
        .enable(enable),
        .select(select)
    );

 // Clock generation
    initial begin
        i_clk = 0;
        forever #5 i_clk = ~i_clk; // 100 MHz clock
	compare();
    end

initial begin
        clk0_i = 0;
        forever #5 clk0_i = ~clk0_i;
	compare();
    end

    initial begin
        clk1_i = 0;
        forever #5 clk1_i = ~clk1_i;	
	compare();
    end

    initial begin
        clk2_i = 0;
        forever #5 clk2_i = ~clk2_i;
	compare();
    end

    initial begin
        clk3_i = 0;
        forever #5 clk3_i = ~clk3_i;
	compare();
    end

    initial begin
        clk4_i = 0;
        forever #5 clk4_i = ~clk4_i;
	compare();
    end

    initial begin
        clk5_i = 0;
        forever #5 clk5_i = ~clk5_i;
	compare();
    end

    initial begin
        clk6_i = 0;
        forever #5 clk6_i = ~clk6_i;
	compare();
    end

    initial begin
        clk7_i = 0;
        forever #5 clk7_i = ~clk7_i;
	compare();
    end

    // 
    initial begin
        rst0_i = 1; #10 rst0_i = 0;
        rst1_i = 1; #10 rst1_i = 0;
        rst2_i = 1; #10 rst2_i = 0;
        rst3_i = 1; #10 rst3_i = 0;
        rst4_i = 1; #10 rst4_i = 0;
        rst5_i = 1; #10 rst5_i = 0;
        rst6_i = 1; #10 rst6_i = 0;
        rst7_i = 1; #10 rst7_i = 0;
	compare();
    end

    //
    initial begin
        $display("Starting testbench for ref_clock_switch8_basic");
        enable = 0;
        select = 3'b000;

        // 
        for (int i = 0; i < 8; i = i + 1) begin
            select = i;
            enable = 1;
            #100;
            enable = 0;
            #100;
        end

        // 
        repeat (100) begin
            select = $random % 8;
            enable = $random % 2;
            #100;
	compare();
        end

        //
        $display("Test complete");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
		
        $finish;
    end

always #50     clock  <= ~clock;

parameter C0P = 3.00;
parameter C1P = 4.00;
parameter C2P = 5.00;
parameter C3P = 6.00;
parameter C4P = 7.00;
parameter C5P = 8.00;
parameter C6P = 9.00;
parameter C7P = 10.00;

always #(C0P/2.0) clk0_i <= ~clk0_i;
always #(C1P/2.0) clk1_i <= ~clk1_i;
always #(C2P/2.0) clk2_i <= ~clk2_i;
always #(C3P/2.0) clk3_i <= ~clk3_i;
always #(C4P/2.0) clk4_i <= ~clk4_i;
always #(C5P/2.0) clk5_i <= ~clk5_i;
always #(C6P/2.0) clk6_i <= ~clk6_i;
always #(C7P/2.0) clk7_i <= ~clk7_i;

wire  clock_b2;
wire  clock_b3;
wire  clock_b4;
wire  clock_b8;

always @( posedge clock_b2 )
begin
    actual_b2 = $realtime - launch_b2;
    launch_b2 = $realtime;
	compare();
end

always @( posedge clock_b3 )
begin
    actual_b3 = $realtime - launch_b3;
    launch_b3 = $realtime;
	compare();
end

always @( posedge clock_b4 )
begin
    actual_b4 = $realtime - launch_b4;
    launch_b4 = $realtime;
	compare();
end

always @( posedge clock_b8 )
begin
    actual_b8 = $realtime - launch_b8;
    launch_b8 = $realtime;
	compare();
end

always @( posedge clock )
begin
    case( select[0] )
    1'b0: expect_b2 = C0P;
    1'b1: expect_b2 = C1P;
    endcase

    case( select[1:0] )
    2'b00: expect_b3 = C0P;
    2'b01: expect_b3 = C1P;
    2'b10: expect_b3 = C2P;
    2'b11: expect_b3 = C3P;
    endcase

    case( select[1:0] )
    2'b00: expect_b4 = C0P;
    2'b01: expect_b4 = C1P;
    2'b10: expect_b4 = C2P;
    2'b11: expect_b4 = C3P;
    endcase

    case( select[2:0] )
    3'b000: expect_b8 = C0P;
    3'b001: expect_b8 = C1P;
    3'b010: expect_b8 = C2P;
    3'b011: expect_b8 = C3P;
    3'b100: expect_b8 = C4P;
    3'b101: expect_b8 = C5P;
    3'b110: expect_b8 = C6P;
    3'b111: expect_b8 = C7P;
    endcase

    if( (launch_b2 > 0.0) && (expect_b2 != actual_b2))
    begin
        $display( "%d: expect_b2=%f, actual_b2=%f", $time, expect_b2, actual_b2);
        $stop;
    end

    if( (launch_b3 > 0.0) && (expect_b3 != actual_b3))
    begin
        $display( "%d: expect_b3=%f, actual_b3=%f", $time, expect_b3, actual_b3);
        $stop;
    end

    if( (launch_b4 > 0.0) && (expect_b4 != actual_b4))
    begin
        $display( "%d: expect_b4=%f, actual_b4=%f", $time, expect_b4, actual_b4);
        $stop;
    end

    if( (launch_b8 > 0.0) && (expect_b8 != actual_b8))
    begin
        $display( "%d: expect_b8=%f, actual_b8=%f", $time, expect_b8, actual_b8);
        $stop;
    end

    select <= select + 1;

    passes  = passes + 1;

	  $display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
compare();
end

reg     notify;
initial notify = 0;

always @( posedge notify ) $stop;

specify
specparam c_width = 1.50;  // is C0P/2.0

// check for narrow pulses

$width( negedge clock_b8, c_width, 0, notify );
$width( posedge clock_b8, c_width, 0, notify );

endspecify

  task compare;
        total_tests = total_tests + 1;
        if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
//				$display("testcase is passed!!!");
            	//$display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
			end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            //$display("i_rst = %h, i_wr = %h, i_signed = %h, i_numerator = %h, i_denominator = %h, o_busy_dut = %h, o_valid_dut = %h, o_err_dut = %h, o_quotient_dut = %h, o_flags_dut = %h, o_busy_ref = %h, o_valid_ref = %h, o_err_ref = %h, o_quotient_ref = %h, o_flags_ref = %h)", i_rst, i_wr, i_signed, i_numerator, i_denominator, o_busy_dut, o_valid_dut, o_err_dut, o_quotient_dut, o_flags_dut, o_busy_ref, o_valid_ref, o_err_ref, o_quotient_ref, o_flags_ref);      //displaying inputs, outputs and result
            failed_tests = failed_tests + 1; 
		end
    
	endtask

endmodule
