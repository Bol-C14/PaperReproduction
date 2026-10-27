`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_rst;
reg i_pipe_stb;
reg i_lock;
reg i_op;
reg [31:0] i_addr;
reg [31:0] i_data;
reg [4:0] i_oreg;
wire o_busy;
wire ref_o_busy;
wire o_pipe_stalled;
wire ref_o_pipe_stalled;
wire o_valid;
wire ref_o_valid;
wire o_err;
wire ref_o_err;
wire [4:0] o_wreg;
wire [4:0] ref_o_wreg;
wire [31:0] o_result;
wire [31:0] ref_o_result;
wire o_wb_cyc_gbl;
wire ref_o_wb_cyc_gbl;
wire o_wb_cyc_lcl;
wire ref_o_wb_cyc_lcl;
wire o_wb_stb_gbl;
wire ref_o_wb_stb_gbl;
wire o_wb_stb_lcl;
wire ref_o_wb_stb_lcl;
wire o_wb_we;
wire ref_o_wb_we;
wire [31:0] o_wb_addr;
wire [31:0] ref_o_wb_addr;
wire [31:0] o_wb_data;
wire [31:0] ref_o_wb_data;
reg i_wb_ack;
reg i_wb_stall;
reg i_wb_err;
reg [31:0] i_wb_data;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
pipemem dut(.i_clk(i_clk), .i_rst(i_rst), .i_pipe_stb(i_pipe_stb), .i_lock(i_lock), .i_op(i_op), .i_addr(i_addr), .i_data(i_data), .i_oreg(i_oreg), .o_busy(o_busy), .o_pipe_stalled(o_pipe_stalled), .o_valid(o_valid), .o_err(o_err), .o_wreg(o_wreg), .o_result(o_result), .o_wb_cyc_gbl(o_wb_cyc_gbl), .o_wb_cyc_lcl(o_wb_cyc_lcl), .o_wb_stb_gbl(o_wb_stb_gbl), .o_wb_stb_lcl(o_wb_stb_lcl), .o_wb_we(o_wb_we), .o_wb_addr(o_wb_addr), .o_wb_data(o_wb_data), .i_wb_ack(i_wb_ack), .i_wb_stall(i_wb_stall), .i_wb_err(i_wb_err), .i_wb_data(i_wb_data));
oracle_pipemem golden(.i_clk(i_clk), .i_rst(i_rst), .i_pipe_stb(i_pipe_stb), .i_lock(i_lock), .i_op(i_op), .i_addr(i_addr), .i_data(i_data), .i_oreg(i_oreg), .o_busy(ref_o_busy), .o_pipe_stalled(ref_o_pipe_stalled), .o_valid(ref_o_valid), .o_err(ref_o_err), .o_wreg(ref_o_wreg), .o_result(ref_o_result), .o_wb_cyc_gbl(ref_o_wb_cyc_gbl), .o_wb_cyc_lcl(ref_o_wb_cyc_lcl), .o_wb_stb_gbl(ref_o_wb_stb_gbl), .o_wb_stb_lcl(ref_o_wb_stb_lcl), .o_wb_we(ref_o_wb_we), .o_wb_addr(ref_o_wb_addr), .o_wb_data(ref_o_wb_data), .i_wb_ack(i_wb_ack), .i_wb_stall(i_wb_stall), .i_wb_err(i_wb_err), .i_wb_data(i_wb_data));
initial begin
i_clk = 0;
i_rst = 1;
i_pipe_stb = 0;
i_lock = 0;
i_op = 0;
i_addr = 0;
i_data = 0;
i_oreg = 0;
i_wb_ack = 0;
i_wb_stall = 0;
i_wb_err = 0;
i_wb_data = 0;
#2;
i_rst = 0;
for(i=0;i<64;i=i+1) begin
i_pipe_stb = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_lock = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_op = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_addr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_oreg = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_ack = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_stall = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_err = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_busy,ref_o_pipe_stalled,ref_o_valid,ref_o_err,ref_o_wreg,ref_o_result,ref_o_wb_cyc_gbl,ref_o_wb_cyc_lcl,ref_o_wb_stb_gbl,ref_o_wb_stb_lcl,ref_o_wb_we,ref_o_wb_addr,ref_o_wb_data}) === 1'bx || (^{o_busy,o_pipe_stalled,o_valid,o_err,o_wreg,o_result,o_wb_cyc_gbl,o_wb_cyc_lcl,o_wb_stb_gbl,o_wb_stb_lcl,o_wb_we,o_wb_addr,o_wb_data}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_busy,o_pipe_stalled,o_valid,o_err,o_wreg,o_result,o_wb_cyc_gbl,o_wb_cyc_lcl,o_wb_stb_gbl,o_wb_stb_lcl,o_wb_we,o_wb_addr,o_wb_data} !== {ref_o_busy,ref_o_pipe_stalled,ref_o_valid,ref_o_err,ref_o_wreg,ref_o_result,ref_o_wb_cyc_gbl,ref_o_wb_cyc_lcl,ref_o_wb_stb_gbl,ref_o_wb_stb_lcl,ref_o_wb_we,ref_o_wb_addr,ref_o_wb_data}) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule