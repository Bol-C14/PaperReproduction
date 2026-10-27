`timescale 1ns/1ps
module oracle_ethmonitor (
   reset,
   tx_clk,
   txd,
   tx_dv,
   tx_er,
   tx_sop,
   tx_eop,
   dst,
   src,
   prmble_len,
   pquant,
   vlan_ctl,
   len,
   frmtype,
   payload,
   payload_vld,
   is_vlan,
   is_stack_vlan,
   is_pause,
   crc_err,
   prmbl_err,
   len_err,
   payload_err,
   frame_err,
   pause_op_err,
   pause_dst_err,
   mac_err,
   end_err,
   jumbo_en,
   data_only,
   frm_rcvd);
parameter ENABLE_SHIFT16 = 1'b 0;
input   reset; 
input   tx_clk; 
input   [7:0] txd; 
input   tx_dv; 
input   tx_er; 
input   tx_sop; 
input   tx_eop; 
output   [47:0] dst; 
output   [47:0] src; 
output   [13:0] prmble_len; 
output   [15:0] pquant; 
output   [15:0] vlan_ctl; 
output   [15:0] len; 
output   [15:0] frmtype; 
output   [7:0] payload; 
output   payload_vld; 
output   is_vlan; 
output   is_stack_vlan;
output   is_pause; 
output   crc_err; 
output   prmbl_err; 
output   len_err; 
output   payload_err; 
output   frame_err; 
output   pause_op_err; 
output   pause_dst_err; 
output   mac_err; 
output   end_err; 
input   jumbo_en; 
input   data_only; 
output   frm_rcvd; 
wire    [47:0] dst; 
reg     [47:0] src; 
wire    [13:0] prmble_len; 
reg     [15:0] pquant; 
reg     [15:0] vlan_ctl; 
wire    [15:0] len; 
wire    [15:0] frmtype; 
reg     [7:0] payload; 
reg     payload_vld; 
wire    is_vlan; 
wire    is_stack_vlan;
wire    is_pause; 
reg     crc_err; 
reg     prmbl_err; 
reg     len_err; 
reg     payload_err; 
reg     frame_err; 
reg     pause_op_err; 
reg     pause_dst_err; 
reg     mac_err; 
reg     end_err; 
reg     frm_rcvd; 
reg     frm_in; 
reg     tx_clk_int; 
reg     tx_eop_reg; 
reg     [13:0] iprmble_len; 
reg     [15:0] ifrmtype; 
reg     [15:0] ilen; 
reg     [47:0] idst; 
reg     iis_vlan; 
reg     iis_stack_vlan;
reg     iis_pause; 
reg     tx_clk_dly;
parameter state_typ_s_idle = 0;
parameter state_typ_s_prmbl = 1;
parameter state_typ_s_dst = 2;
parameter state_typ_s_src = 3;
parameter state_typ_s_typelen = 4;
parameter state_typ_s_pause = 5;
parameter state_typ_s_tag = 6;
parameter state_typ_s_len = 7;
parameter state_typ_s_data = 8;
parameter state_typ_s_pad = 9;
parameter state_typ_s_crc = 10;
parameter state_typ_s_abort = 11;
parameter state_typ_s_utype = 12;
parameter state_typ_s_Dword32Aligned = 13;
reg     [3:0] state; 
reg     [3:0] last_state; 
reg     last_tx_dv; 
reg     [31:0] crc32; 
reg     [31:0] count; 
reg     [31:0] poscnt; 
reg     [7:0] datacnt; 
reg     [7:0] datainc; 
reg     tx_sof; 
reg     tx_dst; 
reg     [31:0]  process_6_crctmp; 
reg     [3:0]  V2V_process_6_i;
integer  process_11_ix; 
integer  process_12_ix; 
reg      process_12_ln; 
integer  process_14_hi; 
integer  process_14_lo; 
reg     [31:0]  process_14_cnttmp; 
integer  process_14_i; 
integer  process_14_flen; 
always @(posedge reset or posedge tx_clk)
   begin : process_1
   if (reset == 1'b 1)
      begin
      tx_eop_reg <= 1'b 0;  
      end
   else
      begin
      tx_eop_reg <= tx_eop; 
      end
   end
always @(tx_sop or tx_eop_reg)
   begin : process_2
   if (tx_sop == 1'b 1 & data_only == 1'b 1)
      begin
      frm_in <= 1'b 1;  
      end
   else if (tx_eop_reg == 1'b 1 )
      begin
      frm_in <= 1'b 0;  
      end
   end
always@(tx_clk)
begin
        tx_clk_dly <= #(1)tx_clk ;
end 
always @(frm_in or tx_dv or tx_clk_dly)
   begin : process_3
   if (frm_in == 1'b 1 && tx_dv == 1'b 1 )
      begin
      tx_clk_int <= #(1) tx_clk_dly;    
      end
   else if (frm_in==1'b1 && tx_dv == 1'b 0)
      begin
      tx_clk_int <= #(1) 1'b 0; 
      end
   else
      begin
      tx_clk_int <= #(1) tx_clk_dly;    
      end
   end
assign prmble_len = iprmble_len; 
assign frmtype = ifrmtype; 
assign len = ilen; 
assign dst = idst; 
assign is_vlan = iis_vlan; 
assign is_stack_vlan = iis_stack_vlan; 
assign is_pause = iis_pause; 
always@(last_tx_dv or tx_dv or tx_sop)
begin
        if (data_only==1'b0)
        begin
                tx_sof <= ~last_tx_dv & tx_dv; 
        end
        else
        begin
                tx_sof <= tx_sop ;
        end
end
always @(last_state or state)
   begin : process_4
   if (last_state != state_typ_s_dst & state == state_typ_s_dst)
      begin
      tx_dst <= 1'b 1;  
      end
   else
      begin
      tx_dst <= 1'b 0;  
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_5
   if (reset == 1'b 1)
      begin
      mac_err <= 1'b 0; 
      last_tx_dv <= 1'b 0;  
      end
   else
      begin
      if (tx_sof == 1'b 1)
         begin
         mac_err <= 1'b 0;  
         end
      else if (tx_er == 1'b 1 )
         begin
         mac_err <= 1'b 1;  
         end
      last_tx_dv <= tx_dv;  
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_6
   if (reset == 1'b 1)
      begin
      crc32 <= {32{1'b 1}}; 
      crc_err <= 1'b 0; 
      end
   else
      begin
      if (tx_dst == 1'b 1 | state != state_typ_s_idle & 
    state != state_typ_s_prmbl & state != state_typ_s_utype | 
    state == state_typ_s_utype & tx_dv == 1'b 1)
         begin
         if (tx_dst == 1'b 1)
            begin
            process_6_crctmp = {32{1'b 1}}; 
            end
         else
            begin
            process_6_crctmp = crc32;   
            end
         for (V2V_process_6_i = 0; V2V_process_6_i <= 7; V2V_process_6_i = V2V_process_6_i + 1)
            begin
            if ((txd[V2V_process_6_i] ^ process_6_crctmp[31]) == 1'b 1)
               begin
               process_6_crctmp = (process_6_crctmp << 1);  
               process_6_crctmp = process_6_crctmp ^ 32'h 04C11DB7; 
               end
            else
               begin
               process_6_crctmp = (process_6_crctmp << 1);  
               end
            end
         crc32 <= process_6_crctmp; 
         if (process_6_crctmp == 32'h C704DD7B)
            begin
            crc_err <= 1'b 0;   
            end
         else
            begin
            crc_err <= 1'b 1;   
            end
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_7
   if (reset == 1'b 1)
      begin
      payload <= {8{1'b 0}};    
      payload_vld <= 1'b 0; 
      payload_err <= 1'b 0; 
      datacnt <= 0; 
      end
   else
      begin
      if (state == state_typ_s_typelen)
         begin
         payload_err <= 1'b 0;  
         end
      if (state == state_typ_s_data)
         begin
         payload <= txd;    
         payload_vld <= 1'b 1;  
         if (count == 0)
            begin
            datacnt <= ({1'b 0, txd});  
            payload_err <= 1'b 0;   
            end
         else if (count == 1 )
            begin
            datainc <= ({1'b 0, txd});  
            end
         else
            begin
            datacnt <= (datacnt + datainc) % 256;   
            if (datacnt != ({1'b 0, txd}))
               begin
               payload_err <= 1'b 1;    
               end
            end
         end
      else
         begin
         payload <= {8{1'b 0}}; 
         payload_vld <= 1'b 0;  
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_8
   if (reset == 1'b 1)
      begin
      poscnt <= 0;  
      end
   else
      begin
      if (tx_dst == 1'b 1)
         begin
         poscnt <= 1;   
         end
      else
         begin
         if (poscnt < 65535)
            begin
            poscnt <= poscnt + 1'b 1;   
            end
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_9
   if (reset == 1'b 1)
      begin
      frm_rcvd <= 1'b 0;    
      end_err <= 1'b 0; 
      end
   else
      begin
      if (last_state != state_typ_s_idle & state == state_typ_s_idle)
         begin
         frm_rcvd <= 1'b 1; 
         end
      else
         begin
         frm_rcvd <= 1'b 0; 
         end
      if (tx_sof == 1'b 1)
         begin
         end_err <= 1'b 0;  
         end
      else if (last_state != state_typ_s_idle & state == state_typ_s_idle & 
    tx_dv == 1'b 1 )
         begin
         end_err <= 1'b 1;  
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_10
   if (reset == 1'b 1)
      begin
      prmbl_err <= 1'b 0;   
      iprmble_len <= 0; 
      end
   else
      begin
      if (tx_sof == 1'b 1)
         begin
         if (txd != 8'h 55)
            begin
            prmbl_err <= 1'b 1; 
            end
         else
            begin
            prmbl_err <= 1'b 0; 
            end
         if (data_only == 1'b 1)
            begin
            iprmble_len <= 0;   
            end
         else
            begin
            iprmble_len <= 1;   
            end
         end
      else if (state == state_typ_s_prmbl )
         begin
         if (txd != 8'h 55 & txd != 8'h D5)
            begin
            prmbl_err <= 1'b 1; 
            end
         iprmble_len <= iprmble_len + 1'b 1;    
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_11
   if (reset == 1'b 1)
      begin
      idst <= {48{1'b 0}};  
      src <= {48{1'b 0}};   
      end
   else
      begin
      process_11_ix = count * 8;    
      if (tx_sof == 1'b 1)
         begin
         process_11_ix = 1'b 0; 
         end
         if (tx_sof == 1'b 1 & data_only == 1'b 1 & state == state_typ_s_Dword32Aligned & ENABLE_SHIFT16 == 1'b1)
            begin
                case (count)
                1'b 0 : ;
                1'b 1 : ;
                default:;
                endcase         
             end
         if (tx_sof == 1'b 0 & data_only == 1'b 1 & ENABLE_SHIFT16 == 1'b1 & state == state_typ_s_dst)
            begin
            case (count)
            1'b 0:
               begin
               idst[7:0] <= txd[7:0];  
               end
            1'b 1:
               begin
               idst[15:8] <= txd[7:0]; 
               end
            2'b 10:
               begin
               idst[23:16] <= txd[7:0];    
               end
            2'b 11:
               begin
               idst[31:24] <= txd[7:0];    
               end
            3'b 100:
               begin
               idst[39:32] <= txd[7:0];    
               end
            3'b 101:
               begin
               idst[47:40] <= txd[7:0];    
               end
            default:
               ;
            endcase         
           end
      if (tx_sof == 1'b 1 & data_only == 1'b 1 & ENABLE_SHIFT16 == 1'b0| state == state_typ_s_dst)
         begin
         case (count)
         1'b 0:
            begin
            idst[7:0] <= txd[7:0];  
            end
         1'b 1:
            begin
            idst[15:8] <= txd[7:0]; 
            end
         2'b 10:
            begin
            idst[23:16] <= txd[7:0];    
            end
         2'b 11:
            begin
            idst[31:24] <= txd[7:0];    
            end
         3'b 100:
            begin
            idst[39:32] <= txd[7:0];    
            end
         3'b 101:
            begin
            idst[47:40] <= txd[7:0];    
            end
         default:
            ;
         endcase         end
      if (state == state_typ_s_src)
         begin
        case (count)
         1'b 0:
            begin
            src[7:0] <= txd[7:0];   
            end
         1'b 1:
            begin
            src[15:8] <= txd[7:0];  
            end
         2'b 10:
            begin
            src[23:16] <= txd[7:0]; 
            end
         2'b 11:
            begin
            src[31:24] <= txd[7:0]; 
            end
         3'b 100:
            begin
            src[39:32] <= txd[7:0]; 
            end
         3'b 101:
            begin
            src[47:40] <= txd[7:0]; 
            end
         default:
            ;
         endcase         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_12
   if (reset == 1'b 1)
      begin
      ilen <= {16{1'b 0}};  
      ifrmtype <= {16{1'b 0}};  
      vlan_ctl <= {16{1'b 0}};  
      iis_vlan <= 1'b 0;    
      len_err <= 1'b 0; 
      iis_stack_vlan <= 1'b0;
      end
   else
      begin
      process_12_ix = 4'b 1000 - count * 8; 
      if (state == state_typ_s_typelen)
         begin
        case (count)
         1'b 0:
            begin
            ifrmtype[15:8] <= txd;  
            ilen[15:8] <= txd;  
            end
         1'b 1:
            begin
            ifrmtype[7:0] <= txd;   
            ilen[7:0] <= txd;   
            end
         default:
            ;
         endcase                
         vlan_ctl <= {16{1'b 0}};   
         iis_vlan <= 1'b 0; 
         len_err  <= 1'b 0; 
         end
         if(state==state_typ_s_typelen)
         begin
                iis_stack_vlan <= 1'b0 ;
         end 
         else if (last_state == state_typ_s_len & state == state_typ_s_tag)
         begin
                iis_stack_vlan <= 1'b1 ;
         end
      else if (state == state_typ_s_len )
         begin
         case (count)
         1'b 0:
            begin
            ifrmtype[15:8] <= txd;  
            ilen[15:8] <= txd;  
            end
         1'b 1:
            begin
            ifrmtype[7:0] <= txd;   
            ilen[7:0] <= txd;   
            end
         default:
            ;
         endcase    
         end
      else if (state == state_typ_s_tag )
         begin
         iis_vlan <= 1'b 1; 
        case (count)
         1'b 0:
            begin
            vlan_ctl[15:8] <= txd;  
            end
         1'b 1:
            begin
            vlan_ctl[7:0] <= txd;   
            end
         default:
            ;
         endcase         end
      if (last_state == state_typ_s_crc & state == state_typ_s_idle & 
    iis_pause == 1'b 0 & (iis_vlan == 1'b 0 & 
    ilen > 45 | iis_vlan == 1'b 1 & 
    ilen > 41))
         begin
         if (tx_dv == 1'b 1 | 
             iis_stack_vlan == 1'b 1 & ilen != poscnt - 5'b 11010 |
             (iis_vlan == 1'b 1 & iis_stack_vlan == 1'b 0) & ilen != poscnt - 5'b 10110 | 
             iis_vlan == 1'b 0 & ilen != poscnt - 5'b 10010)
            begin
            len_err <= 1'b 1;   
            end
         else
            begin
            len_err <= 1'b 0;   
            end
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_13
   if (reset == 1'b 1)
      begin
      pquant <= {16{1'b 0}};    
      iis_pause <= 1'b 0;   
      pause_op_err <= 1'b 0;    
      pause_dst_err <= 1'b 0;   
      end
   else
      begin
      if (tx_sof == 1'b 1)
         begin
         iis_pause <= 1'b 0;    
         pause_op_err <= 1'b 0; 
         pause_dst_err <= 1'b 0;    
         end
      if (state == state_typ_s_pause)
         begin
         iis_pause <= 1'b 1;    
        case (count)
            2'b 10:
               begin
               pquant[15:8] <= txd; 
               end
            2'b 11:
               begin
               pquant[7:0] <= txd;  
               end
            default:
               ;
            endcase            
        if (count == 0 & txd != 8'h 00 | count == 1 & txd != 8'h 01 )
            begin
            pause_op_err <= 1'b 1;  
            end
         if (idst != 48'h 010000c28001)
            begin
            pause_dst_err <= 1'b 1; 
            end
         end
      end
   end
always @(posedge tx_clk_int or posedge reset)
   begin : process_14
   if (reset == 1'b 1)
      begin
      state <= state_typ_s_idle;    
      last_state <= state_typ_s_idle;   
      count <= 0;   
      frame_err <= 1'b 0;   
      end
   else
      begin
      last_state <= state;  
      if (count < 65535)
         begin
         process_14_cnttmp = count + 1'b 1; 
         end
      else
         begin
         process_14_cnttmp = count; 
         end
      if (state != state_typ_s_idle & state != state_typ_s_abort & 
    state != state_typ_s_utype & tx_dv == 1'b 0)
         begin
         state <= state_typ_s_abort;    
         end
      else
         begin
         case (state)
         state_typ_s_abort:
            begin
            if (tx_dv == 1'b 1)
               begin
               if (last_tx_dv == 1'b 0 & data_only == 1'b 1)
                  begin
                  if (ENABLE_SHIFT16 == 1'b0)
                  state <= state_typ_s_dst; 
                  else
                   state <= state_typ_s_Dword32Aligned;                   
                  process_14_cnttmp = 1'b 1;    
                  frame_err <= 1'b 0;   
                  end
               else
                  begin
                  state <= state_typ_s_abort;   
                  end
               end
            else
               begin
               state <= state_typ_s_idle;   
               end
            frame_err <= 1'b 1; 
            end
         state_typ_s_idle:
            begin
            if (tx_sof == 1'b 1)
               begin
               process_14_cnttmp = 1'b 1;   
               frame_err <= 1'b 0;  
               if (data_only == 1'b 1)
                  begin
                  if (ENABLE_SHIFT16 == 1'b0)
                  state <= state_typ_s_dst; 
                  else
                   state <= state_typ_s_Dword32Aligned;                   
                  end
               else
                  begin
                  state <= state_typ_s_prmbl;   
                  end
               end
            else
               begin
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_prmbl:
            begin
            if (txd == 8'h D5)
               begin
               state <= state_typ_s_dst;    
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_Dword32Aligned:
           begin
           if (count == 1)
              begin
              state <= state_typ_s_dst;   
              process_14_cnttmp = 1'b 0;  
              end
           end
         state_typ_s_dst:
            begin
            if (count == 5)
               begin
               state <= state_typ_s_src;    
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_src:
            begin
            if (count == 5)
               begin
               state <= state_typ_s_typelen;    
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_typelen:
            begin
            if (count != 0)
               begin
               process_14_cnttmp = 1'b 0;   
               process_14_flen = ({1'b 0, ilen[15:8], txd});    
               if (process_14_flen <= 1500)
                  begin
                  if (process_14_flen != 0)
                     begin
                     state <= state_typ_s_data; 
                     end
                  else
                     begin
                     if (data_only == 1'b 1)
                        begin
                        state <= state_typ_s_idle;  
                        end
                     else
                        begin
                        state <= state_typ_s_pad;   
                        end
                     end
                  end
               else
                  begin
                  if (process_14_flen == 16'h 8808)
                     begin
                     state <= state_typ_s_pause;    
                     end
                  else if (process_14_flen == 16'h 8100 )
                     begin
                     state <= state_typ_s_tag;  
                     end
                  else
                     begin
                     state <= state_typ_s_utype;    
                     end
                  end
               end
            end
         state_typ_s_pause:
            begin
            if (count >= 3)
               begin
               state <= state_typ_s_pad;    
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_tag:
            begin
            if (count >= 1)
               begin
               state <= state_typ_s_len;    
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_len:
            begin
            if (count >= 1)
               begin
               process_14_cnttmp = 1'b 0;   
               process_14_flen = ({1'b 0, ilen[15:8], txd});    
               if ( process_14_flen == 16'h8100)
               begin
                state <= state_typ_s_tag;
               end
               else if (process_14_flen != 0)
                  begin
                  state <= state_typ_s_data;    
                  end
               else
                  begin
                  if (data_only == 1'b 1)
                     begin
                     state <= state_typ_s_idle; 
                     end
                  else
                     begin
                     state <= state_typ_s_pad;  
                     end
                  end
               end
            end
         state_typ_s_data:
            begin
            if (count >= ilen - 1'b 1)
               begin
               process_14_cnttmp = 1'b 0;   
               if (data_only == 1'b 1)
                  begin
                  state <= state_typ_s_idle;    
                  end
               else if (poscnt < 6'b 111100 - 1'b 1 )
                  begin
                  state <= state_typ_s_pad; 
                  end
               else
                  begin
                  state <= state_typ_s_crc; 
                  end
               end
            end
         state_typ_s_pad:
            begin
            if (poscnt >= 6'b 111100 - 1'b 1)
               begin
               state <= state_typ_s_crc;    
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_crc:
            begin
            if (count >= 3)
               begin
               state <= state_typ_s_idle;   
               process_14_cnttmp = 1'b 0;   
               end
            end
         state_typ_s_utype:
            begin
            if (tx_dv == 1'b 0)
               begin
               state <= state_typ_s_idle;   
               process_14_cnttmp = 1'b 0;   
               end
            end
         endcase
         end
      count <= process_14_cnttmp;   
      end
   end
endmodule