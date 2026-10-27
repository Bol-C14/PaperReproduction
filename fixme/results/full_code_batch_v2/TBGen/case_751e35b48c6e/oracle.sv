`timescale 1ns/1ps
module oracle_omsp_register_file (
    cpuoff,                       
    gie,                          
    oscoff,                       
    pc_sw,                        
    pc_sw_wr,                     
    reg_dest,                     
    reg_src,                      
    scg1,                         
    status,                       
    alu_stat,                     
    alu_stat_wr,                  
    inst_bw,                      
    inst_dest,                    
    inst_src,                     
    mclk,                         
    pc,                           
    puc,                          
    reg_dest_val,                 
    reg_dest_wr,                  
    reg_pc_call,                  
    reg_sp_val,                   
    reg_sp_wr,                    
    reg_sr_wr,                    
    reg_sr_clr,                   
    reg_incr                      
);
output 	            cpuoff;       
output 	            gie;          
output 	            oscoff;       
output       [15:0] pc_sw;        
output              pc_sw_wr;     
output       [15:0] reg_dest;     
output       [15:0] reg_src;      
output              scg1;         
output        [3:0] status;       
input         [3:0] alu_stat;     
input         [3:0] alu_stat_wr;  
input               inst_bw;      
input        [15:0] inst_dest;    
input        [15:0] inst_src;     
input               mclk;         
input        [15:0] pc;           
input               puc;          
input        [15:0] reg_dest_val; 
input               reg_dest_wr;  
input               reg_pc_call;  
input        [15:0] reg_sp_val;   
input               reg_sp_wr;    
input               reg_sr_wr;    
input               reg_sr_clr;   
input               reg_incr;     
wire [15:0] incr_op         = inst_bw ? 16'h0001 : 16'h0002;
wire [15:0] reg_incr_val    = reg_src+incr_op;
wire [15:0] reg_dest_val_in = inst_bw ? {8'h00,reg_dest_val[7:0]} : reg_dest_val;
wire [15:0] inst_src_in = reg_sr_clr ? 16'h0004 : inst_src;
wire [15:0] r0       = pc;
wire [15:0] pc_sw    = reg_dest_val_in;
wire        pc_sw_wr = (inst_dest[0] & reg_dest_wr) | reg_pc_call;
reg [15:0] r1;
wire       r1_wr  = inst_dest[1] & reg_dest_wr;
wire       r1_inc = inst_src_in[1]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)            r1 <= 16'h0000;
  else if (r1_wr)     r1 <= reg_dest_val_in & 16'hfffe;
  else if (reg_sp_wr) r1 <= reg_sp_val      & 16'hfffe;
  else if (r1_inc)    r1 <= reg_incr_val    & 16'hfffe;
reg  [15:0] r2;
wire        r2_wr  = (inst_dest[2] & reg_dest_wr) | reg_sr_wr;
wire        r2_c   = alu_stat_wr[0] ? alu_stat[0]       :
                     r2_wr          ? reg_dest_val_in[0]   : r2[0]; 
wire        r2_z   = alu_stat_wr[1] ? alu_stat[1]       :
                     r2_wr          ? reg_dest_val_in[1]   : r2[1]; 
wire        r2_n   = alu_stat_wr[2] ? alu_stat[2]       :
                     r2_wr          ? reg_dest_val_in[2]   : r2[2]; 
wire  [7:3] r2_nxt = r2_wr          ? reg_dest_val_in[7:3] : r2[7:3];
wire        r2_v   = alu_stat_wr[3] ? alu_stat[3]       :
                     r2_wr          ? reg_dest_val_in[8]   : r2[8]; 
always @(posedge mclk or posedge puc)
  if (puc)             r2 <= 16'h0000;
  else if (reg_sr_clr) r2 <= 16'h0000;
  else                 r2 <= {7'h00, r2_v, r2_nxt, r2_n, r2_z, r2_c};
assign status = {r2[8], r2[2:0]};
assign gie    =  r2[3];
assign cpuoff =  r2[4] | (r2_nxt[4] & r2_wr);
assign oscoff =  r2[5];
assign scg1   =  r2[7];
reg [15:0] r3;
wire       r3_wr  = inst_dest[3] & reg_dest_wr;
wire       r3_inc = inst_src_in[3]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)         r3 <= 16'h0000;
  else if (r3_wr)  r3 <= reg_dest_val_in;
  else if (r3_inc) r3 <= reg_incr_val;
reg [15:0] r4;
wire       r4_wr  = inst_dest[4] & reg_dest_wr;
wire       r4_inc = inst_src_in[4]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r4  <= 16'h0000;
  else if (r4_wr)   r4  <= reg_dest_val_in;
  else if (r4_inc)  r4  <= reg_incr_val;
reg [15:0] r5;
wire       r5_wr  = inst_dest[5] & reg_dest_wr;
wire       r5_inc = inst_src_in[5]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r5  <= 16'h0000;
  else if (r5_wr)   r5  <= reg_dest_val_in;
  else if (r5_inc)  r5  <= reg_incr_val;
reg [15:0] r6;
wire       r6_wr  = inst_dest[6] & reg_dest_wr;
wire       r6_inc = inst_src_in[6]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r6  <= 16'h0000;
  else if (r6_wr)   r6  <= reg_dest_val_in;
  else if (r6_inc)  r6  <= reg_incr_val;
reg [15:0] r7;
wire       r7_wr  = inst_dest[7] & reg_dest_wr;
wire       r7_inc = inst_src_in[7]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r7  <= 16'h0000;
  else if (r7_wr)   r7  <= reg_dest_val_in;
  else if (r7_inc)  r7  <= reg_incr_val;
reg [15:0] r8;
wire       r8_wr  = inst_dest[8] & reg_dest_wr;
wire       r8_inc = inst_src_in[8]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r8  <= 16'h0000;
  else if (r8_wr)   r8  <= reg_dest_val_in;
  else if (r8_inc)  r8  <= reg_incr_val;
reg [15:0] r9;
wire       r9_wr  = inst_dest[9] & reg_dest_wr;
wire       r9_inc = inst_src_in[9]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r9  <= 16'h0000;
  else if (r9_wr)   r9  <= reg_dest_val_in;
  else if (r9_inc)  r9  <= reg_incr_val;
reg [15:0] r10;
wire       r10_wr  = inst_dest[10] & reg_dest_wr;
wire       r10_inc = inst_src_in[10]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r10 <= 16'h0000;
  else if (r10_wr)  r10 <= reg_dest_val_in;
  else if (r10_inc) r10 <= reg_incr_val;
reg [15:0] r11;
wire       r11_wr  = inst_dest[11] & reg_dest_wr;
wire       r11_inc = inst_src_in[11]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r11 <= 16'h0000;
  else if (r11_wr)  r11 <= reg_dest_val_in;
  else if (r11_inc) r11 <= reg_incr_val;
reg [15:0] r12;
wire       r12_wr  = inst_dest[12] & reg_dest_wr;
wire       r12_inc = inst_src_in[12]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r12 <= 16'h0000;
  else if (r12_wr)  r12 <= reg_dest_val_in;
  else if (r12_inc) r12 <= reg_incr_val;
reg [15:0] r13;
wire       r13_wr  = inst_dest[13] & reg_dest_wr;
wire       r13_inc = inst_src_in[13]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r13 <= 16'h0000;
  else if (r13_wr)  r13 <= reg_dest_val_in;
  else if (r13_inc) r13 <= reg_incr_val;
reg [15:0] r14;
wire       r14_wr  = inst_dest[14] & reg_dest_wr;
wire       r14_inc = inst_src_in[14]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r14 <= 16'h0000;
  else if (r14_wr)  r14 <= reg_dest_val_in;
  else if (r14_inc) r14 <= reg_incr_val;
reg [15:0] r15;
wire       r15_wr  = inst_dest[15] & reg_dest_wr;
wire       r15_inc = inst_src_in[15]  & reg_incr;
always @(posedge mclk or posedge puc)
  if (puc)          r15 <= 16'h0000;
  else if (r15_wr)  r15 <= reg_dest_val_in;
  else if (r15_inc) r15 <= reg_incr_val;
assign reg_src  = (r0      & {16{inst_src_in[0]}})   | 
                  (r1      & {16{inst_src_in[1]}})   | 
                  (r2      & {16{inst_src_in[2]}})   | 
                  (r3      & {16{inst_src_in[3]}})   | 
                  (r4      & {16{inst_src_in[4]}})   | 
                  (r5      & {16{inst_src_in[5]}})   | 
                  (r6      & {16{inst_src_in[6]}})   | 
                  (r7      & {16{inst_src_in[7]}})   | 
                  (r8      & {16{inst_src_in[8]}})   | 
                  (r9      & {16{inst_src_in[9]}})   | 
                  (r10     & {16{inst_src_in[10]}})  | 
                  (r11     & {16{inst_src_in[11]}})  | 
                  (r12     & {16{inst_src_in[12]}})  | 
                  (r13     & {16{inst_src_in[13]}})  | 
                  (r14     & {16{inst_src_in[14]}})  | 
                  (r15     & {16{inst_src_in[15]}});
assign reg_dest = (r0      & {16{inst_dest[0]}})  | 
                  (r1      & {16{inst_dest[1]}})  | 
                  (r2      & {16{inst_dest[2]}})  | 
                  (r3      & {16{inst_dest[3]}})  | 
                  (r4      & {16{inst_dest[4]}})  | 
                  (r5      & {16{inst_dest[5]}})  | 
                  (r6      & {16{inst_dest[6]}})  | 
                  (r7      & {16{inst_dest[7]}})  | 
                  (r8      & {16{inst_dest[8]}})  | 
                  (r9      & {16{inst_dest[9]}})  | 
                  (r10     & {16{inst_dest[10]}}) | 
                  (r11     & {16{inst_dest[11]}}) | 
                  (r12     & {16{inst_dest[12]}}) | 
                  (r13     & {16{inst_dest[13]}}) | 
                  (r14     & {16{inst_dest[14]}}) | 
                  (r15     & {16{inst_dest[15]}});
endmodule