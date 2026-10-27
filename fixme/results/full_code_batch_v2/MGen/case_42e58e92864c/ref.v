`timescale 1ns/1ps
 module a23_wishbone_ref
(
input                       i_clk,
input                       i_select,
input       [31:0]          i_write_data,
input                       i_write_enable,
input       [3:0]           i_byte_enable,    
input                       i_data_access,
input                       i_exclusive,      
input       [31:0]          i_address,
output                      o_stall_ref,
input                       i_cache_req,
output reg  [31:0]          o_wb_adr_ref = 'd0,
output reg  [3:0]           o_wb_sel_ref = 'd0,
output reg                  o_wb_we_ref  = 'd0,
input       [31:0]          i_wb_dat,
output reg  [31:0]          o_wb_dat_ref = 'd0,
output reg                  o_wb_cyc_ref = 'd0,
output reg                  o_wb_stb_ref = 'd0,
input                       i_wb_ack,
input                       i_wb_err
);
localparam [3:0] WB_IDLE            = 3'd0,
                 WB_BURST1          = 3'd1,
                 WB_BURST2          = 3'd2,
                 WB_BURST3          = 3'd3,
                 WB_WAIT_ACK        = 3'd4;
reg     [2:0]               wishbone_st = WB_IDLE;
wire                        core_read_request;
wire                        core_write_request;
wire                        cache_read_request;
wire                        cache_write_request;
wire                        start_access;
reg                         servicing_cache = 'd0;
wire    [3:0]               byte_enable;
reg                         exclusive_access = 'd0;
wire                        read_ack;
wire                        wait_write_ack;
wire                        wb_wait;
reg     [31:0]              wbuf_addr_r = 'd0;
reg     [3:0]               wbuf_sel_r  = 'd0;
reg                         wbuf_busy_r = 'd0;
assign read_ack             = i_wb_ack && !i_wb_err && !o_wb_we;
assign o_stall_ref              = ( core_read_request  && !read_ack )       || 
                              ( core_read_request  && servicing_cache ) ||
                              ( core_write_request && servicing_cache ) ||
                              ( core_write_request && wishbone_st == WB_WAIT_ACK) ||
                              ( cache_write_request && wishbone_st == WB_WAIT_ACK) ||
                              wbuf_busy_r;
assign core_read_request    = i_select && !i_write_enable;
assign core_write_request   = i_select &&  i_write_enable;
assign cache_read_request   = i_cache_req && !i_write_enable;
assign cache_write_request  = i_cache_req &&  i_write_enable;
assign wb_wait = (wishbone_st != WB_IDLE) || wbuf_busy_r;
assign start_access = (wishbone_st == WB_IDLE) && (core_read_request || core_write_request || cache_read_request || cache_write_request);
assign byte_enable          = wbuf_busy_r                                   ? wbuf_sel_r    :
                              ( core_write_request || cache_write_request ) ? i_byte_enable : 
                                                                              4'hf          ;
always @( posedge i_clk )
    if ( wb_wait && !wbuf_busy_r && (core_write_request || cache_write_request) )
        begin
        wbuf_addr_r <= i_address;
        wbuf_sel_r  <= i_byte_enable;
        wbuf_busy_r <= 1'd1;
        end
    else if (!o_wb_stb_ref)
        wbuf_busy_r <= 1'd0;
always @( posedge i_clk )
    if ( start_access )
        o_wb_dat_ref <= i_write_data;
assign wait_write_ack = wbuf_busy_r || (wishbone_st == WB_WAIT_ACK && !i_wb_ack);
always @( posedge i_clk )
    case ( wishbone_st )
        WB_IDLE :
            begin 
            if ( start_access )
                begin
                o_wb_stb_ref            <= 1'd1; 
                o_wb_cyc_ref            <= 1'd1; 
                o_wb_sel_ref            <= byte_enable;
                end
            else if ( !wait_write_ack )
                begin
                o_wb_stb_ref            <= 1'd0;
                o_wb_cyc_ref            <= exclusive_access;
                end
            servicing_cache <= cache_read_request && !wait_write_ack;
            if ( wait_write_ack )
                begin
                wishbone_st      <= WB_WAIT_ACK;
                end  
            else if ( cache_read_request )
                begin
                wishbone_st         <= WB_BURST1;
                exclusive_access    <= 1'd0;
                end                    
            else if ( core_read_request )
                begin
                wishbone_st         <= WB_WAIT_ACK;
                exclusive_access    <= i_exclusive;
                end                    
            else if ( core_write_request )
                exclusive_access <= i_exclusive;
            if ( start_access )
                begin
                if (wbuf_busy_r)
                    begin
                    o_wb_we_ref              <= 1'd1;
                    o_wb_adr_ref[31:2]       <= wbuf_addr_r[31:2];
                    end
                else
                    begin
                    o_wb_we_ref              <= core_write_request || cache_write_request;
                    o_wb_adr_ref[31:2]       <= i_address[31:2];
                    end
                o_wb_adr_ref[1:0]        <= byte_enable == 4'b0001 ? 2'd0 :
                                        byte_enable == 4'b0010 ? 2'd1 :
                                        byte_enable == 4'b0100 ? 2'd2 :
                                        byte_enable == 4'b1000 ? 2'd3 :
                                        byte_enable == 4'b0011 ? 2'd0 :
                                        byte_enable == 4'b1100 ? 2'd2 :
                                                                 2'd0 ;
                end
            end
        WB_BURST1:  
            if ( i_wb_ack )
                begin
                o_wb_adr_ref[3:2]   <= o_wb_adr_ref[3:2] + 1'd1;
                wishbone_st     <= WB_BURST2;
                end
        WB_BURST2:  
            if ( i_wb_ack )
                begin
                o_wb_adr_ref[3:2]   <= o_wb_adr_ref[3:2] + 1'd1;
                wishbone_st     <= WB_BURST3;
                end
        WB_BURST3:  
            if ( i_wb_ack )
                begin
                o_wb_adr_ref[3:2]   <= o_wb_adr_ref[3:2] + 1'd1;
                wishbone_st     <= WB_WAIT_ACK;
                end
        WB_WAIT_ACK:   
            if ( i_wb_ack )
                begin
                wishbone_st         <= WB_IDLE;
                o_wb_stb_ref            <= 1'd0; 
                o_wb_cyc_ref            <= exclusive_access; 
                o_wb_we_ref             <= 1'd0;
                servicing_cache     <= 1'd0;
                end
    endcase
wire    [(14*8)-1:0]   xAS_STATE;
assign xAS_STATE  = wishbone_st == WB_IDLE       ? "WB_IDLE"       :
                    wishbone_st == WB_BURST1     ? "WB_BURST1"     :
                    wishbone_st == WB_BURST2     ? "WB_BURST2"     :
                    wishbone_st == WB_BURST3     ? "WB_BURST3"     :
                    wishbone_st == WB_WAIT_ACK   ? "WB_WAIT_ACK"   :
                                                      "UNKNOWN"       ;
endmodule

