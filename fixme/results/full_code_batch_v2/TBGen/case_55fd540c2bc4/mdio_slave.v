`timescale 1ns/1ps

module mdio_slave (reset,
   mdc,
   mdio,
   dev_addr,
   reg_addr,
   reg_read,
   reg_write,
   reg_dout,
   reg_din);
input   reset; 
input   mdc; 
inout   mdio; 
input   [4:0] dev_addr; 
output   [4:0] reg_addr; 
output   reg_read; 
output   reg_write; 
output   [15:0] reg_dout; 
input   [15:0] reg_din; 
wire    VHDL2V_mdio; 
wire    mdio; 
wire    [4:0] reg_addr; 
wire    reg_read; 
wire    reg_write; 
wire    [15:0] reg_dout; 
reg     [4:0] phy_add; 
reg     [4:0] reg_add; 
reg     [15:0] reg_out; 
reg     [15:0] reg_in; 
reg     en_phy_add; 
reg     en_reg_add; 
reg     en_data_out; 
wire    en_data_in; 
wire    shift_data_in; 
wire    phy_add_ok; 
reg     [4:0] cnt_32; 
wire    run_cnt_32; 
wire    ok_32; 
wire    ok_16; 
wire    ok_10; 
wire    ok_5; 
reg     cd_oe; 
wire    mux_0; 
reg     mdio_wait; 
reg     [16:0] mdio_run; 
always @(posedge mdc or posedge reset)
   begin : p_data
   if (reset == 1'b 1)
      begin
      phy_add <= {5{1'b 0}};    
      reg_add <= {5{1'b 0}};    
      reg_out <= {16{1'b 0}};   
      reg_in <= {16{1'b 0}};    
      cnt_32 <= {5{1'b 0}}; 
      end
   else
      begin
      if (en_phy_add == 1'b 1)
         begin
         phy_add[4:0] <= {phy_add[3:0], mdio};  
         end
      else
         begin
         phy_add <= phy_add;    
         end
      if (en_reg_add == 1'b 1)
         begin
         reg_add[4:0] <= {reg_add[3:0], mdio};  
         end
      else
         begin
         reg_add <= reg_add;    
         end
      if (en_data_out == 1'b 1)
         begin
         reg_out[15:0] <= {reg_out[14:0], mdio};    
         end
      else
         begin
         reg_out <= reg_out;    
         end
      if (en_data_in == 1'b 1)
         begin
         reg_in[15:0] <= reg_din;   
         end
      else if (shift_data_in == 1'b 1 )
         begin
         reg_in[15:1] <= reg_in[14:0];  
         end
      else
         begin
         reg_in <= reg_in;  
         end
      if (run_cnt_32 == 1'b 1)
         begin
         cnt_32 <= cnt_32 + 1'b 1;  
         end
      else
         begin
         cnt_32 <= 5'b 00000;   
         end
      end
   end
assign phy_add_ok = phy_add == dev_addr ? 1'b 1 : 
    1'b 0; 
assign ok_32 = cnt_32 == 5'b 11110 ? 1'b 1 : 
    1'b 0; 
assign ok_16 = cnt_32 == 5'b 01111 ? 1'b 1 : 
    1'b 0; 
assign ok_10 = cnt_32 == 5'b 01010 ? 1'b 1 : 
    1'b 0; 
assign ok_5 = cnt_32 == 5'b 00101 ? 1'b 1 : 
    1'b 0; 
assign reg_addr = reg_add; 
assign reg_dout = reg_out; 
assign mux_0 = mdio_run[8] == 1'b 1 ? 1'b 0 : 
    reg_in[15]; 
assign #(5) mdio = cd_oe == 1'b 0 ? mux_0 : 
    1'b Z; 
always @(posedge mdc or posedge reset)
   begin : p_state
   if (reset == 1'b 1)
      begin
      mdio_wait <= 1'b 1;   
      mdio_run <= {17{1'b 0}};  
      cd_oe <= 1'b 1;   
      en_phy_add <= 1'b 0;  
      en_reg_add <= 1'b 0;  
      en_data_out <= 1'b 0; 
      end
   else
      begin
      if (mdio_wait == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[0] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[2] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[4] == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[6] == 1'b 1 & phy_add_ok == 1'b 0 | 
    mdio_run[7] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[9] == 1'b 1 & ok_16 == 1'b 1 | 
    mdio_run[10] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[12] == 1'b 1 & phy_add_ok == 1'b 0 | 
    mdio_run[13] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[14] == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[16] == 1'b 1 | mdio_run[0] == 1'b 0 & 
    mdio_run[1] == 1'b 0 & mdio_run[2] == 1'b 0 & 
    mdio_run[3] == 1'b 0 & mdio_run[4] == 1'b 0 & 
    mdio_run[5] == 1'b 0 & mdio_run[6] == 1'b 0 & 
    mdio_run[7] == 1'b 0 & mdio_run[8] == 1'b 0 & 
    mdio_run[9] == 1'b 0 & mdio_run[10] == 1'b 0 & 
    mdio_run[11] == 1'b 0 & mdio_run[12] == 1'b 0 & 
    mdio_run[13] == 1'b 0 & mdio_run[14] == 1'b 0 & 
    mdio_run[15] == 1'b 0 & mdio_run[16] == 1'b 0)
         begin
         mdio_wait <= 1'b 1;    
         end
      else
         begin
         mdio_wait <= 1'b 0;    
         end
      if (mdio_wait == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[0] == 1'b 1 & mdio == 1'b 1 & 
    ok_32 == 1'b 0)
         begin
         mdio_run[0] <= 1'b 1;  
         end
      else
         begin
         mdio_run[0] <= 1'b 0;  
         end
      if (mdio_run[0] == 1'b 1 & mdio == 1'b 1 & 
    ok_32 == 1'b 1 | mdio_run[1] == 1'b 1 & 
    mdio == 1'b 1)
         begin
         mdio_run[1] <= 1'b 1;  
         end
      else
         begin
         mdio_run[1] <= 1'b 0;  
         end
      if (mdio_run[1] == 1'b 1 & mdio == 1'b 0)
         begin
         mdio_run[2] <= 1'b 1;  
         end
      else
         begin
         mdio_run[2] <= 1'b 0;  
         end
      if (mdio_run[2] == 1'b 1 & mdio == 1'b 1)
         begin
         mdio_run[3] <= 1'b 1;  
         end
      else
         begin
         mdio_run[3] <= 1'b 0;  
         end
      if (mdio_run[3] == 1'b 1 & mdio == 1'b 1)
         begin
         mdio_run[4] <= 1'b 1;  
         end
      else
         begin
         mdio_run[4] <= 1'b 0;  
         end
      if (mdio_run[4] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[5] == 1'b 1 & ok_5 == 1'b 0)
         begin
         mdio_run[5] <= 1'b 1;  
         end
      else
         begin
         mdio_run[5] <= 1'b 0;  
         end
      if (mdio_run[5] == 1'b 1 & ok_5 == 1'b 1 | 
    mdio_run[6] == 1'b 1 & ok_10 == 1'b 0 & 
    phy_add_ok == 1'b 1)
         begin
         mdio_run[6] <= 1'b 1;  
         end
      else
         begin
         mdio_run[6] <= 1'b 0;  
         end
      if (mdio_run[6] == 1'b 1 & ok_10 == 1'b 1 & 
    phy_add_ok == 1'b 1)
         begin
         mdio_run[7] <= 1'b 1;  
         end
      else
         begin
         mdio_run[7] <= 1'b 0;  
         end
      if (mdio_run[7] == 1'b 1 & mdio != 1'b 0)
         begin
         mdio_run[8] <= 1'b 1;  
         end
      else
         begin
         mdio_run[8] <= 1'b 0;  
         end
      if (mdio_run[8] == 1'b 1 | mdio_run[9] == 1'b 1 & 
    ok_16 == 1'b 0)
         begin
         mdio_run[9] <= 1'b 1;  
         end
      else
         begin
         mdio_run[9] <= 1'b 0;  
         end
      if (mdio_run[3] == 1'b 1 & mdio == 1'b 0)
         begin
         mdio_run[10] <= 1'b 1; 
         end
      else
         begin
         mdio_run[10] <= 1'b 0; 
         end
      if (mdio_run[10] == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[11] == 1'b 1 & ok_5 == 1'b 0)
         begin
         mdio_run[11] <= 1'b 1; 
         end
      else
         begin
         mdio_run[11] <= 1'b 0; 
         end
      if (mdio_run[11] == 1'b 1 & ok_5 == 1'b 1 | 
    mdio_run[12] == 1'b 1 & ok_10 == 1'b 0 & 
    phy_add_ok == 1'b 1)
         begin
         mdio_run[12] <= 1'b 1; 
         end
      else
         begin
         mdio_run[12] <= 1'b 0; 
         end
      if (mdio_run[12] == 1'b 1 & ok_10 == 1'b 1 & 
    phy_add_ok == 1'b 1)
         begin
         mdio_run[13] <= 1'b 1; 
         end
      else
         begin
         mdio_run[13] <= 1'b 0; 
         end
      if (mdio_run[13] == 1'b 1 & mdio == 1'b 1)
         begin
         mdio_run[14] <= 1'b 1; 
         end
      else
         begin
         mdio_run[14] <= 1'b 0; 
         end
      if (mdio_run[14] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[15] == 1'b 1 & ok_16 == 1'b 0)
         begin
         mdio_run[15] <= 1'b 1; 
         end
      else
         begin
         mdio_run[15] <= 1'b 0; 
         end
      if (mdio_run[15] == 1'b 1 & ok_16 == 1'b 1)
         begin
         mdio_run[16] <= 1'b 1; 
         end
      else
         begin
         mdio_run[16] <= 1'b 0; 
         end
      if (mdio_run[4] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[5] == 1'b 1 & ok_5 == 1'b 0 | 
    mdio_run[10] == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[11] == 1'b 1 & ok_5 == 1'b 0)
         begin
         en_phy_add <= 1'b 1;   
         end
      else
         begin
         en_phy_add <= 1'b 0;   
         end
      if (mdio_run[5] == 1'b 1 & ok_5 == 1'b 1 | 
    mdio_run[6] == 1'b 1 & ok_10 == 1'b 0 | 
    mdio_run[11] == 1'b 1 & ok_5 == 1'b 1 | 
    mdio_run[12] == 1'b 1 & ok_10 == 1'b 0)
         begin
         en_reg_add <= 1'b 1;   
         end
      else
         begin
         en_reg_add <= 1'b 0;   
         end
      if (mdio_run[14] == 1'b 1 & mdio == 1'b 0 | 
    mdio_run[15] == 1'b 1 & ok_16 == 1'b 0)
         begin
         en_data_out <= 1'b 1;  
         end
      else
         begin
         en_data_out <= 1'b 0;  
         end
      if (mdio_run[7] == 1'b 1 & mdio != 1'b 0 | 
    mdio_run[8] == 1'b 1 | mdio_run[9] == 1'b 1 & 
    ok_16 == 1'b 0)
         begin
         cd_oe <= 1'b 0;    
         end
      else
         begin
         cd_oe <= 1'b 1;    
         end
      end
   end
assign en_data_in = mdio_run[8]; 
assign shift_data_in = mdio_run[9]; 
assign reg_read = mdio_run[7] == 1'b 1 & mdio != 1'b 0 | 
    mdio_run[8] == 1'b 1 ? 1'b 1 : 
    1'b 0; 
assign reg_write = mdio_run[16]; 
assign run_cnt_32 = mdio_wait == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[0] == 1'b 1 & mdio == 1'b 1 & 
    ok_32 == 1'b 0 | mdio_run[4] == 1'b 1 & 
    mdio == 1'b 0 | mdio_run[5] == 1'b 1 & 
    ok_5 == 1'b 0 | mdio_run[5] == 1'b 1 & 
    ok_5 == 1'b 1 | mdio_run[6] == 1'b 1 & 
    ok_10 == 1'b 0 | mdio_run[9] == 1'b 1 | 
    mdio_run[10] == 1'b 1 & mdio == 1'b 1 | 
    mdio_run[11] == 1'b 1 & ok_5 == 1'b 0 | 
    mdio_run[11] == 1'b 1 & ok_5 == 1'b 1 | 
    mdio_run[12] == 1'b 1 & ok_10 == 1'b 0 | 
    mdio_run[15] == 1'b 1 & ok_16 == 1'b 0 ? 1'b 1 : 
    1'b 0; 
endmodule
