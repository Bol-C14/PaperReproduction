`timescale 1ns/1ps
 
module top(
  clk_i, rst_i, cyc_i, stb_i, adr_i, we_i, dat_i, dat_o, ack_o,
  gpio
);
  parameter io = 8;            
  input         clk_i;         
  input         rst_i;         
  input         cyc_i;         
  input         stb_i;         
  input         adr_i;         
  input         we_i;          
  input  [ 7:0] dat_i;         
  output [ 7:0] dat_o;         
  output        ack_o;         
  inout  [io:1] gpio;
  reg [io:1] ctrl, line;                  
  reg [io:1] lgpio, llgpio;               
  initial
  begin
      if(io > 8)
        $display("simple_gpio: max. 8 GPIOs supported.");
  end
  wire wb_acc = cyc_i & stb_i;            
  wire wb_wr  = wb_acc & we_i;            
  always @(posedge clk_i or negedge rst_i)
    if (~rst_i)
      begin
          ctrl <= #1 {{io}{1'b0}};
          line <= #1 {{io}{1'b0}};
      end
    else if (wb_wr)
       if ( adr_i )
         line <= #1 dat_i[io-1:0];
       else
         ctrl <= #1 dat_i[io-1:0];
  reg [7:0] dat_o;
  always @(posedge clk_i)
    if ( adr_i )
      dat_o <= #1 { {{8-io}{1'b0}}, llgpio};
    else
      dat_o <= #1 { {{8-io}{1'b0}}, ctrl};
  reg ack_o;
  always @(posedge clk_i or negedge rst_i)
    if (~rst_i)
      ack_o <= #1 1'b0;
    else
      ack_o <= #1 wb_acc & !ack_o;
  always @(posedge clk_i)
    lgpio <= #1 gpio;
  always @(posedge clk_i)
    llgpio <= #1 lgpio;
  integer n;
  reg [io:1] igpio; 
  always @(ctrl or line)
    for(n=1;n<=io;n=n+1)
      igpio[n] <= ctrl[n] ? line[n] : 1'bz;
  assign gpio = igpio;
endmodule

