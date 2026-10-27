            
`timescale 1ns/10ps
`define CYCLE_TIME 10.0          	  // Modify your clock period here
`define SDFFILE    "WIN.sdf"	  // Modify your sdf file name
`define End_CYCLE  300             // Modify cycle times once your design need more cycle times!


module tb;

`ifdef SDF
	initial $sdf_annotate(`SDFFILE, CPU);
`endif


//input signal 
reg        clk_i           ;
reg        DataOrReg       ;
reg [4:0]  address         ;
reg [7:0]  instr_i         ;
reg        reset           ;
reg [1:0]  vout_addr       ;

//output signal
wire [7:0]    	value_o_ref     ;
wire  		  	is_positive_ref ;
wire [2:0]  	easter_egg_ref  ;

wire [7:0]    	value_o     ;
wire  		  	is_positive ;
wire [2:0]  	easter_egg  ;

    integer total_tests  = 0;
	integer failed_tests = 0;

    wire match;
	reg [11:0] ref_out;
	reg [11:0] dut_out;

	assign ref_out = {value_o_ref,is_positive_ref,easter_egg_ref};
	assign dut_out = {value_o,is_positive,easter_egg};

	assign match = (ref_out === ref_out^dut_out^ref_out);

  

top CPU(
    .clk_i       ( clk_i       ) ,
    .DataOrReg   ( DataOrReg   ) ,
    .address     ( address     ) ,
    .instr_i     ( instr_i     ) ,
    .reset       ( reset       ) ,
    .vout_addr   ( vout_addr   ) ,
    .value_o     ( value_o     ) ,
    .is_positive ( is_positive ) ,
    .easter_egg  ( easter_egg  )
);


CPU_ref CPU_ref(
    .clk_i           ( clk_i           ) ,
    .DataOrReg       ( DataOrReg       ) ,
    .address         ( address         ) ,
    .instr_i         ( instr_i         ) ,
    .reset           ( reset           ) ,
    .vout_addr       ( vout_addr       ) ,
    .value_o_ref     ( value_o_ref     ) ,
    .is_positive_ref ( is_positive_ref ) ,
    .easter_egg_ref  ( easter_egg_ref  )
);



always #5  clk_i = ~clk_i;  

initial begin
	clk_i     = 0;
    reset     = 1; 

    DataOrReg = 0; 
    address   = 0; 
    instr_i   = 0; 
    vout_addr = 0; 
	#20;
	reset = 0;
    DataOrReg = 'd1; 
    address   = 'd1; 
    instr_i   = 'd1; 
    vout_addr = 'd1;
	#10;	
	compare();
	#10;

	repeat(100) begin
    DataOrReg = $random; 
    address   = $random; 
    instr_i   = $random; 
    vout_addr = $random;
	#10;	
	compare();
	#10;
	end

    #1000;
    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
end





    task compare;
        total_tests = total_tests + 1;
        if (match)                               
			begin
				$display("\033[1;32mtestcase is passed!!!\033[0m");
            end
		else begin
			$display("\033[1;31mtestcase is failed!!!\033[0m");
            failed_tests = failed_tests + 1; 
		end
	endtask

initial begin
      $fsdbDumpfile("sim.fsdb");
      $fsdbDumpvars();
	  $fsdbDumpMDA();
end


  


  
endmodule

