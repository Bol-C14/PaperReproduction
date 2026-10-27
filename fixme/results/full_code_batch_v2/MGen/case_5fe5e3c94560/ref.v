`timescale 1ns/1ps
 
module ref_fm_hsys (
    clk_core,
    rst_x,
    i_req,
    i_wr,
    i_adrs,
    ref_o_ack,
    i_be,
    i_wd,
    ref_o_rstr,
    ref_o_rd,
    ref_o_video_start,
    ref_o_aa_en,
    ref_o_fb0_offset,
    ref_o_fb1_offset,
    ref_o_color_mode,
    ref_o_front_buffer,
    ref_o_fb_blend_en,
    i_vint_x,
    i_vint_edge,
    i_vtx_int,
    ref_o_int
);
    input          clk_core;
    input          rst_x;
    input          i_req;
    input          i_wr;
    input  [3:0]   i_adrs;
    output         ref_o_ack;
    input  [3:0]   i_be;
    input  [31:0]  i_wd;
    output         ref_o_rstr;
    output [31:0]  ref_o_rd;
    output         ref_o_video_start;
    output [2:0]   ref_o_aa_en;
    output [6:0]   ref_o_fb0_offset;
    output [6:0]   ref_o_fb1_offset;
    output [1:0]   ref_o_color_mode;
    output         ref_o_front_buffer;
    output         ref_o_fb_blend_en;
    input          i_vint_x;
    input          i_vint_edge;
    input          i_vtx_int;
    output reg     ref_o_int;
    reg            r_video_start;
    reg    [2:0]   r_aa_en;
    reg    [6:0]   r_fb0_offset;
    reg    [6:0]   r_fb1_offset;
    reg    [1:0]   r_color_mode;
    reg            r_fb_blend_en;
    reg            r_rstr;
    reg    [31:0]  r_rd;
    reg            r_vint_x;
    reg    [2:0]   r_mask;
    reg            r_front_buffer;
    reg            r_vint_clear;
    wire           w_hit0;
    wire           w_hit1;
    wire           w_hit2;
    wire           w_hit3;
    wire           w_hit4;
    wire           w_hit5;
    wire           w_hit8;
    wire           w_hit9;
    wire           w_hitA;
    wire           w_hitB;
    wire           w_hitC;
    wire           w_hitD;
    wire           w_hitE;
    wire           w_hitF;
    wire           w_hit10;
    wire           w_hit11;
    wire           w_hit12;
    wire           w_hit13;
    wire           w_hit0_w;
    wire           w_hit1_w;
    wire           w_hit2_w;
    wire           w_hit3_w;
    wire           w_hit4_w;
    wire           w_hit5_w;
    wire           w_hit9_w;
    wire           w_hitA_w;
    wire           w_hitB_w;
    wire   [31:0]  w_rd;
    wire           w_rstr;
    wire           w_vint_x;
    wire           w_vint_on;
    wire   [2:0]   w_int;
assign w_hit0 = (i_adrs[3:0] == 4'h0);  
assign w_hit1 = (i_adrs[3:0] == 4'h1);  
assign w_hit2 = (i_adrs[3:0] == 4'h2);  
assign w_hit3 = (i_adrs[3:0] == 4'h3);  
assign w_hit4 = (i_adrs[3:0] == 4'h4);  
assign w_hit5 = (i_adrs[3:0] == 4'h5);  
assign w_hit8 = (i_adrs[3:0] == 4'h8);  
assign w_hit9 = (i_adrs[3:0] == 4'h9);  
assign w_hitA = (i_adrs[3:0] == 4'ha);  
assign w_hitB = (i_adrs[3:0] == 4'hb);  
assign w_hit0_w = w_hit0 & i_wr & i_req;
assign w_hit1_w = w_hit1 & i_wr & i_req;
assign w_hit2_w = w_hit2 & i_wr & i_req;
assign w_hit3_w = w_hit3 & i_wr & i_req;
assign w_hit4_w = w_hit4 & i_wr & i_req;
assign w_hit5_w = w_hit5 & i_wr & i_req;
assign w_hit9_w = w_hit9 & i_wr & i_req;
assign w_hitA_w = w_hitA & i_wr & i_req;
assign w_hitB_w = w_hitB & i_wr & i_req;
assign w_rstr = i_req & !i_wr;
assign w_rd = (w_hit0) ? {16'hbeef,5'b0,r_aa_en,7'b0,r_video_start} :
              (w_hit1) ? {6'b0,r_fb0_offset,19'b0} :
              (w_hit2) ? {6'b0,r_fb1_offset,19'b0} :
              (w_hit5) ? {30'b0,r_color_mode} :
              (w_hit8) ? {29'b0,i_vtx_int,!i_vint_x,!r_vint_x} :
              (w_hit9) ? {31'b0,r_vint_clear} :
              (w_hitA) ? {29'b0,r_mask} :
                         {31'b0,r_front_buffer};
assign w_vint_on = i_vint_edge;  
assign w_vint_x = ~r_vint_clear | i_vint_x;
assign w_int[0] = (r_mask[0]) ? 1'b0 : ~r_vint_x;
assign w_int[1] = 1'b0;
assign w_int[2] = (r_mask[2]) ? 1'b0 : i_vtx_int;
assign ref_o_rstr  = r_rstr;
assign ref_o_rd = r_rd;
assign ref_o_ack = i_req;
assign ref_o_video_start = r_video_start;
assign ref_o_aa_en = r_aa_en;
assign ref_o_fb0_offset = r_fb0_offset;
assign ref_o_fb1_offset = r_fb1_offset;
assign ref_o_color_mode = r_color_mode;
assign ref_o_front_buffer = r_front_buffer;
assign ref_o_fb_blend_en = r_fb_blend_en;
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_video_start <= 1'b0;
    end else begin
        if (w_hit0_w) begin
            if (i_be[0]) r_video_start   <= i_wd[0];
            if (i_be[1]) r_aa_en         <= i_wd[10:8];
            if (i_be[2]) r_fb_blend_en   <= i_wd[16];
        end
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_fb0_offset <= 7'b0;
    end else begin
        if (w_hit1_w) begin
            if (i_be[2]) r_fb0_offset[4:0] <= i_wd[23:19];
            if (i_be[3]) r_fb0_offset[6:5] <= i_wd[25:24];
        end
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_fb1_offset <= 7'b0;
    end else begin
        if (w_hit2_w) begin
            if (i_be[2]) r_fb1_offset[4:0] <= i_wd[23:19];
            if (i_be[3]) r_fb1_offset[6:5] <= i_wd[25:24];
        end
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_color_mode <= 2'b0;
    end else begin
        if (w_hit5_w) begin
            if (i_be[0]) r_color_mode   <= i_wd[1:0];
        end
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_vint_clear <= 1'b0;
    end else begin
        if (w_hit9_w) begin
            if (i_be[0]) r_vint_clear <= i_wd[0];
        end else if (w_vint_on) begin
            r_vint_clear <= 1'b1;
        end
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_mask <= 2'b11;
    end else begin
        if (w_hitA_w) begin
            if (i_be[0]) r_mask   <= i_wd[1:0];
        end
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_front_buffer <= 1'b0;
    end else begin
        if (w_hitB_w) begin
            if (i_be[0]) r_front_buffer   <= i_wd[0];
        end
    end
end
always @(posedge clk_core) begin
    r_rd <= w_rd;
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_rstr <= 1'b0;
    end else begin
        r_rstr <= w_rstr;
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        r_vint_x <= 1'b1;
    end else begin
        r_vint_x <= w_vint_x;
    end
end
always @(posedge clk_core or negedge rst_x) begin
    if (~rst_x) begin
        ref_o_int <= 1'b0;
    end else begin
        ref_o_int <= |w_int;
    end
end
endmodule

