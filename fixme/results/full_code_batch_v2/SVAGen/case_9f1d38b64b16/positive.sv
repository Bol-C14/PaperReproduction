`timescale 1ns/1ps
module ct_ciu_ctcq_respq_entry(
  ciu_icg_en,
  cpurst_b,
  forever_cpuclk,
  pad_yy_icg_scan_en,
  respq_create_cmplt_init,
  respq_create_dvm,
  respq_create_en_x,
  respq_dvm_x,
  respq_ebiu_resp_create_en_x,
  respq_l2c_resp_create_en_x,
  respq_piu0_resp_create_en_x,
  respq_piu1_resp_create_en_x,
  respq_piu2_resp_create_en_x,
  respq_piu3_resp_create_en_x,
  respq_vld_x
);
input          ciu_icg_en;
input          cpurst_b;
input          forever_cpuclk;
input          pad_yy_icg_scan_en;
input   [5:0]  respq_create_cmplt_init;
input          respq_create_dvm;
input          respq_create_en_x;
input          respq_ebiu_resp_create_en_x;
input          respq_l2c_resp_create_en_x;
input          respq_piu0_resp_create_en_x;
input          respq_piu1_resp_create_en_x;
input          respq_piu2_resp_create_en_x;
input          respq_piu3_resp_create_en_x;
output         respq_dvm_x;
output         respq_vld_x;
reg            respq_dvm;
reg            respq_ebiu_cmplt;
reg            respq_l2c_cmplt;
reg            respq_piu0_cmplt;
reg            respq_piu1_cmplt;
reg            respq_piu2_cmplt;
reg            respq_piu3_cmplt;
reg            respq_vld;
wire           ciu_icg_en;
wire           cpurst_b;
wire           forever_cpuclk;
wire           pad_yy_icg_scan_en;
wire    [5:0]  respq_create_cmplt_init;
wire           respq_create_dvm;
wire           respq_create_en;
wire           respq_create_en_x;
wire           respq_dvm_x;
wire           respq_ebiu_resp_create_en;
wire           respq_ebiu_resp_create_en_x;
wire           respq_entry_clk_en;
wire           respq_l2c_resp_create_en;
wire           respq_l2c_resp_create_en_x;
wire           respq_piu0_resp_create_en;
wire           respq_piu0_resp_create_en_x;
wire           respq_piu1_resp_create_en;
wire           respq_piu1_resp_create_en_x;
wire           respq_piu2_resp_create_en;
wire           respq_piu2_resp_create_en_x;
wire           respq_piu3_resp_create_en;
wire           respq_piu3_resp_create_en_x;
wire           respq_pop_en;
wire           respq_vld_x;
wire           respqentyclk;
assign respqentyclk = forever_cpuclk;
assign respq_pop_en  = respq_l2c_cmplt
                     & respq_ebiu_cmplt
                     & respq_piu3_cmplt
                     & respq_piu2_cmplt
                     & respq_piu1_cmplt
                     & respq_piu0_cmplt
                     & respq_vld;
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_vld <= 1'b0;
  else
  begin
    if(respq_create_en)
      respq_vld <= 1'b1;
    else if(respq_pop_en)
      respq_vld <= 1'b0;
    else
      respq_vld <= respq_vld;
  end
end
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_l2c_cmplt <= 1'b0;
  else if(respq_create_en)
    respq_l2c_cmplt <= respq_create_cmplt_init[5];
  else if(respq_l2c_resp_create_en)
    respq_l2c_cmplt <= 1'b1;
  else
    respq_l2c_cmplt <= respq_l2c_cmplt;
end
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_ebiu_cmplt <= 1'b0;
  else if(respq_create_en)
    respq_ebiu_cmplt <= respq_create_cmplt_init[4];
  else if(respq_ebiu_resp_create_en)
    respq_ebiu_cmplt <= 1'b1;
  else
    respq_ebiu_cmplt <= respq_ebiu_cmplt;
end
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_piu3_cmplt <= 1'b0;
  else if(respq_create_en)
    respq_piu3_cmplt <= respq_create_cmplt_init[3];
  else if(respq_piu3_resp_create_en)
    respq_piu3_cmplt <= 1'b1;
  else
    respq_piu3_cmplt <= respq_piu3_cmplt;
end
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_piu2_cmplt <= 1'b0;
  else if(respq_create_en)
    respq_piu2_cmplt <= respq_create_cmplt_init[2];
  else if(respq_piu2_resp_create_en)
    respq_piu2_cmplt <= 1'b1;
  else
    respq_piu2_cmplt <= respq_piu2_cmplt;
end
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_piu1_cmplt <= 1'b0;
  else if(respq_create_en)
    respq_piu1_cmplt <= respq_create_cmplt_init[1];
  else if(respq_piu1_resp_create_en)
    respq_piu1_cmplt <= 1'b1;
  else
    respq_piu1_cmplt <= respq_piu1_cmplt;
end
always @(posedge respqentyclk or negedge cpurst_b)
begin
  if(~cpurst_b)
    respq_piu0_cmplt <= 1'b0;
  else if(respq_create_en)
    respq_piu0_cmplt <= respq_create_cmplt_init[0];
  else if(respq_piu0_resp_create_en)
    respq_piu0_cmplt <= 1'b1;
  else
    respq_piu0_cmplt <= respq_piu0_cmplt;
end
always @(posedge respqentyclk)
begin
  if (respq_create_en)
    respq_dvm <= respq_create_dvm;
  else
    respq_dvm <= respq_dvm;
end
assign respq_entry_clk_en =  respq_create_en
                          || respq_pop_en
                          || respq_l2c_resp_create_en
                          || respq_ebiu_resp_create_en
                          || respq_piu3_resp_create_en
                          || respq_piu2_resp_create_en
                          || respq_piu1_resp_create_en
                          || respq_piu0_resp_create_en;
assign respq_create_en = respq_create_en_x;
assign respq_l2c_resp_create_en  = respq_l2c_resp_create_en_x;
assign respq_ebiu_resp_create_en = respq_ebiu_resp_create_en_x;
assign respq_piu3_resp_create_en = respq_piu3_resp_create_en_x;
assign respq_piu2_resp_create_en = respq_piu2_resp_create_en_x;
assign respq_piu1_resp_create_en = respq_piu1_resp_create_en_x;
assign respq_piu0_resp_create_en = respq_piu0_resp_create_en_x;
assign respq_vld_x     = respq_vld;
assign respq_dvm_x     = respq_dvm;
always @* assert((respq_vld_x) == (respq_vld));
endmodule