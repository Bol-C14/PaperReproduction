 `timescale 1ns / 1ps

module tb;

    // Parameters
    parameter CLK_PERIOD = 10; // Clock period
    parameter   operation_mode = "DUAL_PORT" ;
    parameter   output_mode    = "REG"       ;

    // Inputs
    reg clk_a;
    reg clk_b;
    reg we_a;
    reg we_b;
    reg ena_a;
    reg ena_b;
    reg signed [31:0] data_in_a;
    reg signed [31:0] data_in_b;
    reg [13:0] addr_a;
    reg [13:0] addr_b;

    // Outputs
    wire [31:0] data_out_a, ref_data_out_a;
    wire [31:0] data_out_b, ref_data_out_b;

wire       match;
integer    total_tests = 0;
integer    failed_tests = 0;

assign match = ({ref_data_out_a, ref_data_out_b} === ({ref_data_out_a, ref_data_out_b} ^ {data_out_a, data_out_b} ^ {ref_data_out_a, ref_data_out_b}));

    // Instantiate the alt_exc_dpram module
    top #(
            .operation_mode(operation_mode),
            .output_mode(output_mode)
         )uut (
        .portadatain(data_in_a),
        .portadataout(data_out_a),
        .portaaddr(addr_a),
        .portawe(we_a),
        .portaena(ena_a),
        .portaclk(clk_a),
        .portbdatain(data_in_b),
        .portbdataout(data_out_b),
        .portbaddr(addr_b),
        .portbwe(we_b),
        .portbena(ena_b),
        .portbclk(clk_b)
    );

    ref_alt_exc_dpram #(
            .operation_mode(operation_mode),
            .output_mode(output_mode)
         )ref_model (
        .portadatain(data_in_a),
        .ref_portadataout(ref_data_out_a),
        .portaaddr(addr_a),
        .portawe(we_a),
        .portaena(ena_a),
        .portaclk(clk_a),
        .portbdatain(data_in_b),
        .ref_portbdataout(ref_data_out_b),
        .portbaddr(addr_b),
        .portbwe(we_b),
        .portbena(ena_b),
        .portbclk(clk_b)
    );

    // Generate clock signals
    initial begin
        clk_a = 0;
        clk_b = 0;
        forever #(CLK_PERIOD / 2) begin
            clk_a = ~clk_a;
            clk_b = ~clk_b;
        end
    end

    // Test Procedure
    initial begin
        // Initialize inputs
        we_a = 0;
        we_b = 0;
        ena_a = 0;
        ena_b = 0;
        data_in_a = 0;
        data_in_b = 0;
        addr_a = 0;
        addr_b = 0;
           
          #10;
        we_a = 1;
        we_b = 1;
        ena_a = 1;
        ena_b = 1;
         
          #10;
        we_a = 0;
        we_b = 0;
        ena_a = 0;
        ena_b = 0;

           #10;

        // Test Case 1: Write to port A and read from port A
        addr_a = 14'h3FFF;
        data_in_a = 32'hDEADBEEF;
        we_a = 1;
        ena_a = 1;
         #50;
        we_a = 0; // Stop writing
         #50;
        
        // Check data out from port A
            compare();

        // Test Case 2: Write to port B and read from port A
        addr_b = 14'h3FFF;
        data_in_b = 32'hBEEFCAFE;
        we_b = 1;
        ena_b = 1;
          #50;
        we_b = 0; // Stop writing
         #50;
        
        // Check data out from port A (should be unchanged)
           compare();


        // Test Case 3: Read from port B
        addr_b = 14'h0002;
        ena_b = 1;
         #50;
        
        // Check data out from port B
            compare();


        // Test Case 4: Simultaneous read and write
        addr_a = 14'h0002;
        data_in_a = 32'hFACEB00C;
        we_a = 1;
        ena_a = 1;
         #50;
        
        // Check data out from both ports
            compare();
  
          //Test Case 5: Write the same address
            we_a = 1;
            ena_a = 1;
            data_in_a = $random;
            addr_a = 100;
            we_b = 1;
            ena_b = 1;
            data_in_b = $random;
            addr_b = 100;
               #100;
            compare();

       //Test Case 6: Read the same address
            we_a = 0;
            ena_a = 1;
            data_in_a = $random;
            addr_a = 100;
            we_b = 0;
            ena_b = 1;
            data_in_b = $random;
            addr_b = 100;
               #100;
            compare();


 for (int i=0; i<97; i++) begin
            we_a = 1;
            ena_a = 1;
            data_in_a = $random;
            addr_a = i;
            we_b = 1;
            ena_b = 1;
            data_in_b = $random;
            addr_b = i+100;
               #10;
            compare();
 end

 for (int i=0; i<97; i++) begin
            we_a = 0;
            ena_a = 1;
            data_in_a = $random;
            addr_a = i;
            we_b = 0;
            ena_b = 1;
            data_in_b = $random;
            addr_b = i+100;
               #10;
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

    initial begin
        /* omitted diagnostic FSDB output: $fsdbDumpfile("sim.fsdb"); */
        /* omitted diagnostic FSDB output: $fsdbDumpvars(); */
    end


endmodule
