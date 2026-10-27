`timescale 1ns/1ps
module ct_lsu_pfu_sdb_cmp(
  cp0_lsu_icg_en,
  cp0_yy_clk_en,
  cpurst_b,
  entry_addr0_act,
  entry_addr_cmp_info_vld,
  entry_check_stride_success,
  entry_clk,
  entry_create_dp_vld,
  entry_create_gateclk_en,
  entry_normal_stride,
  entry_pf_inst_vld,
  entry_stride,
  entry_stride_keep,
  entry_stride_neg,
  entry_strideh_6to0,
  entry_vld,
  forever_cpuclk,
  ld_da_iid,
  pad_yy_icg_scan_en,
  pipe_va,
  rtu_yy_xx_commit0,
  rtu_yy_xx_commit0_iid,
  rtu_yy_xx_commit1,
  rtu_yy_xx_commit1_iid,
  rtu_yy_xx_commit2,
  rtu_yy_xx_commit2_iid,
  rtu_yy_xx_flush
);
input           cp0_lsu_icg_en;
input           cp0_yy_clk_en;
input           cpurst_b;
input           entry_addr0_act;
input           entry_clk;
input           entry_create_dp_vld;
input           entry_create_gateclk_en;
input           entry_pf_inst_vld;
input           entry_stride_keep;
input           entry_vld;
input           forever_cpuclk;
input   [6 :0]  ld_da_iid;
input           pad_yy_icg_scan_en;
input   [39:0]  pipe_va;
input           rtu_yy_xx_commit0;
input   [6 :0]  rtu_yy_xx_commit0_iid;
input           rtu_yy_xx_commit1;
input   [6 :0]  rtu_yy_xx_commit1_iid;
input           rtu_yy_xx_commit2;
input   [6 :0]  rtu_yy_xx_commit2_iid;
input           rtu_yy_xx_flush;
output          entry_addr_cmp_info_vld;
output          entry_check_stride_success;
output          entry_normal_stride;
output  [10:0]  entry_stride;
output          entry_stride_neg;
output  [6 :0]  entry_strideh_6to0;
parameter PA_WIDTH = 40;   
reg     [39:0]  entry_addr_0;
reg     [39:0]  entry_addr_1;
reg     [39:0]  entry_addr_2;
reg             entry_addr_cmp_info_vld;
reg     [2 :0]  entry_addr_vld;
reg     [2 :0]  entry_cmit;
reg     [6 :0]  entry_iid_0;
reg     [6 :0]  entry_iid_1;
reg     [6 :0]  entry_iid_2;
reg     [10:0]  entry_stride;
reg             entry_stride_0to1_neg_cross_2k;
reg             entry_stride_0to1_pos_cross_2k;
reg             entry_stride_0to1_zero;
reg             entry_stride_cmp0_eq;
reg             entry_stride_diff_eq;
reg             entry_stride_neg;
wire            cp0_lsu_icg_en;
wire            cp0_yy_clk_en;
wire            cpurst_b;
wire            entry_addr0_act;
wire            entry_addr_0_clk;
wire            entry_addr_0_clk_en;
wire    [39:0]  entry_addr_0_next;
wire            entry_addr_1_clk;
wire            entry_addr_1_clk_en;
wire    [39:0]  entry_addr_1_next;
wire            entry_addr_2_clk;
wire            entry_addr_2_clk_en;
wire    [39:0]  entry_addr_2_next;
wire    [2 :0]  entry_addr_dp_set;
wire    [2 :0]  entry_addr_set;
wire            entry_check_stride_success;
wire            entry_clk;
wire            entry_clr_addr_info_vld;
wire            entry_cmit_all;
wire            entry_cmit_all_clk;
wire            entry_cmit_all_clk_en;
wire    [2 :0]  entry_cmit_hit0;
wire    [2 :0]  entry_cmit_hit1;
wire    [2 :0]  entry_cmit_hit2;
wire    [2 :0]  entry_cmit_set;
wire            entry_create_dp_vld;
wire            entry_create_gateclk_en;
wire    [2 :0]  entry_flush_uncmit;
wire    [6 :0]  entry_iid_0_next;
wire    [6 :0]  entry_iid_1_next;
wire    [6 :0]  entry_iid_2_next;
wire    [2 :0]  entry_iid_newer_than_ld_da;
wire    [2 :0]  entry_newer_than_ld_da;
wire            entry_normal_stride;
wire            entry_pf_inst_vld;
wire            entry_sel_2;
wire    [39:0]  entry_stride_0to1;
wire            entry_stride_0to1_cross_2k;
wire            entry_stride_0to1_neg_cross_2k_set;
wire            entry_stride_0to1_pos_cross_2k_set;
wire            entry_stride_0to1_zero_set;
wire    [39:0]  entry_stride_1to0;
wire    [39:0]  entry_stride_1to2;
wire            entry_stride_cmp0_eq_set;
wire            entry_stride_create_vld;
wire            entry_stride_diff_eq_set;
wire            entry_stride_ge_cache_line;
wire            entry_stride_keep;
wire            entry_stride_neg_ge_cache_line;
wire            entry_stride_neg_set;
wire            entry_stride_pos_ge_cache_line;
wire    [6 :0]  entry_strideh_6to0;
wire            entry_vld;
wire            forever_cpuclk;
wire    [6 :0]  ld_da_iid;
wire            pad_yy_icg_scan_en;
wire    [39:0]  pipe_va;
wire            rtu_yy_xx_commit0;
wire    [6 :0]  rtu_yy_xx_commit0_iid;
wire            rtu_yy_xx_commit1;
wire    [6 :0]  rtu_yy_xx_commit1_iid;
wire            rtu_yy_xx_commit2;
wire    [6 :0]  rtu_yy_xx_commit2_iid;
wire            rtu_yy_xx_flush;
assign entry_cmit_all_clk_en  = entry_create_gateclk_en
                                ||  entry_vld
                                    &&  entry_cmit_all;
assign entry_cmit_all_clk = forever_cpuclk ;
assign entry_addr_0_clk = forever_cpuclk ;
assign entry_addr_0_clk_en = entry_addr_dp_set[0];
assign entry_addr_1_clk = forever_cpuclk ;
assign entry_addr_1_clk_en = entry_addr_dp_set[1];
assign entry_addr_2_clk = forever_cpuclk ;
assign entry_addr_2_clk_en = entry_addr_dp_set[2];
always @(posedge entry_addr_0_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
  begin
    entry_addr_0[PA_WIDTH-1:0]  <=  {PA_WIDTH{1'b0}};
    entry_iid_0[6:0]             <=  7'b0;
  end
  else if(entry_addr_dp_set[0])
  begin
    entry_addr_0[PA_WIDTH-1:0]  <=  entry_addr_0_next[PA_WIDTH-1:0];
    entry_iid_0[6:0]             <=  entry_iid_0_next[6:0];
  end
end
always @(posedge entry_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    entry_addr_vld[0]   <=  1'b0;
  else if(entry_create_dp_vld ||  entry_flush_uncmit[0] ||  entry_clr_addr_info_vld)
    entry_addr_vld[0]   <=  1'b0;
  else if(entry_addr_set[0])
    entry_addr_vld[0]   <=  1'b1;
end
always @(posedge entry_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    entry_cmit[0]       <=  1'b0;
  else if(entry_create_dp_vld ||  entry_flush_uncmit[0] ||  entry_clr_addr_info_vld)
    entry_cmit[0]       <=  1'b0;
  else if(entry_cmit_set[0])
    entry_cmit[0]       <=  1'b1;
end
always @(posedge entry_addr_1_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
  begin
    entry_addr_1[PA_WIDTH-1:0]  <=  {PA_WIDTH{1'b0}};
    entry_iid_1[6:0]    <=  7'b0;
  end
  else if(entry_addr_dp_set[1])
  begin
    entry_addr_1[PA_WIDTH-1:0]  <=  entry_addr_1_next[PA_WIDTH-1:0];
    entry_iid_1[6:0]             <=  entry_iid_1_next[6:0];
  end
end
always @(posedge entry_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    entry_addr_vld[1]   <=  1'b0;
  else if(entry_create_dp_vld ||  entry_flush_uncmit[1] ||  entry_clr_addr_info_vld)
    entry_addr_vld[1]   <=  1'b0;
  else if(entry_addr_set[1])
    entry_addr_vld[1]   <=  1'b1;
end
always @(posedge entry_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    entry_cmit[1]       <=  1'b0;
  else if(entry_create_dp_vld ||  entry_flush_uncmit[1] ||  entry_clr_addr_info_vld)
    entry_cmit[1]       <=  1'b0;
  else if(entry_cmit_set[1])
    entry_cmit[1]       <=  1'b1;
end
always @(posedge entry_addr_2_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
  begin
    entry_addr_2[PA_WIDTH-1:0]  <=  {PA_WIDTH{1'b0}};
    entry_iid_2[6:0]             <=  7'b0;
  end
  else if(entry_addr_dp_set[2])
  begin
    entry_addr_2[PA_WIDTH-1:0]  <=  entry_addr_2_next[PA_WIDTH-1:0];
    entry_iid_2[6:0]             <=  entry_iid_2_next[6:0];
  end
end
always @(posedge entry_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    entry_addr_vld[2]   <=  1'b0;
  else if(entry_create_dp_vld ||  entry_flush_uncmit[2] ||  entry_clr_addr_info_vld)
    entry_addr_vld[2]   <=  1'b0;
  else if(entry_addr_set[2])
    entry_addr_vld[2]   <=  1'b1;
end
always @(posedge entry_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    entry_cmit[2]       <=  1'b0;
  else if(entry_create_dp_vld ||  entry_flush_uncmit[2] ||  entry_clr_addr_info_vld)
    entry_cmit[2]       <=  1'b0;
  else if(entry_cmit_set[2])
    entry_cmit[2]       <=  1'b1;
end
always @(posedge entry_cmit_all_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
  begin
    entry_stride_neg   <=  1'b0;
    entry_stride[10:0] <=  11'b0;
  end
  else if(entry_stride_create_vld)
  begin
    entry_stride_neg   <=  entry_stride_neg_set;
    entry_stride[10:0] <=  entry_stride_0to1[10:0];
  end
end
always @(posedge entry_cmit_all_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
  begin
    entry_addr_cmp_info_vld        <=  1'b0;
    entry_stride_diff_eq           <=  1'b0;
    entry_stride_cmp0_eq           <=  1'b0;
    entry_stride_0to1_zero         <=  1'b0;
    entry_stride_0to1_pos_cross_2k <=  1'b0;
    entry_stride_0to1_neg_cross_2k <=  1'b0;
  end
  else if(entry_create_dp_vld  ||  entry_clr_addr_info_vld)
  begin
    entry_addr_cmp_info_vld        <=  1'b0;
    entry_stride_diff_eq           <=  1'b0;
    entry_stride_cmp0_eq           <=  1'b0;
    entry_stride_0to1_zero         <=  1'b0;
    entry_stride_0to1_pos_cross_2k <=  1'b0;
    entry_stride_0to1_neg_cross_2k <=  1'b0;
  end
  else if(entry_vld &&  entry_cmit_all)
  begin
    entry_addr_cmp_info_vld        <=  1'b1;
    entry_stride_diff_eq           <=  entry_stride_diff_eq_set;
    entry_stride_cmp0_eq           <=  entry_stride_cmp0_eq_set;
    entry_stride_0to1_zero         <=  entry_stride_0to1_zero_set;
    entry_stride_0to1_pos_cross_2k <=  entry_stride_0to1_pos_cross_2k_set;
    entry_stride_0to1_neg_cross_2k <=  entry_stride_0to1_neg_cross_2k_set;
  end
end
assign entry_cmit_hit0[0] = {rtu_yy_xx_commit0,rtu_yy_xx_commit0_iid[6:0]}
                            ==  {1'b1,entry_iid_0[6:0]};
assign entry_cmit_hit1[0] = {rtu_yy_xx_commit1,rtu_yy_xx_commit1_iid[6:0]}
                            ==  {1'b1,entry_iid_0[6:0]};
assign entry_cmit_hit2[0] = {rtu_yy_xx_commit2,rtu_yy_xx_commit2_iid[6:0]}
                            ==  {1'b1,entry_iid_0[6:0]};
assign entry_cmit_set[0]  = (entry_cmit_hit0[0]
                                ||  entry_cmit_hit1[0]
                                ||  entry_cmit_hit2[0])
                            &&  entry_addr_vld[0];
assign entry_cmit_hit0[1] = {rtu_yy_xx_commit0,rtu_yy_xx_commit0_iid[6:0]}
                            ==  {1'b1,entry_iid_1[6:0]};
assign entry_cmit_hit1[1] = {rtu_yy_xx_commit1,rtu_yy_xx_commit1_iid[6:0]}
                            ==  {1'b1,entry_iid_1[6:0]};
assign entry_cmit_hit2[1] = {rtu_yy_xx_commit2,rtu_yy_xx_commit2_iid[6:0]}
                            ==  {1'b1,entry_iid_1[6:0]};
assign entry_cmit_set[1]  = (entry_cmit_hit0[1]
                                ||  entry_cmit_hit1[1]
                                ||  entry_cmit_hit2[1])
                            &&  entry_addr_vld[1];
assign entry_cmit_hit0[2] = {rtu_yy_xx_commit0,rtu_yy_xx_commit0_iid[6:0]}
                            ==  {1'b1,entry_iid_2[6:0]};
assign entry_cmit_hit1[2] = {rtu_yy_xx_commit1,rtu_yy_xx_commit1_iid[6:0]}
                            ==  {1'b1,entry_iid_2[6:0]};
assign entry_cmit_hit2[2] = {rtu_yy_xx_commit2,rtu_yy_xx_commit2_iid[6:0]}
                            ==  {1'b1,entry_iid_2[6:0]};
assign entry_cmit_set[2]  = (entry_cmit_hit0[2]
                                ||  entry_cmit_hit1[2]
                                ||  entry_cmit_hit2[2])
                            &&  entry_addr_vld[2];
assign entry_flush_uncmit[2:0]  = {3{rtu_yy_xx_flush}}
                                  & (~entry_cmit[2:0]);
assign entry_addr_dp_set[0] = entry_pf_inst_vld
                              &&  !entry_addr_vld[0];
assign entry_addr_dp_set[1] = entry_pf_inst_vld
                              &&  !entry_newer_than_ld_da[0]
                              &&  (entry_addr_vld[0]
                                      &&  !entry_addr_vld[1]
                                  ||  entry_newer_than_ld_da[1]);
assign entry_addr_dp_set[2] = entry_pf_inst_vld
                              &&  !entry_newer_than_ld_da[0]
                              &&  (entry_addr_vld[0]
                                      &&  entry_addr_vld[1]
                                      &&  !entry_addr_vld[2]
                                  ||  entry_newer_than_ld_da[2]);
assign entry_addr_set[0]    = entry_addr_dp_set[0]
                              &&  entry_addr0_act;
assign entry_addr_set[1]    = entry_addr_dp_set[1];
assign entry_addr_set[2]    = entry_addr_dp_set[2];
assign entry_addr_0_next[PA_WIDTH-1:0] = pipe_va[PA_WIDTH-1:0];
assign entry_iid_0_next[6:0]            = ld_da_iid[6:0];
assign entry_addr_1_next[PA_WIDTH-1:0] = pipe_va[PA_WIDTH-1:0];
assign entry_iid_1_next[6:0]            = ld_da_iid[6:0];
assign entry_sel_2 = entry_newer_than_ld_da[1];
assign entry_addr_2_next[PA_WIDTH-1:0] = entry_sel_2
                                          ? entry_addr_1[PA_WIDTH-1:0]
                                          : pipe_va[PA_WIDTH-1:0];
assign entry_iid_2_next[6:0]            = entry_sel_2
                                          ? entry_iid_1[6:0]
                                          : ld_da_iid[6:0];
assign entry_newer_than_ld_da[0]  = entry_iid_newer_than_ld_da[0]
                                    &&  !entry_cmit[0]
                                    &&  entry_addr_vld[0];
assign entry_newer_than_ld_da[1]  = entry_iid_newer_than_ld_da[1]
                                    &&  !entry_cmit[1]
                                    &&  entry_addr_vld[1];
assign entry_newer_than_ld_da[2]  = entry_iid_newer_than_ld_da[2]
                                    &&  !entry_cmit[2]
                                    &&  entry_addr_vld[2];
assign entry_stride_1to0[PA_WIDTH-1:0]  = entry_addr_0[PA_WIDTH-1:0]
                                              - entry_addr_1[PA_WIDTH-1:0];
assign entry_stride_0to1[PA_WIDTH-1:0]  = entry_addr_1[PA_WIDTH-1:0]
                                              - entry_addr_0[PA_WIDTH-1:0];
assign entry_stride_1to2[PA_WIDTH-1:0]  = entry_addr_2[PA_WIDTH-1:0]
                                              - entry_addr_1[PA_WIDTH-1:0];
assign entry_stride_neg_set     = entry_stride_0to1[PA_WIDTH-1];
assign entry_stride_diff_eq_set = entry_stride_0to1[PA_WIDTH-1:0]
                                  ==  entry_stride_1to2[PA_WIDTH-1:0];
assign entry_stride_cmp0_eq_set = entry_stride_0to1[11:0]
                                  ==  {entry_stride_neg,entry_stride[10:0]};
assign entry_stride_0to1_pos_cross_2k_set  = |entry_stride_0to1[PA_WIDTH-1:12];
assign entry_stride_0to1_neg_cross_2k_set  = |entry_stride_1to0[PA_WIDTH-1:12];
assign entry_stride_0to1_zero_set   = ~(|entry_stride_0to1[PA_WIDTH-1:0]);
assign entry_stride_0to1_cross_2k   = entry_stride_neg
                                          &&  entry_stride_0to1_neg_cross_2k
                                      ||  !entry_stride_neg
                                          &&  entry_stride_0to1_pos_cross_2k;
assign entry_normal_stride = ~(!entry_stride_0to1_zero
                                      &&  !entry_stride_0to1_cross_2k
                                      &&  entry_stride_diff_eq);
assign entry_check_stride_success   = entry_normal_stride
                                      &&  entry_stride_cmp0_eq;
assign entry_cmit_all           = &entry_cmit[2:0];
assign entry_stride_create_vld  = entry_cmit_all
                                  &&  !entry_stride_keep
                                  &&  !entry_addr_cmp_info_vld;
assign entry_clr_addr_info_vld  = entry_cmit_all
                                  &&  entry_addr_cmp_info_vld;
assign entry_stride_neg_ge_cache_line = !(&entry_stride[10:6]);
assign entry_stride_pos_ge_cache_line = |entry_stride[10:6];
assign entry_stride_ge_cache_line     = entry_stride_neg
                                        ? entry_stride_neg_ge_cache_line
                                        : entry_stride_pos_ge_cache_line;
assign entry_strideh_6to0[6:0]        = entry_stride_ge_cache_line
                                        ? entry_stride[6:0]
                                        : 7'h40;
always @* assert(1);
endmodule