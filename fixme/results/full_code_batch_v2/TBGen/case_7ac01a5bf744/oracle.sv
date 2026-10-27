`timescale 1ns/1ps
module oracle_wb_regfile (clk_i, nrst_i, wb_adr_i, wb_dat_o, wb_dat_i, wb_sel_i, wb_we_i,
                   wb_stb_i, wb_cyc_i, wb_ack_o, wb_err_o, ws_i, datareg0, datareg1);
    input          clk_i;
    input          nrst_i;
    input    [3:0] wb_adr_i;
    output reg [31:0] wb_dat_o;
    input   [31:0] wb_dat_i;
    input    [3:0] wb_sel_i;
    input          wb_we_i;
    input          wb_stb_i;
    input          wb_cyc_i;
    output reg     wb_ack_o;
    output         wb_err_o;
    input    [7:0] ws_i;	 
    output  [31:0] datareg0;
    output  [31:0] datareg1;
    reg      [7:0] waitstate;
    wire wb_acc = wb_cyc_i & wb_stb_i;    
    wire wb_wr  = wb_acc & wb_we_i;       
    reg [7:0]   datareg0_0;
    reg [7:0]   datareg0_1;
    reg [7:0]   datareg0_2;
    reg [7:0]   datareg0_3;
    reg [7:0]   datareg1_0;
    reg [7:0]   datareg1_1;
    reg [7:0]   datareg1_2;
    reg [7:0]   datareg1_3;
    always @(posedge clk_i or negedge nrst_i)
        if (~nrst_i)                
            begin
                datareg0_0 <= 8'h00;
                datareg0_1 <= 8'h01;
                datareg0_2 <= 8'h02;
                datareg0_3 <= 8'h03;
                datareg1_0 <= 8'h10;
                datareg1_1 <= 8'h11;
                datareg1_2 <= 8'h12;
                datareg1_3 <= 8'h13;
                wb_ack_o <= 1'b0;
                waitstate <= 4'b0;
					 wb_dat_o <= 32'h00000000;
            end
        else if(wb_wr)          
            case (wb_sel_i)
                4'b0000:
                    case (wb_adr_i)         
                        4'b0000: datareg0_0 <= wb_dat_i[7:0];
                        4'b0001: datareg0_1 <= wb_dat_i[7:0];
                        4'b0010: datareg0_2 <= wb_dat_i[7:0];
                        4'b0011: datareg0_3 <= wb_dat_i[7:0];
                        4'b0100: datareg1_0 <= wb_dat_i[7:0];
                        4'b0101: datareg1_1 <= wb_dat_i[7:0];
                        4'b0110: datareg1_2 <= wb_dat_i[7:0];
                        4'b0111: datareg1_3 <= wb_dat_i[7:0];
                    endcase
                4'b0001:
                    case (wb_adr_i)         
                        4'b0000: datareg0_0 <= wb_dat_i[7:0];
                        4'b0001: datareg0_1 <= wb_dat_i[7:0];
                        4'b0010: datareg0_2 <= wb_dat_i[7:0];
                        4'b0011: datareg0_3 <= wb_dat_i[7:0];
                        4'b0100: datareg1_0 <= wb_dat_i[7:0];
                        4'b0101: datareg1_1 <= wb_dat_i[7:0];
                        4'b0110: datareg1_2 <= wb_dat_i[7:0];
                        4'b0111: datareg1_3 <= wb_dat_i[7:0];
                    endcase
                4'b0011:
                    {datareg0_1, datareg0_0} <= wb_dat_i[15:0];
                4'b1111:
                    {datareg0_3, datareg0_2, datareg0_1, datareg0_0} <= wb_dat_i[31:0];
            endcase
    always @(posedge clk_i)
        case (wb_sel_i)
            4'b0000:
                case (wb_adr_i)     
                    4'b0000: wb_dat_o[7:0] <= datareg0_0;
                    4'b0001: wb_dat_o[7:0] <= datareg0_1;
                    4'b0010: wb_dat_o[7:0] <= datareg0_2;
                    4'b0011: wb_dat_o[7:0] <= datareg0_3;
                    4'b0100: wb_dat_o[7:0] <= datareg1_0;
                    4'b0101: wb_dat_o[7:0] <= datareg1_1;
                    4'b0110: wb_dat_o[7:0] <= datareg1_2;
                    4'b0111: wb_dat_o[7:0] <= datareg1_3;
                endcase
            4'b0001:
                case (wb_adr_i)     
                    4'b0000: wb_dat_o[7:0] <= datareg0_0;
                    4'b0001: wb_dat_o[7:0] <= datareg0_1;
                    4'b0010: wb_dat_o[7:0] <= datareg0_2;
                    4'b0011: wb_dat_o[7:0] <= datareg0_3;
                    4'b0100: wb_dat_o[7:0] <= datareg1_0;
                    4'b0101: wb_dat_o[7:0] <= datareg1_1;
                    4'b0110: wb_dat_o[7:0] <= datareg1_2;
                    4'b0111: wb_dat_o[7:0] <= datareg1_3;
                endcase
            4'b0011:
                    wb_dat_o[15:0] <= {datareg0_1, datareg0_0};
            4'b1111:
                    wb_dat_o[31:0] <= {datareg0_3, datareg0_2, datareg0_1, datareg0_0};
        endcase
    always @(posedge clk_i or negedge nrst_i)
        if (nrst_i) begin            
            if (ws_i == 0) begin
                wb_ack_o <= wb_acc & !wb_ack_o;
                end else
            if((waitstate == 4'b0) && (ws_i != 0)) begin
                wb_ack_o <= 1'b0;
                if(wb_acc) begin
                    waitstate <= waitstate + 1;
                end
            end
            else begin
                if(wb_acc) waitstate <= waitstate + 1;
                if(waitstate == ws_i) begin
                    if(wb_acc) wb_ack_o <= 1'b1;
                    waitstate <= 1'b0;
                end
            end
        end
    assign datareg0 = { datareg0_3, datareg0_2, datareg0_1, datareg0_0 };
    assign datareg1 = { datareg1_3, datareg1_2, datareg1_1, datareg1_0 };
    assign wb_err_o = wb_ack_o & wb_adr_i[3];
endmodule