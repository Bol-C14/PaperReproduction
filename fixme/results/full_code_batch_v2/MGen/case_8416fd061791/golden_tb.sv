 `timescale 1ns / 1ps

module tb;

// Inputs
reg clk;
reg reset;
reg [31:0] dat;
reg [6:0] addr;
reg we;

// Outputs
wire busy,ref_busy;
wire [3:0] SF_D,ref_SF_D;
wire LCD_E,ref_LCD_E;
wire LCD_RS,ref_LCD_RS;
wire LCD_RW,ref_LCD_RW;

wire       match;

integer total_tests = 0;
integer failed_tests = 0;
integer wee;

assign match = ({ref_busy,ref_SF_D,ref_LCD_E,ref_LCD_RS,ref_LCD_RW} === {busy,SF_D,LCD_E,LCD_RS,LCD_RW});



// Instantiate the Unit Under Test (UUT)
top uut (
    .clk(clk),
    .reset(reset),
    .dat(dat),
    .addr(addr),
    .we(we),
    .busy(busy),
    .SF_D(SF_D),
    .LCD_E(LCD_E),
    .LCD_RS(LCD_RS),
    .LCD_RW(LCD_RW)
);

ref_lcd ref_model (
    .clk(clk),
    .reset(reset),
    .dat(dat),
    .addr(addr),
    .we(we),
    .ref_busy(ref_busy),
    .ref_SF_D(ref_SF_D),
    .ref_LCD_E(ref_LCD_E),
    .ref_LCD_RS(ref_LCD_RS),
    .ref_LCD_RW(ref_LCD_RW)
);

    always #5 clk = ~clk;

    initial begin
        clk = 0;
        reset = 1;
        dat = 0;
        addr = 0;
        we = 0;

        #10;
        reset = 0;
        #10;


        repeat (400) begin

            we = $random % 2;
            addr = $random % 128;
            dat = $random;
            wee = $random% 32;
           
            #10;
            //check_state(wee);
            //$display("delay_done = %h)", uut.delay_done); 
            compare();
        end
        #10;
        reset = 1;
        #10;
           
        #100;
    // Display completion
    $display("All tests completed.");
    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
end

    task compare;
        total_tests = total_tests + 1;
        // wait (o_valid_dut == 1);
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

    task check_state;
        input [4:0] expected_state;
        // expected_state = $random % 32;
        uut.state = expected_state;
        ref_model.state = expected_state;
    endtask


    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

