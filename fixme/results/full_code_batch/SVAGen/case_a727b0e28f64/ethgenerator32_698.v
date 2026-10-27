`timescale 1ns/1ps
module ethgenerator32 (reset,
   rx_clk,
   rxd,
   rx_dv,
   rx_er,
   sop,
   eop,
   mac_reverse,
   dst,
   src,
   prmble_len,
   pquant,
   vlan_ctl,
   len,
   frmtype,
   cntstart,
   cntstep,
   ipg_len,
   payload_err,
   prmbl_err,
   crc_err,
   vlan_en,
   stack_vlan,
   pause_gen,
   pad_en,
   phy_err,
   end_err,
   data_only,
   start,
   done);
parameter thold = 1'b 1;
parameter ENABLE_SHIFT16 = 1'b 0;
input   reset; 
input   rx_clk; 
output   [7:0] rxd; 
output   rx_dv; 
output   rx_er; 
output   sop; 
output   eop; 
input   mac_reverse; 
input   [47:0] dst; 
input   [47:0] src; 
input   [3:0] prmble_len; 
input   [15:0] pquant; 
input   [15:0] vlan_ctl; 
input   [15:0] len; 
input   [15:0] frmtype; 
input   [7:0] cntstart; 
input   [7:0] cntstep; 
input   [15:0] ipg_len; 
input   payload_err; 
input   prmbl_err; 
input   crc_err; 
input   vlan_en; 
input   stack_vlan;
input   pause_gen; 
input   pad_en; 
input   phy_err; 
input   end_err; 
input   data_only; 
input   start; 
output   done; 
reg     [7:0] rxd; 
reg     rx_dv; 
reg     rx_er; 
reg     sop; 
reg     eop; 
reg     done; 
reg     imac_reverse; 
reg     [47:0] idst; 
reg     [47:0] isrc; 
reg     [3:0] iprmble_len; 
reg     [15:0] ipquant; 
reg     [15:0] ivlan_ctl; 
reg     [15:0] ilen; 
reg     [15:0] ifrmtype; 
reg     [7:0] icntstart; 
reg     [7:0] icntstep; 
reg     [15:0] iipg_len; 
reg     ipayload_err; 
reg     iprmbl_err; 
reg     icrc_err; 
reg     ivlan_en;
reg     istack_vlan; 
reg     ipause_gen; 
reg     ipad_en; 
reg     iphy_err; 
reg     iend_err; 
reg     idata_only; 
parameter state_typ_s_idle = 0;
parameter state_typ_s_prmbl = 1;
parameter state_typ_s_sfd = 2;
parameter state_typ_s_dst = 3;
parameter state_typ_s_src = 4;
parameter state_typ_s_pause = 5;
parameter state_typ_s_tag = 6;
parameter state_typ_s_len = 7;
parameter state_typ_s_data = 8;
parameter state_typ_s_pad = 9;
parameter state_typ_s_crc = 10;
parameter state_typ_s_enderr = 11;
parameter state_typ_s_ipg = 12;
parameter state_typ_s_stack = 13;
parameter state_typ_s_Dword32Aligned = 14;
reg     [3:0] state; 
reg     [3:0] last_state; 
reg     [3:0] last_state_dly; 
reg     [31:0] crc32; 
reg     [31:0] count; 
reg     [31:0] poscnt; 
reg     [7:0] datacnt; 
reg     [7:0] rxdata; 
reg     sop_int; 
reg     [31:0]  process_2_crctmp; 
reg     [3:0]  V2V_process_2_i; 
integer  process_7_hi=5'b 1; 
integer  process_7_lo; 
reg     [31:0]  process_7_cnttmp; 
integer  V2V_process_7_i=0;  
always @(posedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      imac_reverse <= 1'b 0;    
      idst <= {48{1'b 0}};  
      isrc <= {48{1'b 0}};  
      iprmble_len <= 0; 
      ipquant <= {16{1'b 0}};   
      ivlan_ctl <= {16{1'b 0}}; 
      ilen <= {16{1'b 0}};  
      ifrmtype <= {16{1'b 0}};  
      icntstart <= 0;   
      icntstep <= 0;    
      iipg_len <= 0;    
      ipayload_err <= 1'b 0;    
      iprmbl_err <= 1'b 0;  
      icrc_err <= 1'b 0;    
      ivlan_en <= 1'b 0;
      istack_vlan <= 1'b 0; 
      ipause_gen <= 1'b 0;  
      ipad_en <= 1'b 0; 
      iphy_err <= 1'b 0;    
      iend_err <= 1'b 0;    
      idata_only <= 1'b 0;  
      end
   else
      begin
      if (start == 1'b 1 & state == state_typ_s_idle)
         begin
         imac_reverse <= mac_reverse;   
         idst <= dst;   
         isrc <= src;   
         iprmble_len <= prmble_len; 
         ipquant <= pquant; 
         ivlan_ctl <= vlan_ctl; 
         ilen <= len;   
         ifrmtype <= frmtype;   
         icntstart <= cntstart; 
         icntstep <= cntstep;   
         iipg_len <= ipg_len;   
         ipayload_err <= payload_err;   
         iprmbl_err <= prmbl_err;   
         icrc_err <= crc_err;   
         ivlan_en <= vlan_en;
         istack_vlan <= stack_vlan; 
         ipause_gen <= pause_gen;   
         ipad_en <= pad_en; 
         iphy_err <= phy_err;   
         iend_err <= end_err;   
         idata_only <= data_only;   
         end
      end
   end
always @(negedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      crc32 <= {32{1'b 1}}; 
      end
   else
      begin
      if (last_state == state_typ_s_sfd)
         begin
         crc32 <= {32{1'b 1}};  
         end
      else if (state != state_typ_s_idle & state != state_typ_s_prmbl & last_state != state_typ_s_crc )
         begin
         crc32 <= process_2_crctmp; 
         end
      end
   end
always @(posedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      rxd <= {8{1'b 0}};    
      rx_dv <= 1'b 0;   
      rx_er <= 1'b 0;   
      end
   else
      begin
      if (last_state == state_typ_s_idle | last_state == state_typ_s_ipg)
         begin
         rxd <=  {8{1'b 0}};    
         rx_dv <=  1'b 0;   
         end
      else
         begin
         rxd <=  rxdata;    
         rx_dv <=  1'b 1;   
         if (last_state == state_typ_s_src & count == 2 & iphy_err == 1'b 1)
            begin
            rx_er <=  1'b 1;    
            end
         else
            begin
            rx_er <=  1'b 0;    
            end
         end
      end
   end
always @(posedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      sop <= 1'b 0; 
      sop_int <= 1'b 0; 
      eop <= 1'b 0; 
      end
   else
      begin
      if (last_state == state_typ_s_idle & state != state_typ_s_idle)
         begin
         sop_int <= 1'b 1;  
         end
      else
         begin
         sop_int <= 1'b 0;  
         end
      if (last_state != state_typ_s_idle & state == state_typ_s_idle | 
    last_state != state_typ_s_ipg & state == state_typ_s_ipg)
         begin
         if (~(last_state == state_typ_s_ipg & state == state_typ_s_idle))
            begin
            eop <=  1'b 1;  
            end
         end
      else
         begin
         eop <=  1'b 0; 
         end
      sop <=  sop_int;  
      end
   end
always @(posedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      poscnt <= 0;  
      end
   else
      begin
      if (state == state_typ_s_sfd | state == state_typ_s_idle & start == 1'b 1)
         begin
         poscnt <= 0;   
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
always @(posedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      done <= 1'b 1;    
      end
   else
      begin
      if (state == state_typ_s_idle)
         begin
         done <= ~start;    
         end
      else
         begin
         done <= 1'b 0; 
         end
      end
   end
always @(posedge rx_clk or posedge reset)begin
   if (reset == 1'b 1)
      begin
      state <= state_typ_s_idle;    
      last_state <= state_typ_s_idle;   
      rxdata <= {8{1'b X}}; 
      count <= 0;   
      end
   else
      begin
      last_state <= state;  
      last_state_dly <= last_state; 
      if (count < 65535)
         begin
         process_7_cnttmp <= count + 1'b 1;  
         end
      else
         begin
         process_7_cnttmp <= count;  
         end
      case (state)
      state_typ_s_idle:
         begin
         if (start == 1'b 1)
            begin
            if (data_only == 1'b 1)
               begin
               if (ENABLE_SHIFT16 == 1'b0)         
               state <= state_typ_s_dst;    
               else
                state <= state_typ_s_Dword32Aligned; 
               process_7_cnttmp <= 1'b 0;    
               end
            else
               begin
               state <= state_typ_s_prmbl;  
               process_7_cnttmp <= 1'b 1;    
               end
            end
         rxdata <= {8{1'b X}};  
         end
      state_typ_s_prmbl:
         begin
         if (iprmble_len <= process_7_cnttmp)
            begin
            state <= state_typ_s_sfd;   
            end
         rxdata <= 8'h 55;  
         end
      state_typ_s_sfd:
         begin
         state <= state_typ_s_dst;  
         process_7_cnttmp <= 1'b 0;  
         if (iprmbl_err == 1'b 1)
            begin
            rxdata <= 8'h F5;   
            end
         else
            begin
            rxdata <= 8'h D5;   
            end
         end
     state_typ_s_Dword32Aligned:
        begin
        if (count == 1)
           begin
           state <= state_typ_s_dst;    
           process_7_cnttmp <= 1'b 0;    
           end
        case (count)
            1'b 0:
               begin
               rxdata[7:0] <= 8'h 00;    
               end
            1'b 1:
               begin
               rxdata[7:0] <= 8'h 00;   
               end
            default:
               ;
        endcase 
        end
      state_typ_s_dst:
         begin
         if (count == 5)
            begin
            state <= state_typ_s_src;   
            process_7_cnttmp <= 1'b 0;   
            end
         case (count)
         1'b 0:
            begin
            rxdata[7:0] <= idst[7:0];   
            end
         1'b 1:
            begin
            rxdata[7:0] <= idst[15:8];  
            end
         2'b 10:
            begin
            rxdata[7:0] <= idst[23:16]; 
            end
         2'b 11:
            begin
            rxdata[7:0] <= idst[31:24]; 
            end
         3'b 100:
            begin
            rxdata[7:0] <= idst[39:32]; 
            end
         3'b 101:
            begin
            rxdata[7:0] <= idst[47:40]; 
            end
         default:
            ;
         endcase
         end
      state_typ_s_src:
         begin
         if (count == 5)
            begin
            if (ipause_gen == 1'b 1)
               begin
               state <= state_typ_s_pause;  
               end
            else if (ivlan_en == 1'b 1 )
               begin
               state <= state_typ_s_tag;    
               end
            else
               begin
               state <= state_typ_s_len;    
               end
            process_7_cnttmp <= 1'b 0;   
            end
         case (count)
         1'b 0:
            begin
            rxdata[7:0] <= isrc[7:0];   
            end
         1'b 1:
            begin
            rxdata[7:0] <= isrc[15:8];  
            end
         2'b 10:
            begin
            rxdata[7:0] <= isrc[23:16]; 
            end
         2'b 11:
            begin
            rxdata[7:0] <= isrc[31:24]; 
            end
         3'b 100:
            begin
            rxdata[7:0] <= isrc[39:32]; 
            end
         3'b 101:
            begin
            rxdata[7:0] <= isrc[47:40]; 
            end
         default:
            ;
         endcase
         end
      state_typ_s_pause:
         begin
         if (count == 0)
            begin
            rxdata <= 8'h 88;   
            end
         else if (count == 1 )
            begin
            rxdata <= 8'h 08;   
            end
         else if (count == 2 )
            begin
            rxdata <= 8'h 00;   
            end
         else if (count == 3 )
            begin
            rxdata <= 8'h 01;   
            end
         else if (count == 4 )
            begin
            rxdata <= pquant[15:8]; 
            end
         else if (count == 5 )
            begin
            rxdata <= pquant[7:0];  
            if (ipad_en == 1'b 1)
               begin
               state <= state_typ_s_pad;    
               end
            else
               begin
               state <= state_typ_s_crc;    
               end
            process_7_cnttmp <= 1'b 0;   
            end
         end
      state_typ_s_tag:
         begin
         if (count == 0)
            begin
            rxdata <= 8'h 81;   
            end
         else if (count == 1 )
            begin
            rxdata <= 8'h 00;   
            end
         else if (count == 2 )
            begin
            rxdata <= ivlan_ctl[15:8];  
            end
         else if (count == 3 )
            begin
                if (istack_vlan==1'b0)
                begin
                        rxdata <= ivlan_ctl[7:0];   
                        state  <= state_typ_s_len;  
                        process_7_cnttmp <= 1'b 0;
                end
                else
                begin
                        rxdata <= ivlan_ctl[7:0];   
                        state  <= state_typ_s_stack;    
                        process_7_cnttmp <= 1'b 0;
                end 
            end
         end
      state_typ_s_stack:
         begin
         if (count == 0)
            begin
            rxdata <= 8'h 81;   
            end
         else if (count == 1 )
            begin
            rxdata <= 8'h 00;   
            end
         else if (count == 2 )
            begin
            rxdata <= ivlan_ctl[15:8];  
            end
         else if (count == 3 )
            begin
                rxdata <= ivlan_ctl[7:0];   
                state  <= state_typ_s_len;  
                process_7_cnttmp <= 1'b 0;
            end
         end
      state_typ_s_len:
         begin
         if (count == 0)
            begin
            if (ifrmtype != 0)
               begin
               rxdata <= ifrmtype[15:8];    
               end
            else
               begin
               rxdata <= ilen[15:8];    
               end
            end
         else if (count == 1 )
            begin
            if (ifrmtype != 0)
               begin
               rxdata <= ifrmtype[7:0]; 
               end
            else
               begin
               rxdata <= ilen[7:0]; 
               end
            if (ilen == 0)
               begin
               if (idata_only == 1'b 1 & iend_err == 1'b 1)
                  begin
                  state <= state_typ_s_enderr;  
                  end
               else if (idata_only == 1'b 1 )
                  begin
                  state <= state_typ_s_idle;    
                  end
               else if (ipad_en == 1'b 1 )
                  begin
                  state <= state_typ_s_pad; 
                  end
               else
                  begin
                  state <= state_typ_s_crc; 
                  end
               end
            else
               begin
               state <= state_typ_s_data;   
               end
            process_7_cnttmp <= 1'b 0;   
            end
         end
      state_typ_s_data:
         begin
         if (count == 0)
            begin
            rxdata <= icntstart;    
            datacnt <= icntstart;   
            end
         else if (count == 1 )
            begin
            rxdata <= icntstep; 
            end
         else
            begin
            rxdata <= datacnt;  
            datacnt <= (datacnt + icntstep) % 256;  
            end
         if (count >= ilen - 1'b 1)
            begin
            if (idata_only == 1'b 1)
               begin
               if (iend_err == 1'b 1)
                  begin
                  state <= state_typ_s_enderr;  
                  end
               else if (iipg_len != 0 )
                  begin
                  state <= state_typ_s_ipg; 
                  process_7_cnttmp <= 1'b 0; 
                  end
               else
                  begin
                  state <= state_typ_s_idle;    
                  end
               end
            else if (poscnt < 6'b 111100 - 1'b 1 & ipad_en ==  1'b 1 )
               begin
               state <= state_typ_s_pad;    
               end
            else
               begin
               state <= state_typ_s_crc;    
               process_7_cnttmp <= 1'b 0;    
               end
            if (ipayload_err == 1'b 1)
               begin
               rxdata <= rxdata;    
               end
            end
         end
      state_typ_s_pad:
         begin
         rxdata <= {8{1'b 0}};  
         if (poscnt >= 6'b 111100 - 1'b 1)
            begin
            state <= state_typ_s_crc;   
            process_7_cnttmp <= 1'b 0;   
            end
         end
      state_typ_s_crc:
         begin
         rxdata[V2V_process_7_i] <= crc32[process_7_hi - V2V_process_7_i] ^ 1'b 1;   
         if (count == 2 & icrc_err == 1'b 1)
            begin
            rxdata <= rxdata ^ 8'h FF;  
            end
         if (count == 3)
            begin
            if (iend_err == 1'b 1)
               begin
               state <= state_typ_s_enderr; 
               end
            else if (iipg_len > 0 )
               begin
               state <= state_typ_s_ipg;    
               process_7_cnttmp <= 1'b 1;    
               end
            else
               begin
               state <= state_typ_s_idle;   
               end
            end
         end
      state_typ_s_enderr:
         begin
         if (iipg_len == 0)
            begin
            state <= state_typ_s_idle;  
            end
         else
            begin
            state <= state_typ_s_ipg;   
            process_7_cnttmp <= 1'b 1;   
            end
         end
      state_typ_s_ipg:
         begin
         if (count >= iipg_len)
            begin
            state <= state_typ_s_idle;  
            end
         end
      endcase 
      count <= process_7_cnttmp;   
      end
   end
endmodule