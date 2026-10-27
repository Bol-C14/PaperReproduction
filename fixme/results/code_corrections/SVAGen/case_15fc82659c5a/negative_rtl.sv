`timescale 1ns/1ps
module ct_ifu_btb(
  addrgen_btb_index,
  addrgen_btb_tag,
  addrgen_btb_target_pc,
  addrgen_btb_update_vld,
  btb_ifctrl_inv_done,
  btb_ifctrl_inv_on,
  btb_ifdp_way0_pred,
  btb_ifdp_way0_tag,
  btb_ifdp_way0_target,
  btb_ifdp_way0_vld,
  btb_ifdp_way1_pred,
  btb_ifdp_way1_tag,
  btb_ifdp_way1_target,
  btb_ifdp_way1_vld,
  btb_ifdp_way2_pred,
  btb_ifdp_way2_tag,
  btb_ifdp_way2_target,
  btb_ifdp_way2_vld,
  btb_ifdp_way3_pred,
  btb_ifdp_way3_tag,
  btb_ifdp_way3_target,
  btb_ifdp_way3_vld,
  cp0_ifu_btb_en,
  cp0_ifu_icg_en,
  cp0_yy_clk_en,
  cpurst_b,
  forever_cpuclk,
  ibdp_btb_miss,
  ifctrl_btb_inv,
  ipctrl_btb_chgflw_vld,
  ipctrl_btb_way_pred,
  ipctrl_btb_way_pred_error,
  ipdp_btb_index_pc,
  ipdp_btb_target_pc,
  pad_yy_icg_scan_en,
  pcgen_btb_chgflw,
  pcgen_btb_chgflw_higher_than_addrgen,
  pcgen_btb_chgflw_higher_than_if,
  pcgen_btb_chgflw_higher_than_ip,
  pcgen_btb_chgflw_short,
  pcgen_btb_index,
  pcgen_btb_stall,
  pcgen_btb_stall_short
);
input   [9 :0]  addrgen_btb_index;
input   [9 :0]  addrgen_btb_tag;
input   [19:0]  addrgen_btb_target_pc;
input           addrgen_btb_update_vld;
input           cp0_ifu_btb_en;
input           cp0_ifu_icg_en;
input           cp0_yy_clk_en;
input           cpurst_b;
input           forever_cpuclk;
input           ibdp_btb_miss;
input           ifctrl_btb_inv;
input           ipctrl_btb_chgflw_vld;
input   [1 :0]  ipctrl_btb_way_pred;
input           ipctrl_btb_way_pred_error;
input   [38:0]  ipdp_btb_index_pc;
input   [19:0]  ipdp_btb_target_pc;
input           pad_yy_icg_scan_en;
input           pcgen_btb_chgflw;
input           pcgen_btb_chgflw_higher_than_addrgen;
input           pcgen_btb_chgflw_higher_than_if;
input           pcgen_btb_chgflw_higher_than_ip;
input           pcgen_btb_chgflw_short;
input   [9 :0]  pcgen_btb_index;
input           pcgen_btb_stall;
input           pcgen_btb_stall_short;
output          btb_ifctrl_inv_done;
output          btb_ifctrl_inv_on;
output  [1 :0]  btb_ifdp_way0_pred;
output  [9 :0]  btb_ifdp_way0_tag;
output  [19:0]  btb_ifdp_way0_target;
output          btb_ifdp_way0_vld;
output  [1 :0]  btb_ifdp_way1_pred;
output  [9 :0]  btb_ifdp_way1_tag;
output  [19:0]  btb_ifdp_way1_target;
output          btb_ifdp_way1_vld;
output  [1 :0]  btb_ifdp_way2_pred;
output  [9 :0]  btb_ifdp_way2_tag;
output  [19:0]  btb_ifdp_way2_target;
output          btb_ifdp_way2_vld;
output  [1 :0]  btb_ifdp_way3_pred;
output  [9 :0]  btb_ifdp_way3_tag;
output  [19:0]  btb_ifdp_way3_target;
output          btb_ifdp_way3_vld;
reg             after_addrgen_btb_chgflw_first;
reg             after_addrgen_btb_chgflw_second;
reg     [87:0]  btb_data_dout_reg;
reg     [3 :0]  btb_data_wen;
reg     [9 :0]  btb_index;
reg     [9 :0]  btb_index_flop;
reg     [38:0]  btb_index_pc_record;
reg             btb_inv_on_reg;
reg     [9 :0]  btb_inval_cnt;
reg             btb_rd_flop;
reg     [43:0]  btb_tag_dout_reg;
reg     [3 :0]  btb_tag_wen;
reg     [19:0]  btb_target_pc_record;
reg     [9 :0]  refill_buf_index;
reg     [9 :0]  refill_buf_tag;
reg     [19:0]  refill_buf_target_pc;
reg             refill_buf_valid;
reg     [1 :0]  refill_buf_way_pred;
wire    [9 :0]  addrgen_btb_index;
wire    [9 :0]  addrgen_btb_tag;
wire    [19:0]  addrgen_btb_target_pc;
wire            addrgen_btb_update_vld;
wire    [9 :0]  btb_buf_tag_data;
wire    [19:0]  btb_buf_target_pc;
wire            btb_buf_valid;
wire    [1 :0]  btb_buf_way_pred;
wire            btb_data_cen_b;
wire            btb_data_clk_en;
wire    [43:0]  btb_data_din;
wire    [87:0]  btb_data_dout;
wire            btb_data_rd;
wire            btb_dout_flop_clk;
wire            btb_dout_flop_clk_en;
wire            btb_ifctrl_inv_done;
wire            btb_ifctrl_inv_on;
wire    [1 :0]  btb_ifdp_way0_pred;
wire    [9 :0]  btb_ifdp_way0_tag;
wire    [19:0]  btb_ifdp_way0_target;
wire            btb_ifdp_way0_vld;
wire    [1 :0]  btb_ifdp_way1_pred;
wire    [9 :0]  btb_ifdp_way1_tag;
wire    [19:0]  btb_ifdp_way1_target;
wire            btb_ifdp_way1_vld;
wire    [1 :0]  btb_ifdp_way2_pred;
wire    [9 :0]  btb_ifdp_way2_tag;
wire    [19:0]  btb_ifdp_way2_target;
wire            btb_ifdp_way2_vld;
wire    [1 :0]  btb_ifdp_way3_pred;
wire    [9 :0]  btb_ifdp_way3_tag;
wire    [19:0]  btb_ifdp_way3_target;
wire            btb_ifdp_way3_vld;
wire            btb_inv_reg_upd_clk;
wire            btb_inv_reg_upd_clk_en;
wire    [9 :0]  btb_mem_way0_tag_data;
wire    [19:0]  btb_mem_way0_target_pc;
wire            btb_mem_way0_valid;
wire    [1 :0]  btb_mem_way0_way_pred;
wire    [9 :0]  btb_mem_way1_tag_data;
wire    [19:0]  btb_mem_way1_target_pc;
wire            btb_mem_way1_valid;
wire    [1 :0]  btb_mem_way1_way_pred;
wire    [9 :0]  btb_mem_way2_tag_data;
wire    [19:0]  btb_mem_way2_target_pc;
wire            btb_mem_way2_valid;
wire    [1 :0]  btb_mem_way2_way_pred;
wire    [9 :0]  btb_mem_way3_tag_data;
wire    [19:0]  btb_mem_way3_target_pc;
wire            btb_mem_way3_valid;
wire    [1 :0]  btb_mem_way3_way_pred;
wire            btb_miss_way_pred_rd;
wire            btb_tag_cen_b;
wire            btb_tag_clk_en;
wire    [21:0]  btb_tag_din;
wire    [43:0]  btb_tag_dout;
wire            btb_tag_rd;
wire            btb_tag_rd_gateclk_en;
wire            chgflw_higher_than_addrgen;
wire            chgflw_higher_than_if;
wire            chgflw_higher_than_ip;
wire            cp0_ifu_btb_en;
wire            cp0_ifu_icg_en;
wire            cp0_yy_clk_en;
wire            cpurst_b;
wire            forever_cpuclk;
wire            ibdp_btb_miss;
wire            ifctrl_btb_inv;
wire            index_pc_record_clk;
wire            index_pc_record_clk_en;
wire            ip_way_mispred;
wire            ipctrl_btb_chgflw_vld;
wire    [1 :0]  ipctrl_btb_way_pred;
wire            ipctrl_btb_way_pred_error;
wire    [38:0]  ipdp_btb_index_pc;
wire    [19:0]  ipdp_btb_target_pc;
wire            pad_yy_icg_scan_en;
wire            pcgen_btb_chgflw;
wire            pcgen_btb_chgflw_higher_than_addrgen;
wire            pcgen_btb_chgflw_higher_than_if;
wire            pcgen_btb_chgflw_higher_than_ip;
wire            pcgen_btb_chgflw_short;
wire    [9 :0]  pcgen_btb_index;
wire            pcgen_btb_stall;
wire            pcgen_btb_stall_short;
wire            pcgen_stall;
wire            refill_buf_updt_clk;
wire            refill_buf_updt_clk_en;
wire            refill_buf_updt_vld;
wire    [3 :0]  refill_buf_wen;
wire            tag_vld_din;
parameter PC_WIDTH = 40;
assign btb_tag_cen_b = !btb_inv_on_reg &&
                       !(cp0_ifu_btb_en && refill_buf_updt_vld) &&
                       !btb_tag_rd;
assign btb_tag_rd    = cp0_ifu_btb_en &&
                       (
                         (pcgen_btb_chgflw &&
                          !ipctrl_btb_way_pred_error &&
                          !ibdp_btb_miss) ||
                         (!pcgen_btb_chgflw &&
                          !pcgen_btb_stall)
                        );
assign btb_tag_rd_gateclk_en = cp0_ifu_btb_en &&
                              (pcgen_btb_chgflw_short ||
                              !pcgen_btb_stall_short);
assign btb_tag_clk_en = btb_inv_on_reg ||
                        cp0_ifu_btb_en &&
                        (
                          pcgen_btb_chgflw_short ||
                          !pcgen_btb_stall_short ||
                          ibdp_btb_miss
                        );
always @( btb_inv_on_reg
       or refill_buf_wen[3:0]
       or cp0_ifu_btb_en
       or refill_buf_updt_vld)
begin
if(btb_inv_on_reg)
  btb_tag_wen[3:0] = 4'b00;
else if(cp0_ifu_btb_en && refill_buf_updt_vld)
  btb_tag_wen[3:0] = refill_buf_wen[3:0];
else
  btb_tag_wen[3:0] = 4'b1111;
end
assign refill_buf_wen[3:0] = {~(refill_buf_tag[2:1]== 2'b11),
                              ~(refill_buf_tag[2:1]== 2'b10),
                              ~(refill_buf_tag[2:1]== 2'b01),
                              ~(refill_buf_tag[2:1]== 2'b00)};
assign tag_vld_din = refill_buf_updt_vld ? 1'b1 : 1'b0;
assign btb_tag_din[21:0] = {tag_vld_din, refill_buf_tag[9:0],
                            tag_vld_din, refill_buf_tag[9:0]};
assign btb_data_cen_b = !(cp0_ifu_btb_en && refill_buf_updt_vld) &&
                        !btb_data_rd;
assign btb_data_rd    = cp0_ifu_btb_en &&
                        (
                          (pcgen_btb_chgflw &&
                           !ipctrl_btb_way_pred_error &&
                           !ibdp_btb_miss) ||
                          (!pcgen_btb_chgflw &&
                           !pcgen_btb_stall)
                         );
assign btb_data_clk_en = cp0_ifu_btb_en &&
                         (
                          ibdp_btb_miss ||
                          pcgen_btb_chgflw_short ||
                          !pcgen_btb_stall_short
                         );
always @( refill_buf_wen[3:0]
       or cp0_ifu_btb_en
       or refill_buf_updt_vld)
begin
if(cp0_ifu_btb_en && refill_buf_updt_vld)
  btb_data_wen[3:0] = refill_buf_wen[3:0];
else
  btb_data_wen[3:0] = 4'b1111;
end
assign btb_data_din[43:0] = {refill_buf_way_pred[1:0], refill_buf_target_pc[19:0],
                             refill_buf_way_pred[1:0], refill_buf_target_pc[19:0]};
always @( btb_inval_cnt[9:0]
       or btb_inv_on_reg
       or refill_buf_index[9:0]
       or pcgen_btb_index[9:0]
       or refill_buf_updt_vld)
begin
if(btb_inv_on_reg)
  btb_index[9:0] = btb_inval_cnt[9:0];
else if(refill_buf_updt_vld)
  btb_index[9:0] = refill_buf_index[9:0];
else
  btb_index[9:0] = pcgen_btb_index[9:0];
end
assign index_pc_record_clk = forever_cpuclk;
assign index_pc_record_clk_en = btb_inv_on_reg || ipctrl_btb_chgflw_vld;
always @(posedge index_pc_record_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_index_pc_record[PC_WIDTH-2:0] <= {PC_WIDTH-1{1'b0}};
  else if(btb_inv_on_reg)
    btb_index_pc_record[PC_WIDTH-2:0] <= {PC_WIDTH-1{1'b0}};
  else if(ipctrl_btb_chgflw_vld)
    btb_index_pc_record[PC_WIDTH-2:0] <= ipdp_btb_index_pc[PC_WIDTH-2:0];
  else
    btb_index_pc_record[PC_WIDTH-2:0] <= btb_index_pc_record[PC_WIDTH-2:0];
end
always @(posedge index_pc_record_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_target_pc_record[19:0] <= 20'b0;
  else if(btb_inv_on_reg)
    btb_target_pc_record[19:0] <= 20'b0;
  else if(ipctrl_btb_chgflw_vld)
    btb_target_pc_record[19:0] <= ipdp_btb_target_pc[19:0];
  else
    btb_target_pc_record[19:0] <= btb_target_pc_record[19:0];
end
always @(posedge btb_dout_flop_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_rd_flop <= 1'b0;
  else if(btb_inv_on_reg)
    btb_rd_flop <= 1'b0;
  else if(btb_tag_rd)
    btb_rd_flop <= 1'b1;
  else
    btb_rd_flop <= 1'b0;
end
assign btb_dout_flop_clk = forever_cpuclk;
assign btb_dout_flop_clk_en = btb_inv_on_reg ||
                              btb_rd_flop    ||
                              btb_tag_rd_gateclk_en;
always @(posedge btb_dout_flop_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_tag_dout_reg[43:0] <= 44'b0;
  else if(btb_inv_on_reg)
    btb_tag_dout_reg[43:0] <= 44'b0;
  else if(btb_rd_flop && !ip_way_mispred)
    btb_tag_dout_reg[43:0] <= btb_tag_dout[43:0];
  else
    btb_tag_dout_reg[43:0] <= btb_tag_dout_reg[43:0];
end
assign ip_way_mispred = ipctrl_btb_way_pred_error;
always @(posedge btb_dout_flop_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_data_dout_reg[87:0] <= 88'b0;
  else if(btb_inv_on_reg)
    btb_data_dout_reg[87:0] <= 88'b0;
  else if(btb_rd_flop && !ip_way_mispred)
    btb_data_dout_reg[87:0] <= btb_data_dout[87:0];
  else
    btb_data_dout_reg[87:0] <= btb_data_dout_reg[87:0];
end
assign btb_mem_way3_valid           = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[43]
                                    : btb_tag_dout_reg[43];
assign btb_mem_way2_valid           = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[32]
                                    : btb_tag_dout_reg[32];
assign btb_mem_way1_valid           = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[21]
                                    : btb_tag_dout_reg[21];
assign btb_mem_way0_valid           = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[10]
                                    : btb_tag_dout_reg[10];
assign btb_mem_way3_tag_data[9:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[42:33]
                                    : btb_tag_dout_reg[42:33];
assign btb_mem_way2_tag_data[9:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[31:22]
                                    : btb_tag_dout_reg[31:22];
assign btb_mem_way1_tag_data[9:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[20:11]
                                    : btb_tag_dout_reg[20:11];
assign btb_mem_way0_tag_data[9:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_tag_dout[9:0]
                                    : btb_tag_dout_reg[9:0];
assign btb_mem_way3_way_pred[1:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[87:86]
                                    : btb_data_dout_reg[87:86];
assign btb_mem_way2_way_pred[1:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[65:64]
                                    : btb_data_dout_reg[65:64];
assign btb_mem_way1_way_pred[1:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[43:42]
                                    : btb_data_dout_reg[43:42];
assign btb_mem_way0_way_pred[1:0]   = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[21:20]
                                    : btb_data_dout_reg[21:20];
assign btb_mem_way3_target_pc[19:0] = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[85:66]
                                    : btb_data_dout_reg[85:66];
assign btb_mem_way2_target_pc[19:0] = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[63:44]
                                    : btb_data_dout_reg[63:44];
assign btb_mem_way1_target_pc[19:0] = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[41:22]
                                    : btb_data_dout_reg[41:22];
assign btb_mem_way0_target_pc[19:0] = (btb_rd_flop && !ip_way_mispred)
                                    ? btb_data_dout[19:0]
                                    : btb_data_dout_reg[19:0];
always @(posedge forever_cpuclk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_index_flop[9:0] <= 10'b0;
  else
    btb_index_flop[9:0] <= btb_index[9:0];
end
assign btb_buf_valid                = (btb_index_flop[9:0] == refill_buf_index[9:0]) && refill_buf_updt_vld;
assign btb_buf_tag_data[9:0]        = refill_buf_tag[9:0];
assign btb_buf_way_pred[1:0]        = refill_buf_way_pred[1:0];
assign btb_buf_target_pc[19:0]      = refill_buf_target_pc[19:0];
assign btb_ifdp_way0_target[19:0] = ~((btb_mem_way0_valid)
                                  ? btb_mem_way0_target_pc[19:0]
                                  : btb_buf_target_pc[19:0]);
assign btb_ifdp_way0_pred[1:0]    = (btb_mem_way0_valid)
                                  ? btb_mem_way0_way_pred[1:0]
                                  : btb_buf_way_pred[1:0];
assign btb_ifdp_way0_tag[9:0]     = (btb_mem_way0_valid)
                                  ? btb_mem_way0_tag_data[9:0]
                                  : btb_buf_tag_data[9:0];
assign btb_ifdp_way0_vld          = (btb_mem_way0_valid || btb_buf_valid) &&
                                    cp0_ifu_btb_en;
assign btb_ifdp_way1_target[19:0] = btb_mem_way1_target_pc[19:0];
assign btb_ifdp_way1_pred[1:0]    = btb_mem_way1_way_pred[1:0];
assign btb_ifdp_way1_tag[9:0]     = btb_mem_way1_tag_data[9:0];
assign btb_ifdp_way1_vld          = btb_mem_way1_valid && cp0_ifu_btb_en;
assign btb_ifdp_way2_target[19:0] = btb_mem_way2_target_pc[19:0];
assign btb_ifdp_way2_pred[1:0]    = btb_mem_way2_way_pred[1:0];
assign btb_ifdp_way2_tag[9:0]     = btb_mem_way2_tag_data[9:0];
assign btb_ifdp_way2_vld          = btb_mem_way2_valid && cp0_ifu_btb_en;
assign btb_ifdp_way3_target[19:0] = btb_mem_way3_target_pc[19:0];
assign btb_ifdp_way3_pred[1:0]    = btb_mem_way3_way_pred[1:0];
assign btb_ifdp_way3_tag[9:0]     = btb_mem_way3_tag_data[9:0];
assign btb_ifdp_way3_vld          = btb_mem_way3_valid && cp0_ifu_btb_en;
assign btb_inv_reg_upd_clk = forever_cpuclk;
assign btb_inv_reg_upd_clk_en = btb_inv_on_reg || ifctrl_btb_inv;
 parameter INV_CNT_VAL = 10'b0111111111;
always @(posedge btb_inv_reg_upd_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_inval_cnt[9:0] <= 10'b0;
  else if(btb_inv_on_reg)
    btb_inval_cnt[9:0] <= btb_inval_cnt[9:0] - 10'b1;
  else if(ifctrl_btb_inv)
    btb_inval_cnt[9:0] <= INV_CNT_VAL;
  else
    btb_inval_cnt[9:0] <= btb_inval_cnt[9:0];
end
always @(posedge btb_inv_reg_upd_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    btb_inv_on_reg <= 1'b0;
  else if(!(|btb_inval_cnt[9:0]) && btb_inv_on_reg)
    btb_inv_on_reg <= 1'b0;
  else if(ifctrl_btb_inv)
    btb_inv_on_reg <= 1'b1;
  else
    btb_inv_on_reg <= btb_inv_on_reg;
end
assign btb_ifctrl_inv_done = !btb_inv_on_reg;
assign btb_ifctrl_inv_on   = btb_inv_on_reg;
assign refill_buf_updt_clk = forever_cpuclk ;
assign refill_buf_updt_clk_en = btb_inv_on_reg ||
                                addrgen_btb_update_vld ||
                                ipctrl_btb_way_pred_error ||
                                ibdp_btb_miss ||
                                after_addrgen_btb_chgflw_first ||
                                after_addrgen_btb_chgflw_second;
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
  refill_buf_index[9:0] <= 10'b0;
else if(btb_inv_on_reg)
  refill_buf_index[9:0] <= 10'b0;
else if(addrgen_btb_update_vld && !chgflw_higher_than_addrgen)
  refill_buf_index[9:0] <= addrgen_btb_index[9:0];
else if(ipctrl_btb_way_pred_error && !chgflw_higher_than_ip)
  refill_buf_index[9:0] <= btb_index_pc_record[12:3];
else
  refill_buf_index[9:0] <= refill_buf_index[9:0];
end
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    refill_buf_target_pc[19:0] <= 20'b0;
  else if(btb_inv_on_reg)
    refill_buf_target_pc[19:0] <= 20'b0;
  else if(addrgen_btb_update_vld && !chgflw_higher_than_addrgen)
    refill_buf_target_pc[19:0] <= addrgen_btb_target_pc[19:0];
  else if(ipctrl_btb_way_pred_error && !chgflw_higher_than_ip)
    refill_buf_target_pc[19:0] <= btb_target_pc_record[19:0];
  else
    refill_buf_target_pc[19:0] <= refill_buf_target_pc[19:0];
end
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    refill_buf_tag[9:0] <= 10'b0;
  else if(btb_inv_on_reg)
    refill_buf_tag[9:0] <= 10'b0;
  else if(addrgen_btb_update_vld && !chgflw_higher_than_addrgen)
    refill_buf_tag[9:0] <= addrgen_btb_tag[9:0];
  else if(ipctrl_btb_way_pred_error && !chgflw_higher_than_ip)
    refill_buf_tag[9:0] <= {btb_index_pc_record[19:13],btb_index_pc_record[2:0]};
  else
    refill_buf_tag[9:0] <= refill_buf_tag[9:0];
end
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    refill_buf_way_pred[1:0] <= 2'b11;
  else if(btb_inv_on_reg)
    refill_buf_way_pred[1:0] <= 2'b11;
  else if(btb_miss_way_pred_rd)
    refill_buf_way_pred[1:0] <= ipctrl_btb_way_pred[1:0];
  else if(ipctrl_btb_way_pred_error && !chgflw_higher_than_ip)
    refill_buf_way_pred[1:0] <= ipctrl_btb_way_pred[1:0];
  else
    refill_buf_way_pred[1:0] <= refill_buf_way_pred[1:0];
end
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    refill_buf_valid <= 1'b0;
  else if(btb_inv_on_reg)
    refill_buf_valid <= 1'b0;
  else if(btb_miss_way_pred_rd)
    refill_buf_valid <= 1'b1;
  else if(ipctrl_btb_way_pred_error && !chgflw_higher_than_ip)
    refill_buf_valid <= 1'b1;
  else if(ibdp_btb_miss && !chgflw_higher_than_ip ||
          addrgen_btb_update_vld)
    refill_buf_valid <= 1'b0;
  else
    refill_buf_valid <= refill_buf_valid;
end
assign refill_buf_updt_vld = (ibdp_btb_miss ||
                              ipctrl_btb_way_pred_error) &&
                              !chgflw_higher_than_ip &&
                              refill_buf_valid;
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    after_addrgen_btb_chgflw_first <= 1'b0;
  else if(btb_inv_on_reg)
    after_addrgen_btb_chgflw_first <= 1'b0;
  else if(addrgen_btb_update_vld && !chgflw_higher_than_addrgen)
    after_addrgen_btb_chgflw_first <= 1'b1;
  else
    after_addrgen_btb_chgflw_first <= 1'b0;
end
always @(posedge refill_buf_updt_clk or negedge cpurst_b)
begin
  if(!cpurst_b)
    after_addrgen_btb_chgflw_second <= 1'b0;
  else if(btb_inv_on_reg)
    after_addrgen_btb_chgflw_second <= 1'b0;
  else if(after_addrgen_btb_chgflw_first && !chgflw_higher_than_if && !pcgen_stall)
    after_addrgen_btb_chgflw_second <= 1'b1;
  else
    after_addrgen_btb_chgflw_second <= 1'b0;
end
assign btb_miss_way_pred_rd = after_addrgen_btb_chgflw_second;
assign chgflw_higher_than_ip      = pcgen_btb_chgflw_higher_than_ip;
assign chgflw_higher_than_addrgen = pcgen_btb_chgflw_higher_than_addrgen;
assign chgflw_higher_than_if      = pcgen_btb_chgflw_higher_than_if;
assign pcgen_stall                = pcgen_btb_stall;
always @* assert((btb_ifdp_way0_target[19:0]) == 20'((btb_mem_way0_valid)
                                  ? btb_mem_way0_target_pc[19:0]
                                  : btb_buf_target_pc[19:0]));
endmodule