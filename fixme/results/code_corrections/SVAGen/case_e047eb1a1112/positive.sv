`timescale 1ns/1ps
module ct_idu_dep_reg_src2_entry(
  alu0_reg_fwd_vld,
  alu1_reg_fwd_vld,
  cp0_idu_icg_en,
  cp0_yy_clk_en,
  cpurst_b,
  ctrl_xx_rf_pipe0_preg_lch_vld_dupx,
  ctrl_xx_rf_pipe1_preg_lch_vld_dupx,
  dp_xx_rf_pipe0_dst_preg_dupx,
  dp_xx_rf_pipe1_dst_preg_dupx,
  forever_cpuclk,
  gateclk_entry_vld,
  iu_idu_div_inst_vld,
  iu_idu_div_preg_dupx,
  iu_idu_ex2_pipe0_wb_preg_dupx,
  iu_idu_ex2_pipe0_wb_preg_vld_dupx,
  iu_idu_ex2_pipe1_mult_inst_vld_dupx,
  iu_idu_ex2_pipe1_preg_dupx,
  iu_idu_ex2_pipe1_wb_preg_dupx,
  iu_idu_ex2_pipe1_wb_preg_vld_dupx,
  lsu_idu_ag_pipe3_load_inst_vld,
  lsu_idu_ag_pipe3_preg_dupx,
  lsu_idu_dc_pipe3_load_fwd_inst_vld_dupx,
  lsu_idu_dc_pipe3_load_inst_vld_dupx,
  lsu_idu_dc_pipe3_preg_dupx,
  lsu_idu_wb_pipe3_wb_preg_dupx,
  lsu_idu_wb_pipe3_wb_preg_vld_dupx,
  mla_reg_fwd_vld,
  pad_yy_icg_scan_en,
  rtu_idu_flush_fe,
  rtu_idu_flush_is,
  vfpu_idu_ex1_pipe6_mfvr_inst_vld_dupx,
  vfpu_idu_ex1_pipe6_preg_dupx,
  vfpu_idu_ex1_pipe7_mfvr_inst_vld_dupx,
  vfpu_idu_ex1_pipe7_preg_dupx,
  x_create_data,
  x_entry_mla,
  x_gateclk_idx_write_en,
  x_gateclk_write_en,
  x_rdy_clr,
  x_read_data,
  x_write_en
);
input           alu0_reg_fwd_vld;
input           alu1_reg_fwd_vld;
input           cp0_idu_icg_en;
input           cp0_yy_clk_en;
input           cpurst_b;
input           ctrl_xx_rf_pipe0_preg_lch_vld_dupx;
input           ctrl_xx_rf_pipe1_preg_lch_vld_dupx;
input   [6 :0]  dp_xx_rf_pipe0_dst_preg_dupx;
input   [6 :0]  dp_xx_rf_pipe1_dst_preg_dupx;
input           forever_cpuclk;
input           gateclk_entry_vld;
input           iu_idu_div_inst_vld;
input   [6 :0]  iu_idu_div_preg_dupx;
input   [6 :0]  iu_idu_ex2_pipe0_wb_preg_dupx;
input           iu_idu_ex2_pipe0_wb_preg_vld_dupx;
input           iu_idu_ex2_pipe1_mult_inst_vld_dupx;
input   [6 :0]  iu_idu_ex2_pipe1_preg_dupx;
input   [6 :0]  iu_idu_ex2_pipe1_wb_preg_dupx;
input           iu_idu_ex2_pipe1_wb_preg_vld_dupx;
input           lsu_idu_ag_pipe3_load_inst_vld;
input   [6 :0]  lsu_idu_ag_pipe3_preg_dupx;
input           lsu_idu_dc_pipe3_load_fwd_inst_vld_dupx;
input           lsu_idu_dc_pipe3_load_inst_vld_dupx;
input   [6 :0]  lsu_idu_dc_pipe3_preg_dupx;
input   [6 :0]  lsu_idu_wb_pipe3_wb_preg_dupx;
input           lsu_idu_wb_pipe3_wb_preg_vld_dupx;
input           mla_reg_fwd_vld;
input           pad_yy_icg_scan_en;
input           rtu_idu_flush_fe;
input           rtu_idu_flush_is;
input           vfpu_idu_ex1_pipe6_mfvr_inst_vld_dupx;
input   [6 :0]  vfpu_idu_ex1_pipe6_preg_dupx;
input           vfpu_idu_ex1_pipe7_mfvr_inst_vld_dupx;
input   [6 :0]  vfpu_idu_ex1_pipe7_preg_dupx;
input   [10:0]  x_create_data;
input           x_entry_mla;
input           x_gateclk_idx_write_en;
input           x_gateclk_write_en;
input           x_rdy_clr;
input           x_write_en;
output  [12:0]  x_read_data;
reg             lsu_match;
reg             mla_rdy;
reg     [6 :0]  preg;
reg             rdy;
reg             wb;
wire            alu0_data_ready;
wire            alu0_issue_data_ready;
wire            alu0_reg_fwd_vld;
wire            alu1_data_ready;
wire            alu1_issue_data_ready;
wire            alu1_reg_fwd_vld;
wire            cp0_idu_icg_en;
wire            cp0_yy_clk_en;
wire            cpurst_b;
wire            ctrl_xx_rf_pipe0_preg_lch_vld_dupx;
wire            ctrl_xx_rf_pipe1_preg_lch_vld_dupx;
wire            data_ready;
wire            dep_clk;
wire            dep_clk_en;
wire            div_data_ready;
wire    [6 :0]  dp_xx_rf_pipe0_dst_preg_dupx;
wire    [6 :0]  dp_xx_rf_pipe1_dst_preg_dupx;
wire            forever_cpuclk;
wire            gateclk_entry_vld;
wire            iu_idu_div_inst_vld;
wire    [6 :0]  iu_idu_div_preg_dupx;
wire    [6 :0]  iu_idu_ex2_pipe0_wb_preg_dupx;
wire            iu_idu_ex2_pipe0_wb_preg_vld_dupx;
wire            iu_idu_ex2_pipe1_mult_inst_vld_dupx;
wire    [6 :0]  iu_idu_ex2_pipe1_preg_dupx;
wire    [6 :0]  iu_idu_ex2_pipe1_wb_preg_dupx;
wire            iu_idu_ex2_pipe1_wb_preg_vld_dupx;
wire            load_data_ready;
wire            load_issue_data_ready;
wire            lsu_idu_ag_pipe3_load_inst_vld;
wire    [6 :0]  lsu_idu_ag_pipe3_preg_dupx;
wire            lsu_idu_dc_pipe3_load_fwd_inst_vld_dupx;
wire            lsu_idu_dc_pipe3_load_inst_vld_dupx;
wire    [6 :0]  lsu_idu_dc_pipe3_preg_dupx;
wire    [6 :0]  lsu_idu_wb_pipe3_wb_preg_dupx;
wire            lsu_idu_wb_pipe3_wb_preg_vld_dupx;
wire            lsu_match_update;
wire            mla_data_ready;
wire            mla_issue_data_ready;
wire            mla_rdy_update;
wire            mla_reg_fwd_vld;
wire            mult_data_ready;
wire            pad_yy_icg_scan_en;
wire            pipe0_wb;
wire            pipe1_wb;
wire            pipe3_wb;
wire            rdy_clear;
wire            rdy_update;
wire            rtu_idu_flush_fe;
wire            rtu_idu_flush_is;
wire            vfpu0_data_ready;
wire            vfpu1_data_ready;
wire            vfpu_idu_ex1_pipe6_mfvr_inst_vld_dupx;
wire    [6 :0]  vfpu_idu_ex1_pipe6_preg_dupx;
wire            vfpu_idu_ex1_pipe7_mfvr_inst_vld_dupx;
wire    [6 :0]  vfpu_idu_ex1_pipe7_preg_dupx;
wire            wake_up;
wire            wb_update;
wire            write_back;
wire            write_clk;
wire            write_clk_en;
wire    [10:0]  x_create_data;
wire            x_create_lsu_match;
wire            x_create_mla_rdy;
wire    [6 :0]  x_create_preg;
wire            x_create_rdy;
wire            x_create_wb;
wire            x_entry_mla;
wire            x_gateclk_idx_write_en;
wire            x_gateclk_write_en;
wire            x_rdy_clr;
wire    [12:0]  x_read_data;
wire            x_read_lsu_match;
wire            x_read_mla_rdy;
wire    [6 :0]  x_read_preg;
wire            x_read_rdy;
wire            x_read_rdy_for_bypass;
wire            x_read_rdy_for_issue;
wire            x_read_wb;
wire            x_write_en;
assign dep_clk = forever_cpuclk;
assign dep_clk_en = x_gateclk_write_en || gateclk_entry_vld && (!rdy || !wb);
assign write_clk = forever_cpuclk;
assign write_clk_en = x_gateclk_idx_write_en;
assign x_create_lsu_match           = x_create_data[10];
assign x_create_mla_rdy             = x_create_data[9];
assign x_create_preg[6:0]           = x_create_data[8:2];
assign x_create_wb                  = x_create_data[1];
assign x_create_rdy                 = x_create_data[0];
assign x_read_data[12]              = x_read_lsu_match;
assign x_read_data[11]              = x_read_rdy_for_bypass;
assign x_read_data[10]              = x_read_rdy_for_issue;
assign x_read_data[9]               = x_read_mla_rdy;
assign x_read_data[8:2]             = x_read_preg[6:0];
assign x_read_data[1]               = x_read_wb;
assign x_read_data[0]               = x_read_rdy;
assign alu0_data_ready   = ctrl_xx_rf_pipe0_preg_lch_vld_dupx
                           && (dp_xx_rf_pipe0_dst_preg_dupx[6:0] == preg[6:0]);
assign alu1_data_ready   = ctrl_xx_rf_pipe1_preg_lch_vld_dupx
                           && (dp_xx_rf_pipe1_dst_preg_dupx[6:0] == preg[6:0]);
assign mult_data_ready   = iu_idu_ex2_pipe1_mult_inst_vld_dupx
                           && (iu_idu_ex2_pipe1_preg_dupx[6:0] == preg[6:0]);
assign div_data_ready    = iu_idu_div_inst_vld
                           && (iu_idu_div_preg_dupx[6:0] == preg[6:0]);
assign load_data_ready   = lsu_idu_dc_pipe3_load_inst_vld_dupx
                           && (lsu_idu_dc_pipe3_preg_dupx[6:0] == preg[6:0]);
assign vfpu0_data_ready  = vfpu_idu_ex1_pipe6_mfvr_inst_vld_dupx
                           && (vfpu_idu_ex1_pipe6_preg_dupx[6:0] == preg[6:0]);
assign vfpu1_data_ready  = vfpu_idu_ex1_pipe7_mfvr_inst_vld_dupx
                           && (vfpu_idu_ex1_pipe7_preg_dupx[6:0] == preg[6:0]);
assign alu0_issue_data_ready = alu0_reg_fwd_vld;
assign alu1_issue_data_ready = alu1_reg_fwd_vld;
assign load_issue_data_ready = lsu_idu_dc_pipe3_load_fwd_inst_vld_dupx && lsu_match;
assign data_ready        = alu0_data_ready
                           || alu1_data_ready
                           || mult_data_ready
                           || div_data_ready
                           || load_data_ready
                           || vfpu0_data_ready
                           || vfpu1_data_ready;
assign wake_up           = wb;
assign rdy_clear         = x_rdy_clr;
assign rdy_update = (rdy || data_ready || wake_up) && !rdy_clear;
assign x_read_rdy = rdy_update;
assign x_read_rdy_for_issue  = rdy || mla_rdy
                                   || alu0_issue_data_ready
                                   || alu1_issue_data_ready
                                   || load_issue_data_ready
                                   || mla_issue_data_ready;
assign x_read_rdy_for_bypass = rdy;
always @(posedge dep_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    rdy <= 1'b1;
  else if(rtu_idu_flush_fe || rtu_idu_flush_is)
    rdy <= 1'b1;
  else if(x_write_en)
    rdy <= x_create_rdy;
  else
    rdy <= rdy_update;
end
assign mla_issue_data_ready = x_entry_mla
                              && mla_reg_fwd_vld;
assign mla_data_ready       = mla_issue_data_ready;
assign mla_rdy_update = (mla_rdy || mla_data_ready || wake_up) && !rdy_clear;
assign x_read_mla_rdy = mla_rdy_update;
always @(posedge dep_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    mla_rdy <= 1'b1;
  else if(rtu_idu_flush_fe || rtu_idu_flush_is)
    mla_rdy <= 1'b1;
  else if(x_write_en)
    mla_rdy <= x_create_mla_rdy;
  else
    mla_rdy <= mla_rdy_update;
end
assign pipe0_wb = iu_idu_ex2_pipe0_wb_preg_vld_dupx
                  && (iu_idu_ex2_pipe0_wb_preg_dupx[6:0] == preg[6:0]);
assign pipe1_wb = iu_idu_ex2_pipe1_wb_preg_vld_dupx
                  && (iu_idu_ex2_pipe1_wb_preg_dupx[6:0] == preg[6:0]);
assign pipe3_wb = lsu_idu_wb_pipe3_wb_preg_vld_dupx
                  && (lsu_idu_wb_pipe3_wb_preg_dupx[6:0] == preg[6:0]);
assign write_back = wb
                    || pipe0_wb
                    || pipe1_wb
                    || pipe3_wb;
assign x_read_wb = wb_update;
assign wb_update = wb || write_back;
always @(posedge dep_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    wb <= 1'b1;
  else if(rtu_idu_flush_fe || rtu_idu_flush_is)
    wb <= 1'b1;
  else if(x_write_en)
    wb <= x_create_wb;
  else
    wb <= wb_update;
end
assign lsu_match_update = lsu_idu_ag_pipe3_load_inst_vld
                          && (lsu_idu_ag_pipe3_preg_dupx[6:0] == preg[6:0]);
assign x_read_lsu_match  = lsu_match_update;
always @(posedge dep_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    lsu_match <= 1'b0;
  else if(rtu_idu_flush_fe || rtu_idu_flush_is)
    lsu_match <= 1'b0;
  else if(x_write_en)
    lsu_match <= x_create_lsu_match;
  else
    lsu_match <= lsu_match_update;
end
assign x_read_preg[6:0] = preg[6:0];
always @(posedge write_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    preg[6:0] <= 7'b0;
  else if(x_write_en)
    preg[6:0] <= x_create_preg[6:0];
  else
    preg[6:0] <= preg[6:0];
end
always @* assert((x_read_data[12]) == 1'(x_read_lsu_match));
endmodule