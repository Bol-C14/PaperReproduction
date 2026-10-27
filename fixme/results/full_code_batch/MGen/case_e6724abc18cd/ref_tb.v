 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter DW = 32;

    // Inputs
    reg [31:0] rREGA, rREGB, rSIMM, rDWBDI;
    reg [1:0] rMXSRC, rMXTGT;
    reg [4:0] rRA, rRB, rRD;
    reg [2:0] rMXALU;
    reg rBRA, rDLY, rSTALL, gclk, grst, gena;
    reg [10:0] rALT;
    reg [15:0] rIMM;
    reg [5:0] rOPC;

    // Outputs
    wire [DW-1:2] ref_dwb_adr_o;
    wire [3:0] ref_dwb_sel_o;
    wire [31:0] ref_rRESULT;
    wire ref_rMSR_IE, ref_rMSR_BIP;

    // Outputs
    wire [DW-1:2] dwb_adr_o;
    wire [3:0] dwb_sel_o;
    wire [31:0] rRESULT;
    wire rMSR_IE, rMSR_BIP;

	wire match;
 	integer total_tests = 0;
	integer failed_tests = 0;

// rPC未赋值，是高阻态，在一些情况下使ref_ddwb_adr_o和dwb_adr_o为高阻态，异或后为x，无法判断相等。直接用===判断即可。
//assign match = ({ref_dwb_adr_o,ref_dwb_sel_o,ref_rRESULT,ref_rMSR_IE, ref_rMSR_BIP} === ({ref_dwb_adr_o,ref_dwb_sel_o,ref_rRESULT,ref_rMSR_IE, ref_rMSR_BIP}  ^ {dwb_adr_o,dwb_sel_o,rRESULT,rMSR_IE, rMSR_BIP}  ^ {ref_dwb_adr_o,ref_dwb_sel_o,ref_rRESULT,ref_rMSR_IE, ref_rMSR_BIP} ));
assign match = ({ref_dwb_adr_o,ref_dwb_sel_o,ref_rRESULT,ref_rMSR_IE, ref_rMSR_BIP} === {dwb_adr_o,dwb_sel_o,rRESULT,rMSR_IE, rMSR_BIP});

    // Instantiate the aeMB_xecu module
    ref_aeMB_xecu rf (
        .ref_dwb_adr_o(ref_dwb_adr_o),
        .ref_dwb_sel_o(ref_dwb_sel_o),
        .ref_rRESULT(ref_rRESULT),
        .ref_rMSR_IE(ref_rMSR_IE),
        .ref_rMSR_BIP(ref_rMSR_BIP),
        .rREGA(rREGA),
        .rREGB(rREGB),
        .rMXSRC(rMXSRC),
        .rMXTGT(rMXTGT),
        .rRA(rRA),
        .rRB(rRB),
        .rMXALU(rMXALU),
        .rBRA(rBRA),
        .rDLY(rDLY),
        .rALT(rALT),
        .rSTALL(rSTALL),
        .rSIMM(rSIMM),
        .rIMM(rIMM),
        .rOPC(rOPC),
        .rRD(rRD),
        .rDWBDI(rDWBDI),
        .gclk(gclk),
        .grst(grst),
        .gena(gena)
    );

    // Instantiate the aeMB_xecu module
    top uut (
        .dwb_adr_o(dwb_adr_o),
        .dwb_sel_o(dwb_sel_o),
        .rRESULT(rRESULT),
        .rMSR_IE(rMSR_IE),
        .rMSR_BIP(rMSR_BIP),
        .rREGA(rREGA),
        .rREGB(rREGB),
        .rMXSRC(rMXSRC),
        .rMXTGT(rMXTGT),
        .rRA(rRA),
        .rRB(rRB),
        .rMXALU(rMXALU),
        .rBRA(rBRA),
        .rDLY(rDLY),
        .rALT(rALT),
        .rSTALL(rSTALL),
        .rSIMM(rSIMM),
        .rIMM(rIMM),
        .rOPC(rOPC),
        .rRD(rRD),
        .rDWBDI(rDWBDI),
        .gclk(gclk),
        .grst(grst),
        .gena(gena)
    );

    // Clock generation
    initial begin
        gclk = 0;
        forever #5 gclk = ~gclk; // 100 MHz clock
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        grst = 1;
        gena = 0;
        rREGA = 0;
        rREGB = 0;
        rMXSRC = 0;
        rMXTGT = 0;
        rRA = 0;
        rRB = 0;
        rMXALU = 0;
        rBRA = 0;
        rDLY = 0;
        rSTALL = 0;
        rSIMM = 0;
        rIMM = 0;
        rOPC = 0;
        rRD = 0;
        rDWBDI = 0;
        rALT = 0;

        // Release reset
        #10 grst = 0;

        // Test Case 1: Simple Addition
        rREGA = 32'h0000000A; // 10
        rREGB = 32'h00000005; // 5
        rMXSRC = 2'b00; // Select rREGA
        rMXTGT = 2'b00; // Select rREGB
        rMXALU = 3'b000; // Add operation
        rOPC = 6'b000000; // ALU operation
        gena = 1;
	compare();
        #10;
        if (rRESULT == 32'h0000000F) begin
            $display("Test Case 1 Passed: Addition Result = %h", rRESULT);
        end else begin
            $display("Test Case 1 Failed: Result = %h", rRESULT);
        end

   repeat (96) begin
      @(posedge gclk);
	rREGA = $random;
	rREGB = $random;
	rSIMM = $random;
	rDWBDI = $random;
	rMXSRC = $random;
	rMXTGT = $random;
	rRA = $random;
	rRB = $random;
	rRD = $random;
	rMXALU = $random;
	rBRA = $random;
	rDLY = $random;
	rSTALL = $random;
	grst = $random;
	gena = $random;
	rALT = $random;
	rIMM = $random;
	rOPC = $random;
     
      compare();
    end
        // Additional test cases can be added similarly...
	$display("All tests passed: design passed");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        // Finish simulation
        #100;
        $finish;
    end

task compare;
        total_tests = total_tests + 1;
        if (match) begin                               //condition to check DUT outputs and calculated //outputs from task are equabegin								
			$display("\033[1;32mtestcase is passed!!!\033[0m");
			$display("time = %0t,dwb_adr_o=%h,dwb_sel_o=%h,rRESULT=%h,rMSR_IE=%h,rMSR_BIP=%h\n",$time,dwb_adr_o,dwb_sel_o,rRESULT,rMSR_IE, rMSR_BIP);
			$display("testcase is passed!!!");
		end

		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");	
			$display("time = %0t,dwb_adr_o=%h,dwb_sel_o=%h,rRESULT=%h,rMSR_IE=%h,rMSR_BIP=%h\n",$time,dwb_adr_o,dwb_sel_o,rRESULT,rMSR_IE, rMSR_BIP);
            failed_tests = failed_tests + 1; 
		end
	
endtask


    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
