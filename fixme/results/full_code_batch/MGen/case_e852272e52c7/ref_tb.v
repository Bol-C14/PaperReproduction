 
`timescale 1ns / 1ps

module tb;

    // Parameters
    parameter WORD_LEN = 8;
    parameter PRESCALLER_SIZE = 8;

    // Inputs
    reg clk;
    reg rst;
    reg wr;
    reg rd;
    reg [2:0] prescaller;
    reg lsbfirst;
    reg [1:0] mode;
    reg miso;
    reg res_senderr;

    // Outputs
    wire buffempty,ref_buffempty;
    wire sck,ref_sck;
    wire mosi,ref_mosi;
    wire ss,ref_ss;
    wire senderr,ref_senderr;
    wire charreceived,ref_charreceived;

    wire       match;
    integer total_tests = 0;
    integer failed_tests = 0;

    integer [2:0] prescallerint;
    integer [7:0] prescdemux;
    integer i;
    parameter NUM_TESTS = 1000;

wire [WORD_LEN - 1:0] data, TestOut;
reg  [WORD_LEN - 1:0] TestIn;
wire Write;
assign data = (Write == 1) ? TestIn : 32'bz;

    assign match = ({ref_buffempty, ref_sck, ref_mosi, ref_ss, ref_senderr, ref_charreceived} === {buffempty, sck, mosi, ss, senderr, charreceived});

    // Instantiate the SPI Master
    top #(.WORD_LEN(WORD_LEN), .PRESCALLER_SIZE(PRESCALLER_SIZE)) uut (

        .clk(clk),
        .rst(rst),
        .data(data),
        .wr(wr),
        .rd(rd),
        .buffempty(buffempty),
        .prescaller(prescaller),
        .sck(sck),
        .mosi(mosi),
        .miso(miso),
        .ss(ss),
        .lsbfirst(lsbfirst),
        .mode(mode),
        .senderr(senderr),
        .res_senderr(res_senderr),
        .charreceived(charreceived)
    );

    ref_spi_master #(.WORD_LEN(WORD_LEN), .PRESCALLER_SIZE(PRESCALLER_SIZE)) ref_model (
        .clk(clk),
        .rst(rst),
        .data(data),
        .wr(wr),
        .rd(rd),
        .ref_buffempty(ref_buffempty),
        .prescaller(prescaller),
        .ref_sck(ref_sck),
        .ref_mosi(ref_mosi),
        .miso(miso),
        .ref_ss(ref_ss),
        .lsbfirst(lsbfirst),
        .mode(mode),
        .ref_senderr(ref_senderr),
        .res_senderr(res_senderr),
        .ref_charreceived(ref_charreceived)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        rst = 1;
        wr = 0;
        rd = 0;
        prescaller = 3'b000;
        lsbfirst = 0;
        mode = 2'b00;
        miso = 0;
        res_senderr = 0;

        // Release reset
        #10;
        rst = 0;
        #10;
        rst = 1;

        #10;
        repeat(2000) begin
          #20 // Random delay to simulate different arrival times
            rst = 0; // Randomly assert or deassert reset
             #20
            wr = $random % 2;
            rd = $random % 2;
            prescaller = $random % 8;
            lsbfirst = $random % 2;
            mode = $random % 4;
            res_senderr = $random % 2;
            miso = $random % 2;

            // Simulate continuous operations
               #200
             compare();

        end


        // Finish simulation
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
