 `timescale 1ns / 1ps

module tb;

// import "DPI-C" function void fpu_div(double a, double b);

parameter CLK_PERIOD = 10;
parameter NUM_TESTS = 100; 

// Inputs
reg clk;
reg rst;
reg enable;
reg [63:0] opa;
reg [63:0] opb;

// Outputs
wire sign,ref_sign;
wire [55:0] mantissa_7,ref_mantissa_7;
wire [11:0] exponent_out,ref_exponent_out;

wire       match;
integer total_tests = 0;
integer failed_tests = 0;

reg [0:0] ref_sign1;
reg [55:0] ref_mantissa1;
reg [11:0] ref_exponent1;
integer status;
reg [255:0] cmd; 
integer fd;
reg [255:0] line;
integer sscanf_result;

assign match = ({ref_sign, ref_mantissa_7, ref_exponent_out} === {sign, mantissa_7, exponent_out});

// Instantiate the Unit Under Test (UUT)
top uut (
    .clk(clk),
    .rst(rst),
    .enable(enable),
    .opa(opa),
    .opb(opb),
    .sign(sign),
    .mantissa_7(mantissa_7),
    .exponent_out(exponent_out)
);

ref_fpu_div ref_model (
    .clk(clk),
    .rst(rst),
    .enable(enable),
    .opa(opa),
    .opb(opb),
    .ref_sign(ref_sign),
    .ref_mantissa_7(ref_mantissa_7),
    .ref_exponent_out(ref_exponent_out)
);


    always #(CLK_PERIOD/2) clk = ~clk;

    initial begin
        clk = 0;
        rst = 1;
        enable = 0;
        opa = 64'b0;
        opb = 64'b0;
        
        #10 rst = 0;

    for (integer i = 0; i < 64; i++) begin
        #10; enable = 1; opa = 1 << i; opb = 1 << (63-i); 
        #10; enable = 0;
          #540;
    end
        
        for (int i = 0; i < NUM_TESTS; i++) begin
            opa = {$random(),$random()};
            opb = {$random(),$random()};
            enable = 1;
            #10;
                enable = 0;
            #540;
            $sformat(cmd, "./fpu_div_ref %f %f", $bitstoreal(opa), $bitstoreal(opb));
            //status = $system(cmd);

            if (status != 0) begin
                $finish;
            end
            
           fd = $fopen("ref_output.txt", "r");
            if (fd == 0) begin
                $display("Error: Unable to open reference output file.");
                $finish;
            end
            $fgets(line, fd);
            $fclose(fd);

            sscanf_result = $sscanf(line, "%b %h %d", ref_sign1, ref_mantissa1, ref_exponent1);
            if (sscanf_result != 3) begin
                $display("Error: Failed to parse reference output.");
                $finish;
            end
            compare();
            
        end

    // Display completion
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

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule

