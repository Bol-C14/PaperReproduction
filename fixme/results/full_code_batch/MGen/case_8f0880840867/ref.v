`timescale 1ns/1ps
 
module generic_fifo_ctrl_ref(
    wclk,
    wrst_n,
    wen,
    wfull_ref,
    walmost_full_ref,
    mem_wen_ref,
    mem_waddr_ref,
    rclk,
    rrst_n,
    ren,
    rempty_ref,
    ralmost_empty_ref,
    mem_ren_ref,
    mem_raddr_ref
);
parameter AWIDTH = 3;
parameter RAM_DEPTH = (1 << AWIDTH);
parameter EARLY_READ = 0;
parameter CLOCK_CROSSING = 1;
parameter ALMOST_EMPTY_THRESH = 1;
parameter ALMOST_FULL_THRESH = RAM_DEPTH-2;
input              wclk;
input              wrst_n;
input              wen;
output             wfull_ref;
output             walmost_full_ref;
output             mem_wen_ref;
output [AWIDTH:0]  mem_waddr_ref;
input              rclk;
input              rrst_n;
input              ren;
output             rempty_ref;
output             ralmost_empty_ref;
output             mem_ren_ref;
output [AWIDTH:0]  mem_raddr_ref;
reg  [AWIDTH:0]   wr_ptr;
reg  [AWIDTH:0]   rd_ptr;
reg  [AWIDTH:0]   next_rd_ptr;
wire [AWIDTH:0]   wr_gray;
reg  [AWIDTH:0]   wr_gray_reg;
reg  [AWIDTH:0]   wr_gray_meta;
reg  [AWIDTH:0]   wr_gray_sync;
reg  [AWIDTH:0]   wck_rd_ptr;
wire [AWIDTH:0]   wck_level;
wire [AWIDTH:0]   rd_gray;
reg  [AWIDTH:0]   rd_gray_reg;
reg  [AWIDTH:0]   rd_gray_meta;
reg  [AWIDTH:0]   rd_gray_sync;
reg  [AWIDTH:0]   rck_wr_ptr;
wire [AWIDTH:0]   rck_level;
wire [AWIDTH:0]   depth;
wire [AWIDTH:0]   empty_thresh;
wire [AWIDTH:0]   full_thresh;
integer         i;
assign depth = RAM_DEPTH[AWIDTH:0];
assign empty_thresh = ALMOST_EMPTY_THRESH[AWIDTH:0];
assign full_thresh = ALMOST_FULL_THRESH[AWIDTH:0];
assign wfull_ref = (wck_level == depth);
assign walmost_full_ref = (wck_level >= (depth - full_thresh));
assign rempty_ref = (rck_level == 0);
assign ralmost_empty_ref = (rck_level <= empty_thresh);
always @(posedge wclk or negedge wrst_n)
begin
    if (!wrst_n) begin
        wr_ptr <= {(AWIDTH+1){1'b0}};
    end
    else if (wen && !wfull_ref) begin
        wr_ptr <= wr_ptr + {{(AWIDTH){1'b0}}, 1'b1};
    end
end
always @(ren, rd_ptr, rck_wr_ptr)
begin
    next_rd_ptr = rd_ptr;
    if (ren && rd_ptr != rck_wr_ptr) begin
        next_rd_ptr = rd_ptr + {{(AWIDTH){1'b0}}, 1'b1};
    end
end
always @(posedge rclk or negedge rrst_n)
begin
    if (!rrst_n) begin
        rd_ptr <= {(AWIDTH+1){1'b0}};
    end
    else begin
        rd_ptr <= next_rd_ptr;
    end
end
assign wr_gray = wr_ptr ^ (wr_ptr >> 1);
assign rd_gray = rd_ptr ^ (rd_ptr >> 1);
always @(wr_gray_sync)
begin
    rck_wr_ptr[AWIDTH] = wr_gray_sync[AWIDTH];
    for (i = 0; i < AWIDTH; i = i + 1) begin
        rck_wr_ptr[AWIDTH-i-1] = rck_wr_ptr[AWIDTH-i] ^ wr_gray_sync[AWIDTH-i-1];
    end
end
always @(rd_gray_sync)
begin
    wck_rd_ptr[AWIDTH] = rd_gray_sync[AWIDTH];
    for (i = 0; i < AWIDTH; i = i + 1) begin
        wck_rd_ptr[AWIDTH-i-1] = wck_rd_ptr[AWIDTH-i] ^ rd_gray_sync[AWIDTH-i-1];
    end
end
generate
    if (CLOCK_CROSSING) begin
        always @(posedge rclk or negedge rrst_n)
        begin
            if (!rrst_n) begin
                rd_gray_reg <= {(AWIDTH+1){1'b0}};
                wr_gray_meta <= {(AWIDTH+1){1'b0}};
                wr_gray_sync <= {(AWIDTH+1){1'b0}};
            end
            else begin
                rd_gray_reg <= rd_gray;
                wr_gray_meta <= wr_gray_reg;
                wr_gray_sync <= wr_gray_meta;
            end
        end
        always @(posedge wclk or negedge wrst_n)
        begin
            if (!wrst_n) begin
                wr_gray_reg <= {(AWIDTH+1){1'b0}};
                rd_gray_meta <= {(AWIDTH+1){1'b0}};
                rd_gray_sync <= {(AWIDTH+1){1'b0}};
            end
            else begin
                wr_gray_reg <= wr_gray;
                rd_gray_meta <= rd_gray_reg;
                rd_gray_sync <= rd_gray_meta;
            end
        end
    end
    else begin
        always @(wr_gray or rd_gray)
        begin
            wr_gray_sync = wr_gray;
            rd_gray_sync = rd_gray;
        end
    end
endgenerate
assign wck_level = wr_ptr - wck_rd_ptr;
assign rck_level = rck_wr_ptr - rd_ptr;
assign  mem_waddr_ref = wr_ptr;
assign  mem_wen_ref = wen && !wfull_ref;
generate
    if (EARLY_READ) begin
        assign mem_raddr_ref = next_rd_ptr;
        assign mem_ren_ref = 1'b1;
    end
    else begin
        assign mem_raddr_ref = rd_ptr;
        assign mem_ren_ref = ren;
    end
endgenerate
endmodule

