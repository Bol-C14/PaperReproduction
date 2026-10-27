`timescale 1ns/1ps
module calibration_tb;
reg i_clk;
reg i_select;
reg [31:0] i_write_data;
reg i_write_enable;
reg [3:0] i_byte_enable;
reg i_data_access;
reg i_exclusive;
reg [31:0] i_address;
wire o_stall;
wire ref_o_stall;
reg i_cache_req;
wire [31:0] o_wb_adr;
wire [31:0] ref_o_wb_adr;
wire [3:0] o_wb_sel;
wire [3:0] ref_o_wb_sel;
wire o_wb_we;
wire ref_o_wb_we;
reg [31:0] i_wb_dat;
wire [31:0] o_wb_dat;
wire [31:0] ref_o_wb_dat;
wire o_wb_cyc;
wire ref_o_wb_cyc;
wire o_wb_stb;
wire ref_o_wb_stb;
reg i_wb_ack;
reg i_wb_err;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
a23_wishbone dut(.i_clk(i_clk), .i_select(i_select), .i_write_data(i_write_data), .i_write_enable(i_write_enable), .i_byte_enable(i_byte_enable), .i_data_access(i_data_access), .i_exclusive(i_exclusive), .i_address(i_address), .o_stall(o_stall), .i_cache_req(i_cache_req), .o_wb_adr(o_wb_adr), .o_wb_sel(o_wb_sel), .o_wb_we(o_wb_we), .i_wb_dat(i_wb_dat), .o_wb_dat(o_wb_dat), .o_wb_cyc(o_wb_cyc), .o_wb_stb(o_wb_stb), .i_wb_ack(i_wb_ack), .i_wb_err(i_wb_err));
oracle_a23_wishbone golden(.i_clk(i_clk), .i_select(i_select), .i_write_data(i_write_data), .i_write_enable(i_write_enable), .i_byte_enable(i_byte_enable), .i_data_access(i_data_access), .i_exclusive(i_exclusive), .i_address(i_address), .o_stall(ref_o_stall), .i_cache_req(i_cache_req), .o_wb_adr(ref_o_wb_adr), .o_wb_sel(ref_o_wb_sel), .o_wb_we(ref_o_wb_we), .i_wb_dat(i_wb_dat), .o_wb_dat(ref_o_wb_dat), .o_wb_cyc(ref_o_wb_cyc), .o_wb_stb(ref_o_wb_stb), .i_wb_ack(i_wb_ack), .i_wb_err(i_wb_err));
initial begin
i_clk = 0;
i_select = 0;
i_write_data = 0;
i_write_enable = 0;
i_byte_enable = 0;
i_data_access = 0;
i_exclusive = 0;
i_address = 0;
i_cache_req = 0;
i_wb_dat = 0;
i_wb_ack = 0;
i_wb_err = 0;
#2;

for(i=0;i<64;i=i+1) begin
i_select = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_write_data = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_write_enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_byte_enable = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_data_access = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_exclusive = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_address = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_cache_req = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_dat = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_ack = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
i_wb_err = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; i_clk=1; #2;
if ((^{ref_o_stall,ref_o_wb_adr,ref_o_wb_sel,ref_o_wb_we,ref_o_wb_dat,ref_o_wb_cyc,ref_o_wb_stb}) === 1'bx || (^{o_stall,o_wb_adr,o_wb_sel,o_wb_we,o_wb_dat,o_wb_cyc,o_wb_stb}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({o_stall,o_wb_adr,o_wb_sel,o_wb_we,o_wb_dat,o_wb_cyc,o_wb_stb} !== ({ref_o_stall,ref_o_wb_adr,ref_o_wb_sel,ref_o_wb_we,ref_o_wb_dat,ref_o_wb_cyc,ref_o_wb_stb} ^ 1'b1)) failures=failures+1; end
i_clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule