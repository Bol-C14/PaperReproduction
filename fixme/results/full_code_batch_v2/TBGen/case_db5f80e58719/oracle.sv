`timescale 1ns/1ps
module oracle_M65C02_BCD(
    input   Rst,                
    input   Clk,                
    input   En,                 
    input   Op,                 
    input   [7:0] A,            
    input   [7:0] B,            
    input   Ci,                 
    output  reg [8:0] Out,      
    output  reg OV,             
    output  reg Valid           
);
reg     [7:0] S;        
reg     [1:0] DA;       
reg     C3, C7;         
reg     [7:0] Adj;
reg     rEn, rOp;
reg     [7:0] rS;
reg     rC3, rC7;
reg     MSN_GT9, MSN_GT8, LSN_GT9;  
assign Rst_BCD = (Rst | ~En);               
always @(posedge Clk or posedge Rst_BCD)    
begin
    if(Rst_BCD)
        {rEn, rOp} <= #1 0;
    else
        {rEn, rOp} <= #1 {En, Op};
end        
always @(*)
begin
    {C3, S[3:0]} <= ({1'b0, A[3:0]} + {1'b0, B[3:0]} + {4'b0, Ci});
    {C7, S[7:4]} <= ({1'b0, A[7:4]} + {1'b0, B[7:4]} + {4'b0, C3});
end
always @(posedge Clk)
begin
    if(Rst)
        {rC7, rC3, rS} <= #1 0;
    else if(En)
        {rC7, rC3, rS} <= #1 {C7, C3, S};
end
always @(*)
begin
    case(rS[7:4])
        4'b0000 : MSN_GT9 <= 0;
        4'b0001 : MSN_GT9 <= 0;
        4'b0010 : MSN_GT9 <= 0;
        4'b0011 : MSN_GT9 <= 0;
        4'b0100 : MSN_GT9 <= 0;
        4'b0101 : MSN_GT9 <= 0;
        4'b0110 : MSN_GT9 <= 0;
        4'b0111 : MSN_GT9 <= 0;
        4'b1000 : MSN_GT9 <= 0;
        4'b1001 : MSN_GT9 <= 0;
        4'b1010 : MSN_GT9 <= 1;
        4'b1011 : MSN_GT9 <= 1;
        4'b1100 : MSN_GT9 <= 1;
        4'b1101 : MSN_GT9 <= 1;
        4'b1110 : MSN_GT9 <= 1;
        4'b1111 : MSN_GT9 <= 1;
    endcase
end
always @(*)
begin
    case(rS[7:4])
        4'b0000 : MSN_GT8 <= 0;
        4'b0001 : MSN_GT8 <= 0;
        4'b0010 : MSN_GT8 <= 0;
        4'b0011 : MSN_GT8 <= 0;
        4'b0100 : MSN_GT8 <= 0;
        4'b0101 : MSN_GT8 <= 0;
        4'b0110 : MSN_GT8 <= 0;
        4'b0111 : MSN_GT8 <= 0;
        4'b1000 : MSN_GT8 <= 0;
        4'b1001 : MSN_GT8 <= 1;
        4'b1010 : MSN_GT8 <= 1;
        4'b1011 : MSN_GT8 <= 1;
        4'b1100 : MSN_GT8 <= 1;
        4'b1101 : MSN_GT8 <= 1;
        4'b1110 : MSN_GT8 <= 1;
        4'b1111 : MSN_GT8 <= 1;
    endcase
end
always @(*)
begin
    case(rS[3:0])
        4'b0000 : LSN_GT9 <= 0;
        4'b0001 : LSN_GT9 <= 0;
        4'b0010 : LSN_GT9 <= 0;
        4'b0011 : LSN_GT9 <= 0;
        4'b0100 : LSN_GT9 <= 0;
        4'b0101 : LSN_GT9 <= 0;
        4'b0110 : LSN_GT9 <= 0;
        4'b0111 : LSN_GT9 <= 0;
        4'b1000 : LSN_GT9 <= 0;
        4'b1001 : LSN_GT9 <= 0;
        4'b1010 : LSN_GT9 <= 1;
        4'b1011 : LSN_GT9 <= 1;
        4'b1100 : LSN_GT9 <= 1;
        4'b1101 : LSN_GT9 <= 1;
        4'b1110 : LSN_GT9 <= 1;
        4'b1111 : LSN_GT9 <= 1;
    endcase
end
always @(*)
begin
    DA[1] <= ((rOp) ? ~rC7 | (DA[0] & MSN_GT9)
                    :  rC7 | MSN_GT9 | (DA[0] & ~rC3 & MSN_GT8));
    DA[0] <= ((rOp) ? ~rC3
                    :  rC3 | LSN_GT9);
    case(DA)
        2'b01   : Adj <= (rS + ((rOp) ? 8'hFA : 8'h06)); 
        2'b10   : Adj <= (rS + ((rOp) ? 8'hA0 : 8'h60)); 
        2'b11   : Adj <= (rS + ((rOp) ? 8'h9A : 8'h66)); 
        default : Adj <= (rS + 8'h00);                   
    endcase
end
always @(*)
begin
    Out   <= ((rEn) ? {(rOp ^ DA[1]), Adj} : 0);
    OV    <= ((rEn) ? DA[1]                : 0);
    Valid <= rEn;
end
endmodule