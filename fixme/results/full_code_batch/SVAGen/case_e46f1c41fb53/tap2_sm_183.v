`timescale 1ns/1ps
module tap2_sm(
  debug_wake_vld,
  pad_had_jtg_tap_en,
  tclk,
  tms_i,
  trst_b
);
input          pad_had_jtg_tap_en;
input          tclk;
input          tms_i;
input          trst_b;
output         debug_wake_vld;
reg     [7:0]  sm2_data_counter;
reg            sm2_read_vld;
reg     [1:0]  sm2_rs;
reg     [1:0]  sm2_rs_counter;
reg            sm2_write_vld;
reg     [3:0]  tap2_cur_st;
reg     [3:0]  tap2_nxt_st;
reg     [6:0]  tap2_rst_cnt;
wire           debug_wake_vld;
wire           pad_had_jtg_tap_en;
wire           sm2_load_rs;
wire           sm2_load_rw;
wire           sm2_rs_cdic_dr_sel;
wire           sm2_rs_had_dr_sel;
wire           sm2_shift_vld;
wire           sm2_start_vld;
wire           sm2_trn1;
wire           tap2_rst_vld;
wire           tap2_sm_tap_en;
wire           tclk;
wire           tms_i;
wire           trst_b;
parameter TAP2_RESET  = 4'b0000;
parameter TAP2_START  = 4'b0001;
parameter TAP2_RW     = 4'b0010;
parameter TAP2_RS     = 4'b0011;
parameter TAP2_TRN1   = 4'b0100;
parameter TAP2_DATA   = 4'b0101;
parameter TAP2_SYNC   = 4'b0110;
parameter TAP2_PARITY = 4'b0111;
parameter TAP2_TRN2   = 4'b1000;
assign tap2_sm_tap_en = pad_had_jtg_tap_en;
always @(posedge tclk or negedge trst_b)
begin
  if (!trst_b)
    tap2_cur_st[3:0] <= TAP2_RESET;
  else if (tap2_rst_vld && tms_i)
    tap2_cur_st[3:0] <= TAP2_RESET;
  else
    tap2_cur_st[3:0] <= tap2_nxt_st[3:0];
end
always @(posedge tclk or negedge trst_b)
begin
  if (!trst_b)
    tap2_rst_cnt[6:0] <= 7'd80;
  else
  begin
    if (!tms_i)
      tap2_rst_cnt[6:0] <= 7'd80;
    else if (tap2_rst_cnt[6:0] > 7'd0)
      tap2_rst_cnt[6:0] <= tap2_rst_cnt[6:0] - 7'd1;
    else
      tap2_rst_cnt[6:0] <= 7'd80;
  end
end
assign tap2_rst_vld = (tap2_rst_cnt[6:0] == 7'd00);
always @( sm2_data_counter[7:0]
       or tap2_cur_st[3:0]
       or tap2_sm_tap_en
       or sm2_read_vld
       or tms_i
       or sm2_rs_counter[1:0])
begin
 case (tap2_cur_st[3:0])
    TAP2_RESET : begin
      if (tap2_sm_tap_en) begin
        if (tms_i)
          tap2_nxt_st[3:0] = TAP2_START;
        else
          tap2_nxt_st[3:0] = TAP2_RW;
      end
      else
        tap2_nxt_st[3:0] = TAP2_RESET;
    end
    TAP2_START : begin 
      if (!tms_i) 
        tap2_nxt_st[3:0] = TAP2_RW;
      else
          tap2_nxt_st[3:0] = TAP2_START;
    end
    TAP2_RW : begin  
      tap2_nxt_st[3:0] = TAP2_RS;
    end
    TAP2_RS : begin 
      if (sm2_rs_counter[1:0] == 2'd0)
        tap2_nxt_st[3:0] = TAP2_TRN1;
      else
        tap2_nxt_st[3:0] = TAP2_RS;
    end
    TAP2_TRN1 : begin 
      if (sm2_read_vld)  
        tap2_nxt_st[3:0] = TAP2_SYNC;
      else               
        tap2_nxt_st[3:0] = TAP2_DATA;
    end
    TAP2_SYNC : begin
      tap2_nxt_st[3:0] = TAP2_DATA;
    end
    TAP2_DATA : begin 
      if (sm2_data_counter[7:0] == 8'd0)
        tap2_nxt_st[3:0] = TAP2_PARITY;
      else
        tap2_nxt_st[3:0] = TAP2_DATA;
    end
    TAP2_PARITY : begin
      tap2_nxt_st[3:0] = TAP2_TRN2;
    end
    TAP2_TRN2 : begin
      tap2_nxt_st[3:0] = TAP2_START;
    end
    default : begin
      tap2_nxt_st[3:0] = TAP2_RESET;
    end
  endcase
end
assign sm2_start_vld  = (tap2_cur_st[3:0] == TAP2_RW);
assign sm2_load_rw    = (tap2_cur_st[3:0] == TAP2_RW);
assign sm2_load_rs    = (tap2_cur_st[3:0] == TAP2_RS);
assign sm2_trn1       = (tap2_cur_st[3:0] == TAP2_TRN1);
assign sm2_shift_vld  = (tap2_cur_st[3:0] == TAP2_DATA);
always @(posedge tclk or negedge trst_b)
begin
  if(!trst_b)
  begin
    sm2_read_vld <= 1'b0;
    sm2_write_vld <= 1'b0;
  end
  else if (sm2_load_rw)
  begin
    sm2_read_vld <= tms_i;
    sm2_write_vld <= !tms_i;
  end
  else
  begin
    sm2_read_vld <= sm2_read_vld;
    sm2_write_vld <= !tms_i;
  end
end
assign debug_wake_vld = sm2_write_vld;
always @(posedge tclk)
begin
  if (sm2_start_vld)
    sm2_rs_counter[1:0] <= 2'd1;
  else if (sm2_load_rs)
    sm2_rs_counter[1:0] <= sm2_rs_counter[1:0] - 2'd1;
  else
    sm2_rs_counter[1:0] <= sm2_rs_counter[1:0];
end
always @(posedge tclk)
begin
  if (sm2_load_rs)
    sm2_rs[1:0] <= {tms_i, sm2_rs[1]};
  else
    sm2_rs[1:0] <= sm2_rs[1:0];
end
assign sm2_rs_cdic_dr_sel = sm2_rs[1:0] == 2'b01;
assign sm2_rs_had_dr_sel  = sm2_rs[1:0] == 2'b11;
always @(posedge tclk)
begin
  if (sm2_trn1) begin
    if (sm2_rs_had_dr_sel || sm2_rs_cdic_dr_sel)
      sm2_data_counter[7:0] <= 8'd31;
    else
      sm2_data_counter[7:0] <= 8'd7;
  end
  else if (sm2_shift_vld)
    sm2_data_counter[7:0] <= sm2_data_counter[7:0] - 8'd1;
  else
    sm2_data_counter[7:0] <= sm2_data_counter[7:0];
end
endmodule