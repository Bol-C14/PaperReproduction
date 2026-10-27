`timescale 1ns/1ps
module ct_ebiu_ncwt_entry(
  aw_needissue,
  bfifo_pop_bresp,
  ciu_icg_en,
  cpurst_b,
  forever_cpuclk,
  nc_wo_rd_depd_ncwt_x,
  nc_wo_wr_dped_ncwt_x,
  ncq_xx_araddr,
  ncq_xx_awaddr,
  ncq_xx_awid,
  ncwt_bresp_accept_en_x,
  ncwt_bus_bresp_updt_en_x,
  ncwt_bvalid_x,
  ncwt_create_dp_en_x,
  ncwt_create_en_x,
  ncwt_ctrl_clk,
  ncwt_piu0_sel_x,
  ncwt_piu1_sel_x,
  ncwt_piu2_sel_x,
  ncwt_piu3_sel_x,
  ncwt_vld_x,
  ncwt_wdata_create_en_x,
  pad_yy_icg_scan_en,
  x_ncwt_bus
);
input           aw_needissue;
input   [1 :0]  bfifo_pop_bresp;
input           ciu_icg_en;
input           cpurst_b;
input           forever_cpuclk;
input   [39:0]  ncq_xx_araddr;
input   [39:0]  ncq_xx_awaddr;
input   [7 :0]  ncq_xx_awid;
input           ncwt_bresp_accept_en_x;
input           ncwt_bus_bresp_updt_en_x;
input           ncwt_create_dp_en_x;
input           ncwt_create_en_x;
input           ncwt_ctrl_clk;
input           ncwt_wdata_create_en_x;
input           pad_yy_icg_scan_en;
output          nc_wo_rd_depd_ncwt_x;
output          nc_wo_wr_dped_ncwt_x;
output          ncwt_bvalid_x;
output          ncwt_piu0_sel_x;
output          ncwt_piu1_sel_x;
output          ncwt_piu2_sel_x;
output          ncwt_piu3_sel_x;
output          ncwt_vld_x;
output  [9 :0]  x_ncwt_bus;
`define  PA_WIDTH 40;
reg     [7 :0]  ncwt_addr;
reg     [1 :0]  ncwt_bresp;
reg             ncwt_bus_done;
reg             ncwt_gm_fail;
reg     [7 :0]  ncwt_id;
reg             ncwt_resp_done;
reg             ncwt_resp_ready;
reg             ncwt_vld;
wire            aw_needissue;
wire    [1 :0]  bfifo_pop_bresp;
wire            ciu_icg_en;
wire            cpurst_b;
wire            forever_cpuclk;
wire            nc_wo_rd_depd_ncwt_x;
wire            nc_wo_wr_dped_ncwt_x;
wire    [39:0]  ncq_xx_araddr;
wire    [39:0]  ncq_xx_awaddr;
wire    [7 :0]  ncq_xx_awid;
wire            ncwt_bresp_accept_en_x;
wire            ncwt_bus_bresp_updt_en_x;
wire            ncwt_bvalid_x;
wire            ncwt_clk;
wire            ncwt_create_dp_en_x;
wire            ncwt_create_en_x;
wire            ncwt_ctrl_clk;
wire            ncwt_lock;
wire            ncwt_lock_raw;
wire    [2 :0]  ncwt_mid;
wire    [3 :0]  ncwt_mid_sel;
wire            ncwt_piu0_sel_x;
wire            ncwt_piu1_sel_x;
wire            ncwt_piu2_sel_x;
wire            ncwt_piu3_sel_x;
wire            ncwt_pop_en;
wire            ncwt_vld_x;
wire            ncwt_wdata_create_en_x;
wire            pad_yy_icg_scan_en;
wire    [9 :0]  x_ncwt_bus;
parameter ADDRW = `PA_WIDTH;
parameter WO_EX_ID = 5'b11110;
assign ncwt_pop_en = ncwt_vld &
                     ncwt_resp_done &
                     ncwt_bus_done;
always @(posedge ncwt_ctrl_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    ncwt_vld   <= 1'b0;
  else if(ncwt_create_en_x)
    ncwt_vld <= 1'b1;
  else if(ncwt_pop_en) 
    ncwt_vld <= 1'b0;
  else
    ncwt_vld <= ncwt_vld;
end
always @(posedge ncwt_ctrl_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    ncwt_resp_ready <= 1'b0;
  else if (ncwt_create_en_x)
    ncwt_resp_ready <= 1'b0;
  else if (ncwt_wdata_create_en_x & (!ncwt_lock | ncwt_gm_fail))
    ncwt_resp_ready <= 1'b1;
  else if (!ncwt_resp_ready & ncwt_bus_bresp_updt_en_x)
    ncwt_resp_ready <= 1'b1;
end
always @(posedge ncwt_ctrl_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    ncwt_resp_done <= 1'b0;
  else if (ncwt_create_en_x)
    ncwt_resp_done <= 1'b0;
  else if (ncwt_bresp_accept_en_x)
    ncwt_resp_done <= 1'b1;
end
always @(posedge ncwt_ctrl_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    ncwt_bus_done <= 1'b0;
  else if (ncwt_create_en_x)
    ncwt_bus_done <= ncwt_lock_raw & !aw_needissue;
  else if (ncwt_bus_bresp_updt_en_x)
    ncwt_bus_done <= 1'b1;
end
always @(posedge ncwt_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
  begin
    ncwt_addr[7:0] <= 8'b0;
    ncwt_id[7:0]   <= 8'b0;
    ncwt_gm_fail   <= 1'b0;
  end
  else if (ncwt_create_en_x)
  begin
    ncwt_addr[7:0] <= ncq_xx_awaddr[13:6];
    ncwt_id[7:0]   <= ncq_xx_awid[7:0];
    ncwt_gm_fail   <= !aw_needissue;
  end
end
assign ncwt_lock_raw = ncq_xx_awid[4:0] == WO_EX_ID;
assign ncwt_lock = ncwt_id[4:0] == WO_EX_ID;
always @(posedge ncwt_ctrl_clk or negedge cpurst_b)
begin
  if (!cpurst_b)
    ncwt_bresp[1:0] <= 2'b00;
  else if (ncwt_create_en_x & ncwt_lock_raw & !aw_needissue)
    ncwt_bresp[1:0] <= 2'b00;  
  else if (ncwt_bus_bresp_updt_en_x)
    ncwt_bresp[1:0] <= bfifo_pop_bresp[1:0];
end
assign ncwt_mid[2:0] = ncwt_id[7:5];
assign ncwt_mid_sel[3:0] = (4'b1 << ncwt_mid[1:0]) | {4{ncwt_mid[2]}};
assign ncwt_piu0_sel_x = ncwt_mid_sel[0];
assign ncwt_piu1_sel_x = ncwt_mid_sel[1];
assign ncwt_piu2_sel_x = ncwt_mid_sel[2];
assign ncwt_piu3_sel_x = ncwt_mid_sel[3];
assign ncwt_vld_x = ncwt_vld;
assign nc_wo_wr_dped_ncwt_x = (ncq_xx_awaddr[13:6] == ncwt_addr[7:0]) && ncwt_vld;
assign nc_wo_rd_depd_ncwt_x = (ncq_xx_araddr[13:6] == ncwt_addr[7:0]) && ncwt_vld;
assign ncwt_bvalid_x   = ncwt_vld & ncwt_resp_ready & !ncwt_resp_done;
assign x_ncwt_bus[9:0] = {ncwt_id[7:0], ncwt_bresp[1:0]};
assign ncwt_clk = forever_cpuclk;
always @* assert((ncwt_piu0_sel_x) == (ncwt_mid_sel[0]));
endmodule