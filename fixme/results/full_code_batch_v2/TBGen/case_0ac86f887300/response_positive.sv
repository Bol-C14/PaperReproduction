`timescale 1ns/1ps
module calibration_tb;
reg Clk;
reg Reset;
reg Reg_apply_0;
reg [4:0] Reg_addr_0;
reg [15:0] Reg_data_0;
wire Reg_next_0;
wire ref_Reg_next_0;
reg Reg_apply_1;
reg [4:0] Reg_addr_1;
reg [15:0] Reg_data_1;
wire Reg_next_1;
wire ref_Reg_next_1;
wire [5:0] Addra;
wire [5:0] ref_Addra;
wire [31:0] Dina;
wire [31:0] ref_Dina;
reg [31:0] Douta;
wire Wea;
wire ref_Wea;
reg [5:0] CPU_rd_addr;
reg CPU_rd_apply;
wire CPU_rd_grant;
wire ref_CPU_rd_grant;
wire [31:0] CPU_rd_dout;
wire [31:0] ref_CPU_rd_dout;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
RMON_CTRL dut(.Clk(Clk), .Reset(Reset), .Reg_apply_0(Reg_apply_0), .Reg_addr_0(Reg_addr_0), .Reg_data_0(Reg_data_0), .Reg_next_0(Reg_next_0), .Reg_apply_1(Reg_apply_1), .Reg_addr_1(Reg_addr_1), .Reg_data_1(Reg_data_1), .Reg_next_1(Reg_next_1), .Addra(Addra), .Dina(Dina), .Douta(Douta), .Wea(Wea), .CPU_rd_addr(CPU_rd_addr), .CPU_rd_apply(CPU_rd_apply), .CPU_rd_grant(CPU_rd_grant), .CPU_rd_dout(CPU_rd_dout));
oracle_RMON_CTRL golden(.Clk(Clk), .Reset(Reset), .Reg_apply_0(Reg_apply_0), .Reg_addr_0(Reg_addr_0), .Reg_data_0(Reg_data_0), .Reg_next_0(ref_Reg_next_0), .Reg_apply_1(Reg_apply_1), .Reg_addr_1(Reg_addr_1), .Reg_data_1(Reg_data_1), .Reg_next_1(ref_Reg_next_1), .Addra(ref_Addra), .Dina(ref_Dina), .Douta(Douta), .Wea(ref_Wea), .CPU_rd_addr(CPU_rd_addr), .CPU_rd_apply(CPU_rd_apply), .CPU_rd_grant(ref_CPU_rd_grant), .CPU_rd_dout(ref_CPU_rd_dout));
initial begin
Clk = 0;
Reset = 1;
Reg_apply_0 = 0;
Reg_addr_0 = 0;
Reg_data_0 = 0;
Reg_apply_1 = 0;
Reg_addr_1 = 0;
Reg_data_1 = 0;
Douta = 0;
CPU_rd_addr = 0;
CPU_rd_apply = 0;
#2;
Reset = 0;
for(i=0;i<64;i=i+1) begin
Reg_apply_0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Reg_addr_0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Reg_data_0 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Reg_apply_1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Reg_addr_1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Reg_data_1 = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
Douta = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
CPU_rd_addr = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
CPU_rd_apply = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; Clk=1; #2;
if ((^{ref_Reg_next_0,ref_Reg_next_1,ref_Addra,ref_Dina,ref_Wea,ref_CPU_rd_grant,ref_CPU_rd_dout}) === 1'bx || (^{Reg_next_0,Reg_next_1,Addra,Dina,Wea,CPU_rd_grant,CPU_rd_dout}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({Reg_next_0,Reg_next_1,Addra,Dina,Wea,CPU_rd_grant,CPU_rd_dout} !== {ref_Reg_next_0,ref_Reg_next_1,ref_Addra,ref_Dina,ref_Wea,ref_CPU_rd_grant,ref_CPU_rd_dout}) failures=failures+1; end
Clk=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule