`timescale 1ns / 1ps

module tb;

  // Inputs
  reg rst_i;
  reg clk_i;
  reg stb_i;
  reg we_i;
  reg [31:0] dat_i;
  reg [2:0] adr_i;
  reg MISO;

  // Outputs
  wire [31:0] dat_o,ref_dat_o;
  wire int_o,ref_int_o;
  wire SCLK,ref_SCLK;
  wire MOSI,ref_MOSI;

wire       match;
integer    total_tests = 0;
integer    failed_tests = 0;
integer    txr;
integer    txren;

integer       bc;
integer       bc_next;
integer       sck;
integer       sf;
integer       cpol;
integer       cpha;
integer       cyc_i;

assign match = ({ref_dat_o, ref_int_o, ref_SCLK, ref_MOSI} === {dat_o, int_o, SCLK, MOSI});

  top uut (
    .rst_i(rst_i), 
    .clk_i(clk_i), 
    .stb_i(stb_i), 
    .we_i(we_i), 
    .dat_o(dat_o), 
    .dat_i(dat_i), 
    .int_o(int_o), 
    .adr_i(adr_i), 
    .MOSI(MOSI), 
    .SCLK(SCLK), 
    .MISO(MISO)
  );

  ref_tiny_spi ref_model (
    .rst_i(rst_i), 
    .clk_i(clk_i), 
    .stb_i(stb_i), 
    .we_i(we_i), 
    .ref_dat_o(ref_dat_o), 
    .dat_i(dat_i), 
    .ref_int_o(ref_int_o), 
    .adr_i(adr_i), 
    .ref_MOSI(ref_MOSI), 
    .ref_SCLK(ref_SCLK), 
    .MISO(MISO)
  );

  always #5 clk_i = ~clk_i; 

  initial begin
    rst_i = 1;
    clk_i = 0;
    stb_i = 0;
    we_i = 0;
    dat_i = 0;
    adr_i = 0;
    MISO = 0;
    #10;
    rst_i = 0; 

    stb_i = 1; we_i = 1; adr_i = 0; dat_i = 32'hA5A5A5A5; #10;
    stb_i = 1; we_i = 0; adr_i = 0; #10;
    check_value(dat_o, 32'hA5A5A5A5, "Read register 0 failed");
    compare();


    stb_i = 1; we_i = 1; adr_i = 3; dat_i = 32'h00000001; #10;
    stb_i = 1; we_i = 1; adr_i = 1; dat_i = 32'hA5A5A5A5; #10;
    check_SPI_signals(1);
    compare();


    stb_i = 1; we_i = 1; adr_i = 2; dat_i = 32'h00000003; #10;
    check_interrupt();
    compare();

    toggle_signals();
    compare();

    repeat (2000) begin
       #10;
       bc = uut.bc;
       bc_next = uut.bc_next;
       sck = uut.sck;
       sf = uut.sf;
       cpol = uut.cpol;
       cpha = uut.cpha;
       cyc_i = uut.cyc_i;
       #10;
       rst_i = 0;
       stb_i = $random;
       we_i = $random;
       dat_i = $random;
       adr_i = $random % 8;
       MISO = $random;

       bc = $random % 8;
       bc_next = $random;
       sck = $random;
       sf = $random;
       cpol = $random;
       cpha = $random;
       cyc_i = $random;

       #10;
       compare();
    end


      $display("\033[1;34mAll tests completed.\033[0m");
      $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	  $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
      $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish;
  end

  task check_value;
    input [31:0] expected;
    input [31:0] actual;
    input string message;
    begin
      if (actual !== expected) begin
        $display("%s at time %t", message, $time);
      end
    end
  endtask

  task check_SPI_signals;
    input [31:0] mode;
    begin
      case (mode)
        1: begin // CPOL=0, CPHA=1
          #10;
          if (MOSI !== 1'b0) begin
            $display("MOSI should be low on SCLK rising edge in mode 1 at time %t", $time);
          end
          #10;
          if (MOSI !== 1'b1) begin
            $display("MOSI should be high on SCLK falling edge in mode 1 at time %t", $time);
          end
        end
      endcase
    end
  endtask

  task check_interrupt;
    begin
      force uut.txr = txr;
      force ref_model.txr = txr;
      force uut.txren = txren;
      force ref_model.txren = txren;
      if (txr && txren) begin
        if (int_o !== 1'b1) begin
          $display("Interrupt should be high when txr and txren are high at time %t", $time);
        end
      end
        #10;
      release uut.txr;
      release uut.txren;
      release ref_model.txr;
      release ref_model.txren;
    end
  endtask


  task toggle_signals;
    begin
      rst_i = ~rst_i;
      stb_i = ~stb_i;
      we_i = ~we_i;
      dat_i = ~dat_i;
      adr_i = ~adr_i;
      MISO = ~MISO;
    end
  endtask

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

endmodule
