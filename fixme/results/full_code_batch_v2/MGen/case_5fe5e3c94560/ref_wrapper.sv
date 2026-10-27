`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned clk_core,
    input longint unsigned rst_x,
    input longint unsigned i_req,
    input longint unsigned i_wr,
    input longint unsigned i_adrs,
    output longint unsigned ref_o_ack__dpi,
    input longint unsigned i_be,
    input longint unsigned i_wd,
    output longint unsigned ref_o_rstr__dpi,
    output longint unsigned ref_o_rd__dpi,
    output longint unsigned ref_o_video_start__dpi,
    output longint unsigned ref_o_aa_en__dpi,
    output longint unsigned ref_o_fb0_offset__dpi,
    output longint unsigned ref_o_fb1_offset__dpi,
    output longint unsigned ref_o_color_mode__dpi,
    output longint unsigned ref_o_front_buffer__dpi,
    output longint unsigned ref_o_fb_blend_en__dpi,
    input longint unsigned i_vint_x,
    input longint unsigned i_vint_edge,
    input longint unsigned i_vtx_int,
    output longint unsigned ref_o_int__dpi
);

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
input clk_core;
input rst_x;
input i_req;
input i_wr;
input [3:0] i_adrs;
output reg ref_o_ack;
input [3:0] i_be;
input [31:0] i_wd;
output reg ref_o_rstr;
output reg [31:0] ref_o_rd;
output reg ref_o_video_start;
output reg [2:0] ref_o_aa_en;
output reg [6:0] ref_o_fb0_offset;
output reg [6:0] ref_o_fb1_offset;
output reg [1:0] ref_o_color_mode;
output reg ref_o_front_buffer;
output reg ref_o_fb_blend_en;
input i_vint_x;
input i_vint_edge;
input i_vtx_int;
output reg ref_o_int;
longint unsigned ref_o_ack__dpi;
longint unsigned ref_o_rstr__dpi;
longint unsigned ref_o_rd__dpi;
longint unsigned ref_o_video_start__dpi;
longint unsigned ref_o_aa_en__dpi;
longint unsigned ref_o_fb0_offset__dpi;
longint unsigned ref_o_fb1_offset__dpi;
longint unsigned ref_o_color_mode__dpi;
longint unsigned ref_o_front_buffer__dpi;
longint unsigned ref_o_fb_blend_en__dpi;
longint unsigned ref_o_int__dpi;

always @(*) begin
    ref_model_eval(clk_core, rst_x, i_req, i_wr, i_adrs, ref_o_ack__dpi, i_be, i_wd, ref_o_rstr__dpi, ref_o_rd__dpi, ref_o_video_start__dpi, ref_o_aa_en__dpi, ref_o_fb0_offset__dpi, ref_o_fb1_offset__dpi, ref_o_color_mode__dpi, ref_o_front_buffer__dpi, ref_o_fb_blend_en__dpi, i_vint_x, i_vint_edge, i_vtx_int, ref_o_int__dpi);
    ref_o_ack = ref_o_ack__dpi[0];
    ref_o_rstr = ref_o_rstr__dpi[0];
    ref_o_rd = ref_o_rd__dpi[31:0];
    ref_o_video_start = ref_o_video_start__dpi[0];
    ref_o_aa_en = ref_o_aa_en__dpi[2:0];
    ref_o_fb0_offset = ref_o_fb0_offset__dpi[6:0];
    ref_o_fb1_offset = ref_o_fb1_offset__dpi[6:0];
    ref_o_color_mode = ref_o_color_mode__dpi[1:0];
    ref_o_front_buffer = ref_o_front_buffer__dpi[0];
    ref_o_fb_blend_en = ref_o_fb_blend_en__dpi[0];
    ref_o_int = ref_o_int__dpi[0];
end
endmodule
