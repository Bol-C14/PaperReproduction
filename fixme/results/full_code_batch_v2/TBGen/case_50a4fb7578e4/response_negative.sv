`timescale 1ns/1ps
module calibration_tb;
wire [3:0] key_en;
wire [3:0] ref_key_en;
wire [1:0] col_addr;
wire [1:0] ref_col_addr;
wire [1:0] chmod;
wire [1:0] ref_chmod;
wire [1:0] mode;
wire [1:0] ref_mode;
wire [1:0] data_type;
wire [1:0] ref_data_type;
wire col_wr_en;
wire ref_col_wr_en;
wire col_rd_en;
wire ref_col_rd_en;
wire [1:0] key_sel;
wire [1:0] ref_key_sel;
wire [3:0] iv_en;
wire [3:0] ref_iv_en;
wire [3:0] iv_sel;
wire [3:0] ref_iv_sel;
wire int_ccf;
wire ref_int_ccf;
wire int_err;
wire ref_int_err;
wire disable_core;
wire ref_disable_core;
wire first_block;
wire ref_first_block;
wire dma_req_wr;
wire ref_dma_req_wr;
wire dma_req_rd;
wire ref_dma_req_rd;
wire start_core;
wire ref_start_core;
wire [31:0] PRDATA;
wire [31:0] ref_PRDATA;
reg [3:0] PADDR;
reg [12:0] PWDATA;
reg PWRITE;
reg PENABLE;
reg PSEL;
reg PCLK;
reg PRESETn;
reg [31:0] key_bus;
reg [31:0] col_bus;
reg [31:0] iv_bus;
reg ccf_set;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
host_interface dut(.key_en(key_en), .col_addr(col_addr), .chmod(chmod), .mode(mode), .data_type(data_type), .col_wr_en(col_wr_en), .col_rd_en(col_rd_en), .key_sel(key_sel), .iv_en(iv_en), .iv_sel(iv_sel), .int_ccf(int_ccf), .int_err(int_err), .disable_core(disable_core), .first_block(first_block), .dma_req_wr(dma_req_wr), .dma_req_rd(dma_req_rd), .start_core(start_core), .PRDATA(PRDATA), .PADDR(PADDR), .PWDATA(PWDATA), .PWRITE(PWRITE), .PENABLE(PENABLE), .PSEL(PSEL), .PCLK(PCLK), .PRESETn(PRESETn), .key_bus(key_bus), .col_bus(col_bus), .iv_bus(iv_bus), .ccf_set(ccf_set));
oracle_host_interface golden(.key_en(ref_key_en), .col_addr(ref_col_addr), .chmod(ref_chmod), .mode(ref_mode), .data_type(ref_data_type), .col_wr_en(ref_col_wr_en), .col_rd_en(ref_col_rd_en), .key_sel(ref_key_sel), .iv_en(ref_iv_en), .iv_sel(ref_iv_sel), .int_ccf(ref_int_ccf), .int_err(ref_int_err), .disable_core(ref_disable_core), .first_block(ref_first_block), .dma_req_wr(ref_dma_req_wr), .dma_req_rd(ref_dma_req_rd), .start_core(ref_start_core), .PRDATA(ref_PRDATA), .PADDR(PADDR), .PWDATA(PWDATA), .PWRITE(PWRITE), .PENABLE(PENABLE), .PSEL(PSEL), .PCLK(PCLK), .PRESETn(PRESETn), .key_bus(key_bus), .col_bus(col_bus), .iv_bus(iv_bus), .ccf_set(ccf_set));
initial begin
PADDR = 0;
PWDATA = 0;
PWRITE = 0;
PENABLE = 0;
PSEL = 0;
PCLK = 0;
PRESETn = 0;
key_bus = 0;
col_bus = 0;
iv_bus = 0;
ccf_set = 0;
#2;

for(i=0;i<64;i=i+1) begin
PADDR = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
PWDATA = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
PWRITE = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
PENABLE = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
PSEL = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
PRESETn = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
key_bus = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
col_bus = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
iv_bus = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
ccf_set = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; PCLK=1; #2;
if ((^{ref_key_en,ref_col_addr,ref_chmod,ref_mode,ref_data_type,ref_col_wr_en,ref_col_rd_en,ref_key_sel,ref_iv_en,ref_iv_sel,ref_int_ccf,ref_int_err,ref_disable_core,ref_first_block,ref_dma_req_wr,ref_dma_req_rd,ref_start_core,ref_PRDATA}) === 1'bx || (^{key_en,col_addr,chmod,mode,data_type,col_wr_en,col_rd_en,key_sel,iv_en,iv_sel,int_ccf,int_err,disable_core,first_block,dma_req_wr,dma_req_rd,start_core,PRDATA}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({key_en,col_addr,chmod,mode,data_type,col_wr_en,col_rd_en,key_sel,iv_en,iv_sel,int_ccf,int_err,disable_core,first_block,dma_req_wr,dma_req_rd,start_core,PRDATA} !== ({ref_key_en,ref_col_addr,ref_chmod,ref_mode,ref_data_type,ref_col_wr_en,ref_col_rd_en,ref_key_sel,ref_iv_en,ref_iv_sel,ref_int_ccf,ref_int_err,ref_disable_core,ref_first_block,ref_dma_req_wr,ref_dma_req_rd,ref_start_core,ref_PRDATA} ^ 1'b1)) failures=failures+1; end
PCLK=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule