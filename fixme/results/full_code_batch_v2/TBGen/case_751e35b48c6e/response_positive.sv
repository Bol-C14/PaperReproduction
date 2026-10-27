`timescale 1ns/1ps
module calibration_tb;
wire cpuoff;
wire ref_cpuoff;
wire gie;
wire ref_gie;
wire oscoff;
wire ref_oscoff;
wire [15:0] pc_sw;
wire [15:0] ref_pc_sw;
wire pc_sw_wr;
wire ref_pc_sw_wr;
wire [15:0] reg_dest;
wire [15:0] ref_reg_dest;
wire [15:0] reg_src;
wire [15:0] ref_reg_src;
wire scg1;
wire ref_scg1;
wire [3:0] status;
wire [3:0] ref_status;
reg [3:0] alu_stat;
reg [3:0] alu_stat_wr;
reg inst_bw;
reg [15:0] inst_dest;
reg [15:0] inst_src;
reg mclk;
reg [15:0] pc;
reg puc;
reg [15:0] reg_dest_val;
reg reg_dest_wr;
reg reg_pc_call;
reg [15:0] reg_sp_val;
reg reg_sp_wr;
reg reg_sr_wr;
reg reg_sr_clr;
reg reg_incr;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
omsp_register_file dut(.cpuoff(cpuoff), .gie(gie), .oscoff(oscoff), .pc_sw(pc_sw), .pc_sw_wr(pc_sw_wr), .reg_dest(reg_dest), .reg_src(reg_src), .scg1(scg1), .status(status), .alu_stat(alu_stat), .alu_stat_wr(alu_stat_wr), .inst_bw(inst_bw), .inst_dest(inst_dest), .inst_src(inst_src), .mclk(mclk), .pc(pc), .puc(puc), .reg_dest_val(reg_dest_val), .reg_dest_wr(reg_dest_wr), .reg_pc_call(reg_pc_call), .reg_sp_val(reg_sp_val), .reg_sp_wr(reg_sp_wr), .reg_sr_wr(reg_sr_wr), .reg_sr_clr(reg_sr_clr), .reg_incr(reg_incr));
oracle_omsp_register_file golden(.cpuoff(ref_cpuoff), .gie(ref_gie), .oscoff(ref_oscoff), .pc_sw(ref_pc_sw), .pc_sw_wr(ref_pc_sw_wr), .reg_dest(ref_reg_dest), .reg_src(ref_reg_src), .scg1(ref_scg1), .status(ref_status), .alu_stat(alu_stat), .alu_stat_wr(alu_stat_wr), .inst_bw(inst_bw), .inst_dest(inst_dest), .inst_src(inst_src), .mclk(mclk), .pc(pc), .puc(puc), .reg_dest_val(reg_dest_val), .reg_dest_wr(reg_dest_wr), .reg_pc_call(reg_pc_call), .reg_sp_val(reg_sp_val), .reg_sp_wr(reg_sp_wr), .reg_sr_wr(reg_sr_wr), .reg_sr_clr(reg_sr_clr), .reg_incr(reg_incr));
initial begin
alu_stat = 0;
alu_stat_wr = 0;
inst_bw = 0;
inst_dest = 0;
inst_src = 0;
mclk = 0;
pc = 0;
puc = 0;
reg_dest_val = 0;
reg_dest_wr = 0;
reg_pc_call = 0;
reg_sp_val = 0;
reg_sp_wr = 0;
reg_sr_wr = 0;
reg_sr_clr = 0;
reg_incr = 0;
#2;

for(i=0;i<64;i=i+1) begin
alu_stat = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
alu_stat_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inst_bw = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inst_dest = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inst_src = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
pc = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
puc = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_dest_val = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_dest_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_pc_call = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_sp_val = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_sp_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_sr_wr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_sr_clr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
reg_incr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; mclk=1; #2;
if ((^{ref_cpuoff,ref_gie,ref_oscoff,ref_pc_sw,ref_pc_sw_wr,ref_reg_dest,ref_reg_src,ref_scg1,ref_status}) === 1'bx || (^{cpuoff,gie,oscoff,pc_sw,pc_sw_wr,reg_dest,reg_src,scg1,status}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({cpuoff,gie,oscoff,pc_sw,pc_sw_wr,reg_dest,reg_src,scg1,status} !== {ref_cpuoff,ref_gie,ref_oscoff,ref_pc_sw,ref_pc_sw_wr,ref_reg_dest,ref_reg_src,ref_scg1,ref_status}) failures=failures+1; end
mclk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule