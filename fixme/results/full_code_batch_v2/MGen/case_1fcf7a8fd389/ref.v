`timescale 1ns/1ps
 
module ref_cavlc_read_levels (
    clk,
    rst_n,
    ena,
    t1s_sel,
    prefix_sel,
    suffix_sel,
    calc_sel,
    TrailingOnes,
    TotalCoeff,
    rbsp,
    i,
    ref_level_0,
    ref_level_1,
    ref_level_2,
    ref_level_3,
    ref_level_4,
    ref_level_5,
    ref_level_6,
    ref_level_7,
    ref_level_8,
    ref_level_9,
    ref_level_10,
    ref_level_11,
    ref_level_12,
    ref_level_13,
    ref_level_14,
    ref_level_15,
    ref_len_comb
);
input   clk;
input   rst_n;
input   ena;
input   t1s_sel;
input   prefix_sel;
input   suffix_sel;
input   calc_sel;
input   [1:0]   TrailingOnes;
input   [4:0]   TotalCoeff;
input   [0:15]  rbsp;
input   [3:0]   i;
output  [8:0]   ref_level_0;
output  [8:0]   ref_level_1;
output  [8:0]   ref_level_2;
output  [8:0]   ref_level_3;
output  [8:0]   ref_level_4;
output  [8:0]   ref_level_5;
output  [8:0]   ref_level_6;
output  [8:0]   ref_level_7;
output  [8:0]   ref_level_8;
output  [8:0]   ref_level_9;
output  [8:0]   ref_level_10;
output  [8:0]   ref_level_11;
output  [8:0]   ref_level_12;
output  [8:0]   ref_level_13;
output  [8:0]   ref_level_14;
output  [8:0]   ref_level_15;
output  [4:0]   ref_len_comb;
reg     [0:15]  rbsp_internal;        
reg     [3:0]   level_prefix_comb;
reg     [8:0]   level_suffix;
reg     [4:0]   ref_len_comb;
reg     [3:0]   level_prefix;
reg     [2:0]   suffixLength;   
reg     [8:0]   level;
reg     [8:0]   level_abs;
reg     [8:0]   level_code_tmp;
reg     [8:0]   ref_level_0, ref_level_1, ref_level_2, ref_level_3, ref_level_4, ref_level_5, ref_level_6, ref_level_7;
reg     [8:0]   ref_level_8, ref_level_9, ref_level_10, ref_level_11, ref_level_12, ref_level_13, ref_level_14, ref_level_15;
always @(*)
if ((t1s_sel || prefix_sel || suffix_sel)&& ena)
    rbsp_internal <= rbsp;
else
    rbsp_internal <= 'hffff;
always @(*)
if (rbsp_internal[0])         level_prefix_comb <= 0;
else if (rbsp_internal[1])    level_prefix_comb <= 1;
else if (rbsp_internal[2])    level_prefix_comb <= 2;
else if (rbsp_internal[3])    level_prefix_comb <= 3;
else if (rbsp_internal[4])    level_prefix_comb <= 4;
else if (rbsp_internal[5])    level_prefix_comb <= 5;
else if (rbsp_internal[6])    level_prefix_comb <= 6;
else if (rbsp_internal[7])    level_prefix_comb <= 7;
else if (rbsp_internal[8])    level_prefix_comb <= 8;
else if (rbsp_internal[9])    level_prefix_comb <= 9;
else if (rbsp_internal[10])   level_prefix_comb <= 10;
else if (rbsp_internal[11])   level_prefix_comb <= 11;
else if (rbsp_internal[12])   level_prefix_comb <= 12; 
else if (rbsp_internal[13])   level_prefix_comb <= 13; 
else if (rbsp_internal[14])   level_prefix_comb <= 14;
else if (rbsp_internal[15])   level_prefix_comb <= 15;
else                          level_prefix_comb <= 'bx;
always @(posedge clk or negedge rst_n)
if (!rst_n)
    level_prefix <= 0;
else if (prefix_sel && ena)
    level_prefix <= level_prefix_comb;
wire first_level;
assign first_level = (i == TotalCoeff - TrailingOnes - 1);
always @(posedge clk or negedge rst_n)
if (!rst_n)
    suffixLength <= 0;
else if (prefix_sel && ena) begin
    if (TotalCoeff > 10 && TrailingOnes < 3 && first_level )  
        suffixLength <= 1;
    else if (first_level)
        suffixLength <= 0;
    else if (suffixLength == 0 && level_abs > 2'd3)
        suffixLength <= 2;
    else if (suffixLength == 0)
        suffixLength <= 1;
    else if (  level_abs > (2'd3 << (suffixLength - 1'b1) ) && suffixLength < 6)
        suffixLength <= suffixLength + 1'b1;
end
always @(*)
if (suffixLength > 0 && level_prefix <= 14) 
    level_suffix <= {3'b0, rbsp_internal[0:5] >> (3'd6 - suffixLength)};
else if (level_prefix == 14)   
    level_suffix <= {3'b0, rbsp_internal[0:3] };
else if (level_prefix == 15) 
    level_suffix <= rbsp_internal[3:11];     
else 
    level_suffix <= 0;      
always @(posedge clk or negedge rst_n)
if (!rst_n) begin
    level_code_tmp <=  0;
end
else if (suffix_sel && ena) begin
    level_code_tmp <= (level_prefix << suffixLength) + level_suffix + 
    ((suffixLength == 0 && level_prefix == 15) ? 4'd15 : 0);
end
wire    [2:0]   tmp1;
assign tmp1 = (first_level && TrailingOnes < 3)? 2'd2 : 2'd0;
always @(*)
begin
    if (level_code_tmp % 2 == 0) begin
        level <= ( level_code_tmp + tmp1 + 2 ) >> 1;
    end
    else begin
        level <= (-level_code_tmp - tmp1 - 1 ) >> 1;
    end
end
wire level_abs_refresh;
assign level_abs_refresh = calc_sel && ena;
always @(posedge clk or negedge rst_n)
if (!rst_n) begin
    level_abs <= 0;
end
else if (level_abs_refresh) begin
    level_abs <= level[8] ? -level : level;
end
always @ (posedge clk or negedge rst_n)
if (!rst_n) begin
    ref_level_0 <= 0;   ref_level_1 <= 0;   ref_level_2 <= 0;   ref_level_3 <= 0;
    ref_level_4 <= 0;   ref_level_5 <= 0;   ref_level_6 <= 0;   ref_level_7 <= 0;
    ref_level_8 <= 0;   ref_level_9 <= 0;   ref_level_10<= 0;   ref_level_11<= 0;
    ref_level_12<= 0;   ref_level_13<= 0;   ref_level_14<= 0;   ref_level_15<= 0;
end
else if (t1s_sel && ena)
    case (i)
    0 : ref_level_0 <= rbsp_internal[0]? -1 : 1;
    1 : begin
            ref_level_1 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_0 <= rbsp_internal[1]? -1 : 1;
        end
    2 : begin
            ref_level_2 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_1 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_0 <= rbsp_internal[2]? -1 : 1;
        end         
    3 : begin
            ref_level_3 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_2 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_1 <= rbsp_internal[2]? -1 : 1;
        end 
    4 : begin
            ref_level_4 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_3 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_2 <= rbsp_internal[2]? -1 : 1;
        end 
    5 : begin
            ref_level_5 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_4 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_3 <= rbsp_internal[2]? -1 : 1;
        end 
    6 : begin
            ref_level_6 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_5 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_4 <= rbsp_internal[2]? -1 : 1;
        end 
    7 : begin
            ref_level_7 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_6 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_5 <= rbsp_internal[2]? -1 : 1;
        end 
    8 : begin
            ref_level_8 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_7 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_6 <= rbsp_internal[2]? -1 : 1;
        end 
    9 : begin
            ref_level_9 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_8 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_7 <= rbsp_internal[2]? -1 : 1;
        end 
    10: begin
            ref_level_10 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_9 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_8 <= rbsp_internal[2]? -1 : 1;
        end 
    11: begin
            ref_level_11 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_10 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_9 <= rbsp_internal[2]? -1 : 1;
        end 
    12: begin
            ref_level_12 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_11 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_10 <= rbsp_internal[2]? -1 : 1;
        end 
    13: begin
            ref_level_13 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_12 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_11 <= rbsp_internal[2]? -1 : 1;
        end 
    14: begin
            ref_level_14 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_13 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_12 <= rbsp_internal[2]? -1 : 1;
        end 
    15: begin
            ref_level_15 <= rbsp_internal[0]? -1 : 1;
            if (TrailingOnes[1])
                ref_level_14 <= rbsp_internal[1]? -1 : 1;
            if (TrailingOnes == 3)
                ref_level_13 <= rbsp_internal[2]? -1 : 1;
        end 
endcase
else if (calc_sel && ena)
case (i)
    0 :ref_level_0 <= level;
    1 :ref_level_1 <= level;
    2 :ref_level_2 <= level;
    3 :ref_level_3 <= level;
    4 :ref_level_4 <= level;
    5 :ref_level_5 <= level;
    6 :ref_level_6 <= level;
    7 :ref_level_7 <= level;
    8 :ref_level_8 <= level;
    9 :ref_level_9 <= level;
    10:ref_level_10<= level;
    11:ref_level_11<= level;
    12:ref_level_12<= level;
    13:ref_level_13<= level;
    14:ref_level_14<= level;
    15:ref_level_15<= level;
endcase
always @(*)
if(t1s_sel)
    ref_len_comb <= TrailingOnes;
else if(prefix_sel)
    ref_len_comb <= level_prefix_comb + 1;
else if(suffix_sel && suffixLength > 0 && level_prefix <= 14)
    ref_len_comb <= suffixLength;  
else if(suffix_sel && level_prefix == 14)
    ref_len_comb <= 4;
else if(suffix_sel && level_prefix == 15)
    ref_len_comb <= 12;
else
    ref_len_comb <= 0;        
endmodule

