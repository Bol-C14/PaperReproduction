`timescale 1ns/1ps
module MUX32_ref(
    data1_i    ,
    data2_i    ,
    select_i   ,
    data_o     
);

input [31:0] data1_i,data2_i;
input select_i;
output[31:0] data_o;

assign data_o = (select_i)? data2_i : data1_i ;

endmodule


module PC_ref
(
    clk_i,
    start_i,
    pc_i,
    hazardpc_i,
    pc_o,
);

// Ports
input               clk_i;
input               start_i, hazardpc_i;
input   [31:0]      pc_i;
output  [31:0]      pc_o;

// Wires & Registers_ref
reg     [31:0]      pc_o;
reg     flag,flag_next;

always@(*)begin
    if(pc_i == 32'd248)flag_next = 1;
    else flag_next = flag;
end

always@(posedge clk_i or negedge start_i) begin
    if(~start_i) begin
        pc_o <= 32'b0;
        flag <= 0;
    end
    else begin
        flag <= flag_next;
        if(start_i & (!hazardpc_i))
            pc_o <= (flag)? 32'd248 : pc_i ;
        else
            pc_o <= pc_o;
    end
end

endmodule
module Instruction_Memory_ref
(
    clk,
    reset,
    addr_i, 
    instr_i,
    instr_o
);
integer i;
// Interface
input               clk;
input               reset;
input   [31:0]      addr_i;
input   [7:0]       instr_i;
output  [31:0]      instr_o;

// Instruction memory
reg     [31:0]     memory  [0:63];
reg     [1:0]      quad,quad_d1;
reg     [7:0]      instr_read;
reg     [5:0]      address_read;
reg                flag,flag_next;
reg     [1:0]      counter,counter_next;
reg     [5:0]      instr_wr_address,instr_wr_address_next;

assign  instr_o = memory[addr_i>>2];  

always@(*)begin
    if(instr_i == 8'b1111_1110)flag_next = 1;
    else if (instr_i == 8'b1111_1111)flag_next = 0;
    else flag_next = flag;

    if(flag)counter_next = counter + 2'd1;
    else counter_next = counter;

    if(counter == 2'b11)instr_wr_address_next = instr_wr_address + 6'd1;
    else instr_wr_address_next = instr_wr_address;
end

always@(posedge clk or posedge reset)begin
    if(reset)begin
        for(i=0;i<63;i=i+1)begin
            memory[i] <= 0;
        end
        counter         <= 0;
        quad            <= 0;
        instr_read      <= 0;
        flag            <= 0;
        address_read    <= 0;
        instr_wr_address<=0;
    end
    else begin
        flag             <= flag_next;
        counter          <= counter_next;
        quad             <= (2'b11-counter);
        quad_d1          <= quad;
        instr_wr_address <= instr_wr_address_next;
        address_read     <= instr_wr_address;
        instr_read       <= instr_i;
        
        
        if(flag)begin
            case(quad)
            2'b00: memory[address_read][7:0]   <= (instr_read == 8'b1111_1111)?0:instr_read;
            2'b01: memory[address_read][15:8]  <= (instr_read == 8'b1111_1111)?0:instr_read;
            2'b10: memory[address_read][23:16] <= (instr_read == 8'b1111_1111)?0:instr_read;
            2'b11: memory[address_read][31:24] <= (instr_read == 8'b1111_1111)?0:instr_read;
            default: memory[address_read][7:0] <= (instr_read == 8'b1111_1111)?0:instr_read;
            endcase
        end
    end
end
endmodule

module ALU_ref (data1_i, data2_i, ALUCtrl_i, data_o,Zero_o);

input [31:0] data1_i, data2_i;
input [2:0] ALUCtrl_i;
output reg[31:0] data_o;
output reg Zero_o;

parameter SUM = 3'b001;
parameter SUB = 3'b010;
parameter AND = 3'b011;
parameter OR  = 3'b100;
parameter XOR = 3'b101;
parameter MUL = 3'b110;


/* implement here */
always@(*)begin
Zero_o   = (data1_i - data2_i)?0:1;
case(ALUCtrl_i)

  SUM : begin
    data_o = data1_i + data2_i;
  end
  SUB : begin
    data_o = data1_i - data2_i;
  end
  AND : begin
    data_o = data1_i & data2_i;
  end
  OR : begin
    data_o = data1_i | data2_i;
  end
  XOR : begin
    data_o = data1_i ^ data2_i;
  end
  MUL : begin
    data_o = data1_i * data2_i;
  end
  default : begin
    data_o = data1_i;
  end

endcase

end

endmodule

module Adder_ref
(
    data1_in,
    data2_in,
    data_o
);

input [31:0] data1_in,data2_in;
output [31:0] data_o;

assign data_o = data1_in + data2_in ;

endmodule

module IF_ID_ref(
	clk_i,
	start_i,
	pc_i,
	inst_i,
	hazard_i,
	flush_i,
	pcIm_i,
	pcIm_o,
	pc_o,
	inst_o,
);

input	clk_i, hazard_i, flush_i, start_i;
input	[31:0]	inst_i, pc_i;
input 	[11:0]	pcIm_i;
output 	[11:0]	pcIm_o;
output	[31:0]	pc_o, inst_o;

reg [31:0]	pc_o, inst_o;
reg [11:0] 	pcIm_o;

always@(posedge clk_i) begin
	if(~start_i) begin
		pc_o <= 32'b0;
		inst_o <= 32'b0;
		pcIm_o <= 12'b0;
	end
	else if(flush_i) begin
		pc_o <= pc_i;
		inst_o <= 32'b0;
		pcIm_o <= 12'b0;
	end
	else if(hazard_i) begin
		pc_o <= pc_i;
		inst_o <= inst_o;
		pcIm_o <= pcIm_i;
	end
	else begin
		pc_o <= pc_i;
		inst_o <= inst_i;
		pcIm_o <= pcIm_i;
	end
end

endmodule

module Shift1_ref (
  input [31:0] data_i,
  output [31:0] data_o
);

assign data_o = {data_i[30:0],1'b0};

endmodule


module Sign_Extend_ref(
    select_i,
    data0_i,
    data1_i,
    data_o     
);
input [11:0] data0_i,data1_i;
input select_i;
output[31:0] data_o;

assign data_o = (select_i)? {{20{data1_i[11]}},data1_i} : {{20{data0_i[11]}},data0_i} ; 

endmodule

module ALU_Control_ref(
    funct_i    ,
    ALUOp_i    ,
    ALUCtrl_o 
);

input [9:0] funct_i;//funct7[9:3]+funct3[2:0]
input [1:0] ALUOp_i;//00 for addi
output reg[2:0] ALUCtrl_o;

always@(*)begin

  case(ALUOp_i)

    2'b11 : begin
        ALUCtrl_o = 3'b001;//add
    end

    2'b10 : begin
        case(funct_i)

            10'b0000000000 : begin
                ALUCtrl_o = 3'b001;//add
            end
            10'b0100000000 : begin
                ALUCtrl_o = 3'b010;//sub
            end
            10'b0000001000 : begin
                ALUCtrl_o = 3'b110;//MUL
            end
            10'b0000000110 : begin
                ALUCtrl_o = 3'b100;//OR
            end
            10'b0000000111 : begin
                ALUCtrl_o = 3'b011;//AND
            end
            default : begin
                ALUCtrl_o = 3'b001;
            end
        endcase
    end

    2'b01 : begin //beq,ALU_ref do subtraction
    ALUCtrl_o = 3'b010;//sub
    end
    default : begin
        ALUCtrl_o = 3'b001;
    end
endcase

end

endmodule


module VALU_ref (v1_i, v2_i, VALUCtrl_i, v_o,over);

    input signed[31:0] v1_i, v2_i; 
    input [2:0] VALUCtrl_i; //VALU_ref instruction
    output reg [31:0] v_o; //output vector
    output reg [3:0]  over;//signed bit
    //output reg VZero_o; //branching signal

    reg signed[7:0] e1, e2, e3, e4;
    reg signed[7:0] b1,b2,b3,b4,b5,b6,b7,b8;
    wire [15:0]  a1,a2,a3,a4,a5,a6,a7,a8;
    reg signed[15:0]   s1,s2,s3,s4;
    //sign extension
    assign a1 = {{8{v1_i[7]}} ,v1_i[7:0]};
    assign a2 = {{8{v2_i[7]}} ,v2_i[7:0]};
    assign a3 = {{8{v1_i[15]}},v1_i[15:8]};
    assign a4 = {{8{v2_i[15]}},v2_i[15:8]};
    assign a5 = {{8{v1_i[23]}},v1_i[23:16]};
    assign a6 = {{8{v2_i[23]}},v2_i[23:16]};
    assign a7 = {{8{v1_i[31]}},v1_i[31:24]};
    assign a8 = {{8{v2_i[31]}},v2_i[31:24]};

    

    parameter VSUM  = 3'b010; //vector addition
    parameter VSUB  = 3'b110; //vector subtraction
    parameter VDP   = 3'b001; //dot product
    //parameter VSM   = 3'b000; //scalar multiplication
    //parameter VADDI = 3'b011; //vector addi
    //parameter VXP  = 3'b100; //cross product
    
    always @(*) begin
        
        //VZero_o = (v1_i - v2_i) ? 0 : 1;
        over[0] = 0;
        over[1] = 0;
        over[2] = 0;
        over[3] = 0;
        b1 = v1_i[7:0];
        b2 = v2_i[7:0];
        b3 = v1_i[15:8];
        b4 = v2_i[15:8];
        b5 = v1_i[23:16];
        b6 = v2_i[23:16];
        b7 = v1_i[31:24];
        b8 = v2_i[31:24];
        case (VALUCtrl_i)
            VSUM: begin
                
                e1 = b1 + b2;
                e2 = b3 + b4;
                e3 = b5 + b6;
                e4 = b7 + b8;
                v_o = {e4,e3,e2,e1};
                
                if( ~v1_i[7]  & ~v2_i[7] )over[0] = 1;
                else over[0] = 0;
                if( ~v1_i[15] & ~v2_i[15] )over[1] = 1;
                else over[1] = 0;
                if( ~v1_i[23] & ~v2_i[23] )over[2] = 1;
                else over[2] = 0;
                if( ~v1_i[31] & ~v2_i[31] )over[3] = 1;
                else over[3] = 0;
                
            end
            
            VSUB: begin

                e1 = b1 - b2;
                e2 = b3 - b4;
                e3 = b5 - b6;
                e4 = b7 - b8;
                v_o = {e4,e3,e2,e1};


                if( ~v1_i[7]  & (v2_i[7]) )over[0] = 1;
                else over[0] = 0;
                if( ~v1_i[15] & (v2_i[15]) )over[1] = 1;
                else over[1] = 0;
                if( ~v1_i[23] & (v2_i[23]) )over[2] = 1;
                else over[2] = 0;
                if( ~v1_i[31] & (v2_i[31]) )over[3] = 1;
                else over[3] = 0;

            end

            VDP: begin
                
                s1  = a1 * a2 ;
                s2  = a3 * a4 ;
                s3  = a5 * a6 ;
                s4  = a7 * a8 ;//16bits
             
                v_o = (s1+s2+s3+s4);

            end

            default: begin
                
                over[0] = 0;
                over[1] = 0;
                over[2] = 0;
                over[3] = 0;
                v_o = v1_i;
                
            end
            
        endcase
        
    end
    
endmodule

module VALU_ctrl_ref(vfunct_i, VALUCtrl_o);

    input [9:0] vfunct_i; //{funct6, vm, funct3}
    //input [1:0] VALUOp_i;
    output reg [2:0] VALUCtrl_o;

    always @(*) begin
        case (vfunct_i)
            10'b000000_1_001: begin
                VALUCtrl_o = 3'b010; //vector addition
            end 
            10'b010000_1_000: begin
                VALUCtrl_o = 3'b110; //vector subtraction
            end
            10'b000000_1_111: begin
                VALUCtrl_o = 3'b000; //scalar multiplication
            end
            10'b000000_1_110: begin
                VALUCtrl_o = 3'b001; //dot product
            end
            default: begin
                VALUCtrl_o = 3'b000;
            end
        endcase
    end
endmodule


module Control_ref(
    Op_i       ,
    ALUOp_o    ,
    ALUSrc_o   ,
    RegWrite_o ,
    MemRd_o,
    MemWr_o,
    MemToReg_o,
    immSelect_o
);

//ports

input [6:0]     Op_i;
output reg[1:0]     ALUOp_o;
output  reg      ALUSrc_o,immSelect_o;
output  reg    RegWrite_o ,MemRd_o,MemWr_o,MemToReg_o;




always@(*)begin

  case(Op_i)

  7'b0010011 : begin //addi
  ALUOp_o = 2'b11;
  ALUSrc_o = 1'b1;
  RegWrite_o = 1'b1;
  MemRd_o = 1'b0;
  MemWr_o = 1'b0;
  MemToReg_o = 1'b0;
  immSelect_o = 1'b0;
  end
  
  7'b0110011 : begin //others
  ALUOp_o = 2'b10;
  ALUSrc_o = 1'b0;
  RegWrite_o = 1'b1;
  MemRd_o = 1'b0;
  MemWr_o = 1'b0;
  MemToReg_o = 1'b0;
  immSelect_o = 1'b0;
  end

  7'b1100011 : begin //beq
  ALUOp_o = 2'b01;
  ALUSrc_o = 1'b1;
  RegWrite_o = 1'b0;
  MemRd_o = 1'b0;
  MemWr_o = 1'b0;
  MemToReg_o = 1'b0;
  immSelect_o = 1'b0;
  end

  7'b0000011 : begin //lw
  ALUOp_o = 2'b00;
  ALUSrc_o = 1'b1;
  MemRd_o = 1'b1;
  MemToReg_o = 1'b1;
  RegWrite_o = 1'b1;
  MemWr_o = 1'b0;
  immSelect_o = 1'b0;
  end

  7'b0100011 : begin //sw
  ALUOp_o = 2'b00;
  ALUSrc_o = 1'b1;
  MemWr_o = 1'b1;
  RegWrite_o = 1'b0;
  MemRd_o = 1'b0;
  MemToReg_o = 1'b0;
  immSelect_o = 1'b1;
  end

  //---------NEW-----------
  7'b1010111: begin //vector
  ALUOp_o = 2'b00; //useless
  ALUSrc_o = 1'b0;
  RegWrite_o = 1'b1;
  MemRd_o = 1'b0;
  MemWr_o = 1'b0;
  MemToReg_o = 1'b0;
  immSelect_o = 1'b0;
  end
  //---------NEW-----------

  default : begin
  ALUOp_o = 2'b11;
  ALUSrc_o = 1'b1;
  RegWrite_o = 1'b0;
  MemRd_o = 1'b0;
  MemWr_o = 1'b0;
  MemToReg_o = 1'b0;
  immSelect_o = 1'b0;
  end
  endcase
end
endmodule

module Registers_ref
(
    clk_i,
    reset,
    op_address,
    RSaddr_i,
    RTaddr_i,
    RDaddr_i, 
    RDdata_i,
    RegWrite_i,
    is_pos_i, 
    RSdata_o, 
    RTdata_o,
    reg_o,
    pos_o
);
integer i;
// Ports
input               clk_i;
input               reset;
input   [4:0]       op_address;
input   [4:0]       RSaddr_i;
input   [4:0]       RTaddr_i;
input   [4:0]       RDaddr_i;
input   [31:0]      RDdata_i;
input               RegWrite_i;
input   [3:0]       is_pos_i;
output  [31:0]      RSdata_o; 
output  [31:0]      RTdata_o;
output  [31:0]       reg_o;
output  [3:0]       pos_o;
// Register File
reg     [31:0]      register        [0:31];
reg     [3:0]       pos             [0:31];
// Read Data      
assign  RSdata_o = register[RSaddr_i];
assign  RTdata_o = register[RTaddr_i];
assign  reg_o    = register[op_address];
assign  pos_o    = pos[op_address];
// Write Data

always@(negedge clk_i or posedge reset)begin
    if(reset) begin
        for(i=0;i<32;i=i+1)register[i] <= 0;
        for(i=0;i<32;i=i+1)pos[i]      <= 0;
    end  

    else  begin
        if(RegWrite_i)begin
            register[RDaddr_i] <= RDdata_i;
            pos[RDaddr_i]      <= is_pos_i;
        end
    end      
end
   
endmodule 


module ID_EX_ref(
	clk_i,
	start_i,
	inst_i,
	pc_i,
	pcEx_i,
	RDData0_i,
	RDData1_i,
	SignExtended_i,
	RegDst_i,
	ALUOp_i,
	ALUSrc_i,
	RegWrite_i,
	MemToReg_i,
	MemRead_i,
	MemWrite_i,
	inst_o,
	PC_branch_select_i,
	RSaddr_i,     
    RTaddr_i,
	pc_o,
	pcEx_o,
	RDData0_o,
	RDData1_o,
	SignExtended_o,
	RegDst_o,
	ALUOp_o,
	ALUSrc_o,
	RegWrite_o,
	MemToReg_o,
	MemRead_o,
	MemWrite_o,
	PC_branch_select_o,
	RSaddr_o,
	RTaddr_o
);

input	clk_i, ALUSrc_i, RegWrite_i, MemToReg_i, MemRead_i, MemWrite_i, start_i; 
input	[31:0]	inst_i, pc_i, RDData0_i, RDData1_i, SignExtended_i;
input	[1:0]	ALUOp_i;
input 	[4:0]	RegDst_i,RSaddr_i,RTaddr_i;
input  [31:0] pcEx_i;
input PC_branch_select_i;
output	ALUSrc_o, RegWrite_o, MemToReg_o, MemRead_o, MemWrite_o;  
output	[31:0]	inst_o, pc_o, RDData0_o, RDData1_o, SignExtended_o;
output	[1:0]	ALUOp_o;
output 	[4:0]	RegDst_o,RSaddr_o,RTaddr_o;
output  [31:0] pcEx_o;
output reg PC_branch_select_o;
reg	ALUSrc_o, RegWrite_o, MemToReg_o, MemRead_o, MemWrite_o;  
reg	[31:0]	inst_o, pc_o, RDData0_o, RDData1_o, SignExtended_o,pcEx_o;
reg	[1:0]	ALUOp_o;
reg [4:0]	RegDst_o,RSaddr_o,RTaddr_o;

always@(posedge clk_i or negedge start_i) begin
	if(~start_i) begin
		inst_o <= 0;
		pc_o <= 0 ;
		RDData0_o <= 0;
		RDData1_o <= 0;
		SignExtended_o <= 0;
		RegDst_o <= 0;
		ALUOp_o <= 0;
		ALUSrc_o <= 0;
		RegWrite_o <= 0;
		MemToReg_o <= 0;
		MemRead_o <= 0;
		MemWrite_o <= 0;
		pcEx_o <= 0;
		PC_branch_select_o <=0;
		RSaddr_o <= 0;
		RTaddr_o <= 0;
	end
	else begin
		inst_o <= inst_i;
		pc_o <= pc_i ;
		RDData0_o <= RDData0_i;
		RDData1_o <= RDData1_i;
		SignExtended_o <= SignExtended_i;
		RegDst_o <= RegDst_i;
		ALUOp_o <= ALUOp_i;
		ALUSrc_o <= ALUSrc_i;
		RegWrite_o <= RegWrite_i;
		MemToReg_o <= MemToReg_i;
		MemRead_o <= MemRead_i;
		MemWrite_o <= MemWrite_i;
		pcEx_o <= pcEx_i;
		PC_branch_select_o <= PC_branch_select_i;
		RSaddr_o <= RSaddr_i;
		RTaddr_o <= RTaddr_i;
	end
end

endmodule

module HazradDetect_ref(
    IF_IDrs1_i,
    IF_IDrs2_i,
    ID_EXrd_i,
    ID_EX_MemRead_i,
    Hazard_o,
);

input ID_EX_MemRead_i;
input [4:0] IF_IDrs1_i, IF_IDrs2_i, ID_EXrd_i;
output Hazard_o;

assign Hazard_o = ((ID_EX_MemRead_i && (ID_EXrd_i == IF_IDrs1_i || ID_EXrd_i == IF_IDrs2_i))? 1'b1 : 1'b0);

endmodule

module ForwardingUnit_ref
(   
    EX_MEM_RegWrite_i,
    EX_MEM_RD_i,
    ID_EX_RS_i,
    ID_EX_RT_i,
    MEM_WB_RegWrite_i,
    MEM_WB_RD_i,
    ForwardA_o,
    ForwardB_o
);

input			    EX_MEM_RegWrite_i, MEM_WB_RegWrite_i;
input	    [4:0]	ID_EX_RS_i, ID_EX_RT_i, EX_MEM_RD_i, MEM_WB_RD_i;
output reg	[1:0]	ForwardA_o, ForwardB_o;

always@(*)begin
    ForwardA_o = 2'b00;

    if(EX_MEM_RegWrite_i && 
    (EX_MEM_RD_i != 5'b00000) && 
    (EX_MEM_RD_i == ID_EX_RS_i)) ForwardA_o = 2'b10;

    else if(MEM_WB_RegWrite_i &&
    (MEM_WB_RD_i != 5'b00000) &&
    MEM_WB_RD_i == ID_EX_RS_i)  ForwardA_o = 2'b01;

    ForwardB_o = 2'b00;

    if(EX_MEM_RegWrite_i && 
    (EX_MEM_RD_i != 5'b00000) && 
    (EX_MEM_RD_i == ID_EX_RT_i)) ForwardB_o = 2'b10;

    else if(MEM_WB_RegWrite_i &&
    (MEM_WB_RD_i != 5'b00000) &&
    MEM_WB_RD_i == ID_EX_RT_i)  ForwardB_o = 2'b01;

end
endmodule

module ForwardingMUX_ref(
    select_i,
    data_i,
    EX_MEM_i,
    MEM_WB_i,
    data_o
);

input	[1:0]		select_i;
input	[31:0]		data_i, EX_MEM_i, MEM_WB_i;
output reg[31:0]	data_o;


always @(*) begin
	case(select_i)
        2'b00: data_o = data_i;

        2'b01: data_o = MEM_WB_i;

		2'b10: data_o = EX_MEM_i;	

        default : data_o = data_i;
	endcase
end

endmodule

module EX_MEM_ref(
	clk_i,
	start_i,
	pc_i,
	zero_i,
	ALUResult_i,
    VALUResult_i, //NEW
	RDData_i,
	RDaddr_i,
	RegWrite_i,
	MemToReg_i,
	MemRead_i,
	MemWrite_i,
	instr_i,
	instr_o,
	pc_o,
	zero_o,
	ALUResult_o,
    VALUResult_o, //NEW
	RDData_o,
	RDaddr_o,
	RegWrite_o,
	MemToReg_o,
	MemRead_o,
	MemWrite_o,
);

input	clk_i, zero_i, RegWrite_i, MemToReg_i, MemRead_i, MemWrite_i, start_i;
input	[31:0]	pc_i, ALUResult_i, RDData_i, VALUResult_i; //NEW
input	[4:0] RDaddr_i;
input 	[31:0] instr_i;
output reg [31:0] instr_o;
output	zero_o, RegWrite_o, MemToReg_o, MemRead_o, MemWrite_o;
output	[31:0]	pc_o, ALUResult_o, RDData_o, VALUResult_o; //NEW
output reg[4:0] RDaddr_o;
reg	 zero_o, RegWrite_o, MemToReg_o, MemRead_o, MemWrite_o;
reg	[31:0]	pc_o, ALUResult_o, RDData_o, VALUResult_o;//NEW

always@(posedge clk_i or negedge start_i) begin
	if(~start_i) begin
		pc_o <= 0;
		zero_o <= 0;
		ALUResult_o <= 0;
        VALUResult_o <= 0; //NEW
		RDData_o <= 0;
		RDaddr_o <= 0;
		RegWrite_o <= 0;
		MemToReg_o <= 0;
		MemRead_o <= 0;
		MemWrite_o <= 0;
		instr_o	<= 0;
	end
	else begin
		pc_o <= pc_i;
		zero_o <= zero_i;
		ALUResult_o <= ALUResult_i;
        VALUResult_o <= VALUResult_i; //NEW
		RDData_o <= RDData_i;
		RDaddr_o <= RDaddr_i;
		RegWrite_o <= RegWrite_i;
		MemToReg_o <= MemToReg_i;
		MemRead_o <= MemRead_i;
		MemWrite_o <= MemWrite_i;
		instr_o    <= instr_i;
	end
end

endmodule

module Data_Memory_ref
(   
    clk_i,
    reset,
    op_addr,
    addr_i,
    data_i,
    MemWrite_i,
    MemRead_i,
    data_o,
    data_mem_o
);


input clk_i;
input reset;
input [4:0] op_addr;
input [31:0] addr_i,data_i;
input MemWrite_i, MemRead_i;
integer i;
output [31:0] data_o;
output [31:0] data_mem_o;

reg [7:0] memory [0:31];
wire [31:0] op;

assign op = { memory[addr_i + 3],memory[addr_i + 2],
memory[addr_i + 1],memory[addr_i]};

assign data_mem_o = { memory[op_addr + 3],memory[op_addr + 2],
memory[op_addr + 1],memory[op_addr]};

assign data_o = (MemRead_i) ? op : 32'b0;

always @(posedge clk_i or posedge reset) begin

    if(reset)for(i=0;i<32;i=i+1)memory[i] <= 0;
     else if(MemWrite_i) begin
            memory[addr_i + 3] <= data_i[31:24];
            memory[addr_i + 2] <= data_i[23:16];
            memory[addr_i + 1] <= data_i[15:8];
            memory[addr_i]     <= data_i[7:0];
        end
end

endmodule

module MEM_WB_ref(
	clk_i,
	start_i,
	ALUResult_i,
	RDData_i,
	RDaddr_i,
	RegWrite_i,
	MemToReg_i,
	DataMemReadData_i,
	ALUResult_o,
	RDData_o,
	RDaddr_o,
	RegWrite_o,
	MemToReg_o,
	DataMemReadData_o
);

input	clk_i, RegWrite_i, MemToReg_i, start_i;
input	[31:0]	ALUResult_i, RDData_i, DataMemReadData_i;
input	[4:0]	RDaddr_i;

output	 RegWrite_o, MemToReg_o;
output	[31:0]	ALUResult_o, RDData_o, DataMemReadData_o;

reg	 RegWrite_o, MemToReg_o;
reg	[31:0]	ALUResult_o, RDData_o, DataMemReadData_o;
output reg	[4:0]	RDaddr_o;

always@(posedge clk_i or negedge start_i) begin
	if(~start_i) begin
		ALUResult_o <= 0;
		RDData_o <= 0;
		RDaddr_o <= 0;
		RegWrite_o <= 0;
		MemToReg_o <= 0;
		DataMemReadData_o<=0;
	end
	else begin
		ALUResult_o <= ALUResult_i;
		RDData_o <= RDData_i;
		RDaddr_o <= RDaddr_i;
		RegWrite_o <= RegWrite_i;
		MemToReg_o <= MemToReg_i;
		DataMemReadData_o <= DataMemReadData_i;
	end
end

endmodule


module MUX_Control_ref(
    Hazard_i, 
    RegDst_i,  
    ALUOp_i, 
    ALUSrc_i,  
    RegWrite_i, 
    MemToReg_i, 
    MemRead_i,
    MemWrite_i,
    RegDst_o,  
    ALUOp_o, 
    ALUSrc_o,  
    RegWrite_o, 
    MemToReg_o, 
    MemRead_o,
    MemWrite_o,  
);

input	[1:0]	ALUOp_i;
input 	[4:0]	RegDst_i;
input	Hazard_i, ALUSrc_i, RegWrite_i, MemToReg_i, MemRead_i, MemWrite_i; 

output	reg [1:0]	ALUOp_o;
output 	reg [4:0]	RegDst_o;
output	reg ALUSrc_o, RegWrite_o, MemToReg_o, MemRead_o, MemWrite_o; 

always@(*)begin
    case(Hazard_i)
    1'b1 : begin
    RegDst_o <= 4'b0000;  
    ALUOp_o <= 2'b00;
    ALUSrc_o <= 1'b0; 
    RegWrite_o <= 1'b0;
    MemToReg_o <= 1'b0;
    MemRead_o <= 1'b0;
    MemWrite_o <= 1'b0;
    end

    1'b0 : begin
    RegDst_o <= RegDst_i;  
    ALUOp_o <= ALUOp_i;
    ALUSrc_o <= ALUSrc_i; 
    RegWrite_o <= RegWrite_i;
    MemToReg_o <= MemToReg_i;
    MemRead_o <= MemRead_i;
    MemWrite_o <= MemWrite_i;
    end

    default : begin
    RegDst_o <= RegDst_i;  
    ALUOp_o <= ALUOp_i;
    ALUSrc_o <= ALUSrc_i; 
    RegWrite_o <= RegWrite_i;
    MemToReg_o <= MemToReg_i;
    MemRead_o <= MemRead_i;
    MemWrite_o <= MemWrite_i;
    end

    endcase

end
endmodule

module CPU_ref
(
    clk_i, 
    DataOrReg,
    address,
    instr_i,
    reset,
    vout_addr,
    value_o_ref,
    is_positive_ref,
    easter_egg_ref
);

//------------------------- I/O Ports -------------------------------//

input               clk_i           ;
input               DataOrReg       ;
input [4:0]         address         ;
input [7:0]         instr_i         ;
input               reset           ;
input [1:0]         vout_addr       ; //00:ouput 8,i.e. [7:0] LSB ; 01: [15:8]
output reg [7:0]    value_o_ref     ;
output  			is_positive_ref ;
output  reg[2:0]  	easter_egg_ref  ;

//------------------------- Wire&Reg -------------------------------//

wire [3:0] vector_signed_bits;
wire [31:0] op_selection;
wire [31:0] inst_addr,inst,addPC,aluData,RSD,RTD,signExData,MUXop;
wire [9:0] ALUfunct_in;
wire [2:0] alu_ctrl_wire;
wire [11:0] pcIm,swIm;
wire isBranch;
wire rst;
wire [31:0] AddSum_data_o;
wire [31:0] pcSelect_data_o;
wire        HazradDetect_Hazard_o;
wire [31:0] IF_ID_pc_o;
wire [31:0] shiftLeft_data_o;
wire [11:0] IF_ID_pcIm_o;
wire [31:0] IF_ID_inst_o;
wire [4:0]  MEM_WB_RDaddr_o;
wire [31:0] memToReg_data_o;
wire        MEM_WB_RegWrite_o;
wire        Control_immSelect_o;
wire [31:0] PCImmExtend_data_o;
wire [31:0] Registers_RSdata_o;
wire [31:0] Registers_RTdata_o;
wire [31:0] Sign_Extend_data_o;
wire [4:0]  MUX_Control_RegDst_o;
wire [1:0]  MUX_Control_ALUOp_o;
wire        MUX_Control_ALUSrc_o;
wire        MUX_Control_RegWrite_o;
wire        MUX_Control_MemToReg_o;
wire        MUX_Control_MemRead_o;
wire        MUX_Control_MemWrite_o;
wire [31:0] ForwardToData2_data_o;
wire [31:0] ID_EX_SignExtended_o;
wire        ID_EX_ALUSrc_o;
wire [1:0]  ID_EX_ALUOp_o;
wire [31:0] ForwardToData1_data_o;
wire [31:0] MUX_ALUSrc_data_o;
wire [2:0]  ALU_Control_ALUCtrl_o;
wire        ID_EX_MemRead_o;
wire [1:0]  Control_ALUOp_o;
wire        Control_ALUSrc_o;
wire        Control_RegWrite_o;
wire        Control_MemToReg_o;
wire        Control_MemRd_o;
wire        Control_MemWr_o;
wire        EX_MEM_RegWrite_o;
wire [4:0]  EX_MEM_RDaddr_o;
wire [4:0]  ID_EX_RSaddr_o;
wire [4:0]  ID_EX_RTaddr_o;
wire [1:0]  ForwardingUnit_ForwardA_o;
wire [31:0] ID_EX_RDData0_o;
wire [31:0] ID_EX_inst_o;
wire [31:0] EX_MEM_instr_o;
wire [31:0] EX_MEM_ALUResult_o;
wire [1:0]  ForwardingUnit_ForwardB_o;
wire [31:0] ID_EX_RDData1_o;
wire [31:0] ID_EX_pc_o;
wire        ALU_Zero_o;
wire [31:0] ALU_data_o;
wire [4:0]  ID_EX_RegDst_o;
wire        ID_EX_RegWrite_o;
wire        ID_EX_MemToReg_o;
wire        ID_EX_MemWrite_o;
wire [31:0] EX_MEM_RDData_o;
wire        EX_MEM_MemWrite_o;
wire        EX_MEM_MemRead_o;
wire        EX_MEM_MemToReg_o;
wire [31:0] MEM_WB_ALUResult_o;
wire [31:0] MEM_WB_DataMemReadData_o;
wire        MEM_WB_MemToReg_o;
wire [31:0] Data_Memory_data_o;
wire [31:0] data_mem_o,reg_o;
wire RegEqual;
wire PC_Branch_Select;//in IF stage
wire [31:0] VALU_v_o, EX_MEM_VALUResult_o, aluToDM_data_o; //NEW
wire toDataMemory; //NEW: used in MUX32_ref aluToDM
wire [2:0] VALU_Control_VALUCtrl_o;
wire [3:0] is_positive_line;

reg               flag;
reg               start_i;
reg [3:0] vector_signed [0:2];
reg easter_flag,easter_flag_next;
reg [7:0] egg1,egg2,egg3;
reg [2:0] easter_counter,easter_counter_next;
//------------------------- continuous assginment -------------------------------//

assign RegEqual = (Registers_RSdata_o == Registers_RTdata_o);
assign PC_Branch_Select = RegEqual & isBranch;
assign isBranch = (IF_ID_inst_o[6:0]==7'b1100011)? 1'b1:1'b0;
assign ALUfunct_in = {ID_EX_inst_o[31:25],ID_EX_inst_o[14:12]};
assign pcIm = {inst[31],inst[7],inst[30:25],inst[11:8]};
assign swIm = {inst[31:25],inst[11:7]};
assign rst = reset;
//assign op_selection = (DataOrReg)? reg_o : data_mem_o;//May28 removed.
assign toDataMemory = (EX_MEM_instr_o[6:0] == 7'b1010111)? 1 : 0; //NEW
assign is_positive_ref = is_positive_line[vout_addr];

//------------------------- Sequentail Part -------------------------------//

always@(posedge clk_i or posedge reset )begin
    if(reset)begin
        flag    <= 0;
        start_i <= 0;
        vector_signed[0] <= 0;
        vector_signed[1] <= 0;
        egg1             <= 8'b0000_1101;//013
        egg2             <= 8'b0011_0110;//054
        egg3             <= 8'b1001_1010;//154
    end
    else begin
        vector_signed[0] <= vector_signed_bits;
        vector_signed[1] <= vector_signed[0];
        egg1             <= 8'b0000_1101;//013
        egg2             <= 8'b0011_0110;//054
        egg3             <= 8'b1001_1010;//154
       if(flag)begin
            if(instr_i == 8'b1111_1111)begin
                flag    <= 0;
                start_i <= 1;
            end
            else begin
                flag    <= flag;
                start_i <= start_i;
            end
        end
        else begin
            if(instr_i == 8'b1111_1110)flag <= 1;//start reading in instr
            else flag <= flag;
            start_i <= start_i;
            
        end
    end
end

always@(posedge clk_i or posedge reset )begin
    if(reset)begin
        easter_flag    <= 0;
        easter_counter <= 0;
    end
    else begin
        easter_flag <= easter_flag_next;
        easter_counter <= easter_counter_next;
        if(easter_flag)begin
            easter_egg_ref[0] <= egg1[(3'd7 - easter_counter)];
            easter_egg_ref[1] <= egg2[(3'd7 - easter_counter)];
            easter_egg_ref[2] <= egg3[(3'd7 - easter_counter)];
        end
        else begin
            easter_egg_ref[0] <= 0;
            easter_egg_ref[1] <= 0;
            easter_egg_ref[2] <= 0;
        end
    end
end


//------------------------- Combinational Part -------------------------------//
always@(*)begin
    if(instr_i == 8'b1010_1010)easter_flag_next <= 1;
    else if(easter_counter == 3'd7)easter_flag_next <= 0;
         else                      easter_flag_next <= easter_flag;

    if(easter_flag)easter_counter_next = easter_counter + 3'd1;
    else easter_counter_next = easter_counter;
end

always@(*)begin
    case(vout_addr)
        2'b00:value_o_ref   = (DataOrReg)? reg_o[7:0]   : data_mem_o[7:0];
        2'b01:value_o_ref   = (DataOrReg)? reg_o[15:8]  : data_mem_o[15:8];
        2'b10:value_o_ref   = (DataOrReg)? reg_o[23:16] : data_mem_o[23:16];
        2'b11:value_o_ref   = (DataOrReg)? reg_o[31:24] : data_mem_o[31:24];
    endcase
end

MUX32_ref pcSelect(
    .data1_i    (addPC),
    .data2_i    (AddSum_data_o),//branch value
    .select_i   (isBranch),
    .data_o     (pcSelect_data_o)
);

PC_ref PC_ref(
    .clk_i      (clk_i),
    .start_i    (start_i),
    .pc_i       (pcSelect_data_o),
    .hazardpc_i (HazradDetect_Hazard_o),
    .pc_o       (inst_addr)
);

Adder_ref Add_PC(
    .data1_in   (inst_addr),
    .data2_in   (32'd4),
    .data_o     (addPC)              //to IF_ID_ref.pc_i
);


Instruction_Memory_ref Instruction_Memory_ref(
    .clk        (clk_i),
    .reset      (rst),
    .addr_i     (inst_addr), 
    .instr_i    (instr_i),
    .instr_o    (inst)          //to IF_ID_ref.inst_i
);

//AddSum was in EX stage initally, but moved to IF stage.
ALU_ref AddSum(
    .data1_i    (IF_ID_pc_o),
    .data2_i    (shiftLeft_data_o),
    .ALUCtrl_i  (3'b001),
    .data_o     (AddSum_data_o),
    .Zero_o     ()
);

//the following two function is for branch judgement
Shift1_ref shiftLeft(
    .data_i (PCImmExtend_data_o),
    .data_o(shiftLeft_data_o)
);

Sign_Extend_ref PCImmExtend(
    .select_i   (1'b0),
    .data0_i     (IF_ID_pcIm_o),
    .data1_i     (12'b0),
    .data_o     (PCImmExtend_data_o)  //to ID_EX_ref.pcEx_i
);
//

IF_ID_ref IF_ID_ref(
    .clk_i  (clk_i),
    .start_i    (start_i),
    .pc_i   (inst_addr),
    .inst_i (inst), 
    .hazard_i   (HazradDetect_Hazard_o),
    .flush_i    (PC_Branch_Select),
    .pcIm_i (pcIm),
    .pcIm_o (IF_ID_pcIm_o),
    .pc_o   (IF_ID_pc_o),     //to ID_EX_ref.pc_i
    .inst_o (IF_ID_inst_o)      //to ID_EX_ref.inst_i
);

Control_ref Control_ref(
    .Op_i       (IF_ID_inst_o[6:0]),
    .ALUOp_o    (Control_ALUOp_o),             //to ID_EX_ref.ALUOp_i
    .ALUSrc_o   (Control_ALUSrc_o),             //to ID_EX_ref.ALUSrc_i
    .RegWrite_o (Control_RegWrite_o),             //to ID_EX_ref.RegWrite_i
    .MemRd_o    (Control_MemRd_o),             //to ID_EX_ref.MemRead_i
    .MemWr_o    (Control_MemWr_o),             //to ID_EX_ref.MemWrite_i
    .MemToReg_o   (Control_MemToReg_o),              //to ID_EX_ref.MemToReg_i
    .immSelect_o  (Control_immSelect_o)             //to Sign_Extend_ref.select_i
);

Registers_ref Registers_ref(
    .clk_i      (clk_i),
    .reset      (rst),
    .op_address (address),
    .RSaddr_i   (IF_ID_inst_o[19:15]),     
    .RTaddr_i   (IF_ID_inst_o[24:20]),     
    .RDaddr_i   (MEM_WB_RDaddr_o), 
    .RDdata_i   (memToReg_data_o),
    .RegWrite_i (MEM_WB_RegWrite_o), 
    .is_pos_i   (vector_signed[1]),
    .RSdata_o   (Registers_RSdata_o),                  //to ID_EX_ref.RDData0_i
    .RTdata_o   (Registers_RTdata_o),                  //to ID_EX_ref.RDData1_i
    .reg_o      (reg_o),
    .pos_o      (is_positive_line)
);


Sign_Extend_ref Sign_Extend_ref(
    .select_i   (Control_immSelect_o), //select=1 for sw,0 for others
    .data0_i     (IF_ID_inst_o[31:20]),
    .data1_i     ({IF_ID_inst_o[31:25],IF_ID_inst_o[11:7]}),
    .data_o     (Sign_Extend_data_o)   // to ID_EX_ref.SignExtended_i
);

ID_EX_ref ID_EX_ref(
    .clk_i  (clk_i),
    .start_i    (start_i),
    .inst_i (IF_ID_inst_o),
    .pc_i   (IF_ID_pc_o),
    .pcEx_i(PCImmExtend_data_o),//useless for now
    .RDData0_i  (Registers_RSdata_o),
    .RDData1_i  (Registers_RTdata_o),
    .SignExtended_i (Sign_Extend_data_o),
    .RegDst_i   (MUX_Control_RegDst_o),
    .ALUOp_i    (MUX_Control_ALUOp_o),
    .ALUSrc_i   (MUX_Control_ALUSrc_o),
    .RegWrite_i (MUX_Control_RegWrite_o),
    .MemToReg_i (MUX_Control_MemToReg_o),
    .MemRead_i  (MUX_Control_MemRead_o),
    .MemWrite_i  (MUX_Control_MemWrite_o),
    .PC_branch_select_i (PC_Branch_Select),//useless
    .RSaddr_i   (IF_ID_inst_o[19:15]),     
    .RTaddr_i   (IF_ID_inst_o[24:20]),
    .inst_o (ID_EX_inst_o),     
    .pc_o   (ID_EX_pc_o),             //to EX_MEM_ref.pc_i
    .pcEx_o (),             //to shiftLeft.data_i
    .RDData0_o  (ID_EX_RDData0_o),         //to ALU_ref.data1_i
    .RDData1_o  (ID_EX_RDData1_o),         //to EX_MEM_ref.RDData_i
    .SignExtended_o (ID_EX_SignExtended_o),     //to MEX_ALUSrc.data2_i
    .RegDst_o   (ID_EX_RegDst_o),         //to EX_MEM_ref.RDaddr_i
    .ALUOp_o    (ID_EX_ALUOp_o),         //to ALU_Control_ref.ALUOp_i
    .ALUSrc_o   (ID_EX_ALUSrc_o),         //to ALUSrc.select_i
    .RegWrite_o (ID_EX_RegWrite_o),         //to EX_MEM_ref.RegWrite_i
    .MemToReg_o (ID_EX_MemToReg_o),         //to EX_MEM_ref.MemToReg_i
    .MemRead_o  (ID_EX_MemRead_o),         //to EX_MEM_ref..MemRead_i
    .MemWrite_o (ID_EX_MemWrite_o),         //to EX_MEM_ref.MemWrite_i
    .PC_branch_select_o (),
    .RSaddr_o(ID_EX_RSaddr_o),
    .RTaddr_o(ID_EX_RTaddr_o)
);

MUX32_ref MUX_ALUSrc(
    .data1_i    (ForwardToData2_data_o),
    .data2_i    (ID_EX_SignExtended_o),
    .select_i   (ID_EX_ALUSrc_o),
    .data_o     (MUX_ALUSrc_data_o)
);

ALU_Control_ref ALU_Control_ref(
    .funct_i    (ALUfunct_in),
    .ALUOp_i    (ID_EX_ALUOp_o),
    .ALUCtrl_o  (ALU_Control_ALUCtrl_o)
);

ALU_ref ALU_ref(
    .data1_i    (ForwardToData1_data_o),
    .data2_i    (MUX_ALUSrc_data_o),
    .ALUCtrl_i  (ALU_Control_ALUCtrl_o),
    .data_o     (ALU_data_o),         //to EX_MEM_ref.ALUResult_i    &    EX_MEM_ref.RDaddr_i
    .Zero_o     (ALU_Zero_o)          //to EX_MEM_ref.zero_i
);

HazradDetect_ref HazradDetect_ref(
    .IF_IDrs1_i  (IF_ID_inst_o[24:20]),
    .IF_IDrs2_i  (IF_ID_inst_o[19:15]),
    .ID_EXrd_i  (IF_ID_inst_o[19:15]),
    .ID_EX_MemRead_i    (ID_EX_MemRead_o),
    .Hazard_o   (HazradDetect_Hazard_o)
);

MUX_Control_ref MUX_Control_ref(
    .Hazard_i   (HazradDetect_Hazard_o), 
    .RegDst_i   (IF_ID_inst_o[11:7]),  
    .ALUOp_i    (Control_ALUOp_o), 
    .ALUSrc_i   (Control_ALUSrc_o),  
    .RegWrite_i (Control_RegWrite_o), 
    .MemToReg_i     (Control_MemToReg_o), 
    .MemRead_i  (Control_MemRd_o),
    .MemWrite_i     (Control_MemWr_o),
    .RegDst_o   (MUX_Control_RegDst_o),  
    .ALUOp_o    (MUX_Control_ALUOp_o), 
    .ALUSrc_o   (MUX_Control_ALUSrc_o),  
    .RegWrite_o     (MUX_Control_RegWrite_o), 
    .MemToReg_o     (MUX_Control_MemToReg_o),  
    .MemRead_o  (MUX_Control_MemRead_o),
    .MemWrite_o     (MUX_Control_MemWrite_o)  
);

ForwardingUnit_ref ForwardingUnit_ref(
    .EX_MEM_RegWrite_i (EX_MEM_RegWrite_o),
    .EX_MEM_RD_i       (EX_MEM_RDaddr_o),
    .ID_EX_RS_i        (ID_EX_RSaddr_o),
    .ID_EX_RT_i        (ID_EX_RTaddr_o),
    .MEM_WB_RegWrite_i (MEM_WB_RegWrite_o),
    .MEM_WB_RD_i       (MEM_WB_RDaddr_o),
    .ForwardA_o        (ForwardingUnit_ForwardA_o),
    .ForwardB_o        (ForwardingUnit_ForwardB_o)
);

ForwardingMUX_ref ForwardToData1(
    .select_i (ForwardingUnit_ForwardA_o),
    .data_i   (ID_EX_RDData0_o),
    .EX_MEM_i (EX_MEM_ALUResult_o),
    .MEM_WB_i (memToReg_data_o),
    .data_o   (ForwardToData1_data_o)
);

ForwardingMUX_ref ForwardToData2(
    .select_i (ForwardingUnit_ForwardB_o),
    .data_i   (ID_EX_RDData1_o),
    .EX_MEM_i (EX_MEM_ALUResult_o),
    .MEM_WB_i (memToReg_data_o),
    .data_o   (ForwardToData2_data_o)
);

EX_MEM_ref EX_MEM_ref(
    .clk_i  (clk_i),
    .start_i    (start_i),
    .pc_i   (ID_EX_pc_o),
    .zero_i (ALU_Zero_o),
    .ALUResult_i    (ALU_data_o),
    .VALUResult_i (VALU_v_o), //NEW
    .RDData_i   (ForwardToData2_data_o),//Reg read data2
    .RDaddr_i   (ID_EX_RegDst_o),//from IF_ID_ref.inst_o[11:7]
    .RegWrite_i (ID_EX_RegWrite_o),
    .MemToReg_i (ID_EX_MemToReg_o),
    .MemRead_i  (ID_EX_MemRead_o),
    .MemWrite_i (ID_EX_MemWrite_o),
    .instr_i(ID_EX_inst_o),
    .instr_o(EX_MEM_instr_o),
    .pc_o   (),
    .zero_o (),
    .ALUResult_o    (EX_MEM_ALUResult_o),
    .VALUResult_o (EX_MEM_VALUResult_o), //NEW         //to MEM_WB_ref.ALUResult_i
    .RDData_o   (EX_MEM_RDData_o),             //to MEM_WB_ref.RDData_i
    .RDaddr_o   (EX_MEM_RDaddr_o),             //to MEM_WB_ref.RDaddr_i 
    .RegWrite_o (EX_MEM_RegWrite_o),             //to MEM_WB_ref.RegWrite_i
    .MemToReg_o (EX_MEM_MemToReg_o),             //to MEM_WB_ref.MemToReg_i
    .MemRead_o  (EX_MEM_MemRead_o),             //to Data_Memory_ref.MemRead_i
    .MemWrite_o (EX_MEM_MemWrite_o)              //to Data_Memory_ref.MemWrite_i
);

Data_Memory_ref Data_Memory_ref(
    .clk_i      (clk_i),
    .reset      (rst),
    .op_addr    (address),
    .addr_i     (aluToDM_data_o),
    .data_i     (EX_MEM_RDData_o),
    .MemWrite_i (EX_MEM_MemWrite_o),
    .MemRead_i  (EX_MEM_MemRead_o),
    .data_o     (Data_Memory_data_o),
    .data_mem_o (data_mem_o)
);

MEM_WB_ref MEM_WB_ref(
    .clk_i  (clk_i),
    .start_i    (start_i),
    //.ALUResult_i    (EX_MEM_ALUResult_o),
    .ALUResult_i    (aluToDM_data_o),
    .RDData_i   (EX_MEM_RDData_o),
    .RDaddr_i   (EX_MEM_RDaddr_o),
    .RegWrite_i (EX_MEM_RegWrite_o),
    .MemToReg_i (EX_MEM_MemToReg_o),
    .DataMemReadData_i(Data_Memory_data_o),
    .ALUResult_o    (MEM_WB_ALUResult_o),
    .RDData_o   (),         //to memToReg.data1_i
    .RDaddr_o   (MEM_WB_RDaddr_o),         
    .RegWrite_o (MEM_WB_RegWrite_o),         //to Registera.RegWrite_i
    .MemToReg_o (MEM_WB_MemToReg_o),          //to memToReg.select_i
    .DataMemReadData_o(MEM_WB_DataMemReadData_o)
);

MUX32_ref memToReg(
    .data1_i    (MEM_WB_ALUResult_o),
    .data2_i    (MEM_WB_DataMemReadData_o),
    .select_i   (MEM_WB_MemToReg_o),//MemToReg control
    .data_o     (memToReg_data_o)
);

MUX32_ref aluToDM( //NEW module: to decide if addr_i in Data_Memory_ref comes from ALU_ref or VALU_ref
    .data1_i(EX_MEM_ALUResult_o),
    .data2_i(EX_MEM_VALUResult_o),
    .select_i(toDataMemory), //NEW, no change in MUX32_ref.v
    .data_o(aluToDM_data_o) //to Data_Memory_ref Data_Memory_ref
);

VALU_ref VALU_ref( //NEW module
    .v1_i(ForwardToData1_data_o),
    .v2_i(MUX_ALUSrc_data_o),
    .VALUCtrl_i(VALU_Control_VALUCtrl_o),
    .v_o(VALU_v_o),
    .over(vector_signed_bits)
);

VALU_ctrl_ref VALU_Control( //NEW module
    .vfunct_i(ALUfunct_in),
    .VALUCtrl_o(VALU_Control_VALUCtrl_o)
);

endmodule

