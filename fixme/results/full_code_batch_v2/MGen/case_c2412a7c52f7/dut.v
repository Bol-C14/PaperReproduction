`timescale 1ns/1ps
 
module top (
    rx_in,
    rx_fastclk,
    rx_slowclk,
    rx_locked,
    rx_coreclk,
    rx_reset,
    rx_dpll_reset,
    rx_channel_data_align,
    rx_out,
    rx_dpa_locked
);
    parameter number_of_channels = 1;
    parameter deserialization_factor = 4;
    parameter use_coreclock_input = "OFF";
    parameter enable_dpa_fifo = "ON";
    parameter registered_output = "ON";
    parameter REGISTER_WIDTH = deserialization_factor*number_of_channels;
    input [number_of_channels -1 :0] rx_in;
    input rx_fastclk;
    input rx_slowclk;
    input rx_locked;
    input [number_of_channels -1 :0] rx_coreclk;
    input [number_of_channels -1 :0] rx_reset;
    input [number_of_channels -1 :0] rx_dpll_reset;
    input [number_of_channels -1 :0] rx_channel_data_align;
    output [REGISTER_WIDTH -1: 0] rx_out;
    output [number_of_channels -1: 0] rx_dpa_locked;
    reg [REGISTER_WIDTH -1 : 0] rx_shift_reg;
    reg [REGISTER_WIDTH -1 : 0] rx_parallel_load_reg;
    reg [number_of_channels -1 : 0] rx_in_reg;
    reg [number_of_channels -1 : 0] dpa_in;
    reg [number_of_channels -1 : 0] retime_data;
    reg [REGISTER_WIDTH -1 : 0] ram_array0;
    reg [REGISTER_WIDTH -1 : 0] ram_array1;
    reg [REGISTER_WIDTH -1 : 0] ram_array2;
    reg [REGISTER_WIDTH -1 : 0] ram_array3;
    reg [2 : 0] wrPtr [number_of_channels -1 : 0];
    reg [2 : 0] rdPtr [number_of_channels -1 : 0];
    reg [3 : 0] bitslip_count [number_of_channels -1 : 0];
    reg [3 : 0] bitslip_count_pre [number_of_channels -1 : 0];
    reg [REGISTER_WIDTH -1 : 0] rxpdat2;
    reg [REGISTER_WIDTH -1 : 0] rxpdat3;
    reg [REGISTER_WIDTH -1 : 0] rxpdatout;
    reg [REGISTER_WIDTH -1 : 0] fifo_data_out;
    reg [REGISTER_WIDTH -1 : 0] rx_out_reg;
    reg [number_of_channels -1 : 0] dpagclk_pre;
    reg [number_of_channels -1 : 0] rx_channel_data_align_pre;
    reg [number_of_channels -1 : 0] fifo_write_clk_pre;
    reg [number_of_channels -1 : 0] clkout_tmp;
    reg [number_of_channels -1 : 0] sync_reset;
    wire [number_of_channels -1:0] dpagclk;
    wire[number_of_channels -1:0] fifo_write_clk;
    wire [REGISTER_WIDTH -1 : 0] rx_out_int;
    wire [REGISTER_WIDTH -1 : 0] serdes_data_out;
    wire [REGISTER_WIDTH -1 : 0] fifo_data_in;
    wire [REGISTER_WIDTH -1 : 0] rxpdat1;
    tri0[number_of_channels -1 :0] rx_reset;
    tri0[number_of_channels -1 :0] rx_dpll_reset;
    tri0[number_of_channels -1 :0] rx_channel_data_align;
    tri0[number_of_channels -1 :0] rx_coreclk;
    integer i;
    integer i0;
    integer i1;
    integer i2;
    integer i3;
    integer i4;
    integer i5;
    integer i6;
    integer i7;
    integer i8;
    integer j;
    integer j1;
    integer j2;
    integer j3;
    integer k;
    integer x;
    integer negedge_count;
    integer fastclk_posedge_count [number_of_channels -1: 0];
    integer fastclk_negedge_count [number_of_channels - 1 : 0];
    integer bitslip_count_reg [number_of_channels -1: 0];
    initial
    begin : INITIALIZATION
        rxpdat2 = {REGISTER_WIDTH{1'b0}};
        rxpdat3 = {REGISTER_WIDTH{1'b0}};
        rxpdatout = {REGISTER_WIDTH{1'b0}};
        rx_out_reg = {REGISTER_WIDTH{1'b0}};
        ram_array0 = {REGISTER_WIDTH{1'b0}};
        ram_array1 = {REGISTER_WIDTH{1'b0}};
        ram_array2 = {REGISTER_WIDTH{1'b0}};
        ram_array3 = {REGISTER_WIDTH{1'b0}};
        rx_in_reg = {number_of_channels{1'b0}};
        dpa_in = {number_of_channels{1'b0}};
        retime_data = {number_of_channels{1'b0}};
        rx_channel_data_align_pre = {number_of_channels{1'b0}};
        clkout_tmp = {number_of_channels{1'b0}};
        sync_reset = {number_of_channels{1'b0}};
        rx_shift_reg = {REGISTER_WIDTH{1'b0}};
        rx_parallel_load_reg = {REGISTER_WIDTH{1'b0}};
        fifo_data_out = {REGISTER_WIDTH{1'b0}};      
        for (i = 0; i < number_of_channels; i = i + 1)
        begin
            wrPtr[i] = 0;
            rdPtr[i] = 2;
            bitslip_count[i] = 0;
            bitslip_count_reg[i] = 0;
            fastclk_posedge_count[i] = 0;
            fastclk_negedge_count[i] = 0;
        end
    end 
    always @ (posedge dpagclk)
    begin : DPA_SERDES_SLOWCLK
        for(i0 = 0; i0 <=number_of_channels -1; i0=i0+1)
        begin
            if ((dpagclk[i0] == 1'b1) && (dpagclk_pre[i0] == 1'b0))
            begin
                if ((rx_reset[i0] == 1'b1) || (rx_dpll_reset[i0] == 1'b1))
                    sync_reset[i0] <= 1'b1;
                else
                    sync_reset[i0] <= 1'b0;
                fastclk_negedge_count[i0] <= #1 0;
            end
        end
    end 
    always @ (posedge rx_fastclk)
    begin : DPA_SERDES_POSEDGE_FASTCLK
        for(i1 = 0; i1 <=number_of_channels -1; i1=i1+1)
        begin
            if (fastclk_negedge_count[i1] == 2)
                rx_parallel_load_reg <= rx_shift_reg;
            if (sync_reset[i1] == 1'b1)
            begin
                fastclk_posedge_count[i1] <= 0;
                clkout_tmp[i1] <= 1'b0;
            end
            else
            begin
                if (fastclk_posedge_count[i1] % (deserialization_factor / 2) == 0)
                begin
                    fastclk_posedge_count[i1] <= 1;
                    clkout_tmp[i1] <= !clkout_tmp[i1];
                end
                fastclk_posedge_count[i1] <= (fastclk_posedge_count[i1] + 1) % deserialization_factor;
            end
        end
    end 
    always @ (negedge rx_fastclk)
    begin : DPA_SERDES_NEGEDGE_FAST_CLOCK
        if (rx_fastclk == 1'b0)
        begin
            for (i2 = 0; i2 <= number_of_channels -1; i2 = i2+1)
            begin
                for (x=deserialization_factor-1; x > 0; x=x-1)
                    rx_shift_reg[x + (i2 * deserialization_factor)] <=  rx_shift_reg [x-1 + (i2 * deserialization_factor)];
                rx_shift_reg[i2 * deserialization_factor] <= retime_data[i2];
                retime_data <= rx_in;
                fastclk_negedge_count[i2] <= (fastclk_negedge_count[i2] + 1) ;
            end
        end
    end 
    always @ (posedge fifo_write_clk)
    begin : DPA_FIFO_WRITE_CLOCK
        if ((enable_dpa_fifo == "ON")  && (rx_locked == 1'b1))
        begin
            for (i3 = 0; i3 <= number_of_channels-1; i3 = i3+1)
            begin
                if(sync_reset[i3] == 1'b1)
                    wrPtr[i3] <= 0;
                else if ((fifo_write_clk[i3] == 1'b1) && (fifo_write_clk_pre[i3] == 1'b0))
                begin
                    case (wrPtr[i3])
                        3'b000:
                            for (j = i3*deserialization_factor; j <= (i3+1)*deserialization_factor -1; j=j+1)
                                ram_array0[j] <= fifo_data_in[j];
                        3'b001:
                            for (j = i3*deserialization_factor; j <= (i3+1)*deserialization_factor -1; j=j+1)
                                ram_array1[j] <= fifo_data_in[j];
                        3'b010:
                            for (j = i3*deserialization_factor; j <= (i3+1)*deserialization_factor -1; j=j+1)
                                ram_array2[j] <= fifo_data_in[j];
                        3'b011:
                            for (j = i3*deserialization_factor; j <= (i3+1)*deserialization_factor -1; j=j+1)
                                ram_array3[j] <= fifo_data_in[j];
                        default:
                            $display ("Error! Invalid wrPtr value.");
                    endcase
                    wrPtr[i3] <= (wrPtr[i3] + 1) % 4;
                end
            end
        end
    end 
    always @ (negedge fifo_write_clk)
    begin
        for (i6 = 0; i6 <= number_of_channels-1; i6 = i6+1)
        begin
            if (fifo_write_clk[i6] == 1'b0)
                fifo_write_clk_pre[i6] <= fifo_write_clk[i6];
        end
    end
    always @ (posedge dpagclk)
    begin : DPA_FIFO_SLOW_CLOCK
        if((enable_dpa_fifo == "ON") )
        begin
            for (i4 = 0; i4 <= number_of_channels-1; i4 = i4+1)
            begin
                if ((dpagclk[i4] == 1'b1) && (dpagclk_pre[i4] == 1'b0))
                begin
                    if ((rx_reset[i4] == 1'b1) || (rx_dpll_reset[i4] == 1'b1) || (sync_reset[i4] == 1'b1))
                    begin
                        for (j1 = i4*deserialization_factor; j1 <= (i4+1)*deserialization_factor -1; j1=j1+1)
                        begin
                            fifo_data_out[j1] <=  1'b0;
                            ram_array0[j1]  <=  1'b0;
                            ram_array1[j1]  <=  1'b0;
                            ram_array2[j1]  <=  1'b0;
                            ram_array3[j1]  <=  1'b0;
                        end
                        wrPtr[i4] <= 0;
                        rdPtr[i4] <= 2;
                    end
                    else
                    begin
                        case (rdPtr[i4])
                            3'b000:
                                for (j1 = i4*deserialization_factor; j1 <= (i4+1)*deserialization_factor -1; j1=j1+1)
                                    fifo_data_out[j1] <= ram_array0[j1];
                            3'b001:
                                for (j1 = i4*deserialization_factor; j1 <= (i4+1)*deserialization_factor -1; j1=j1+1)
                                    fifo_data_out[j1] <= ram_array1[j1];
                            3'b010:
                                for (j1 = i4*deserialization_factor; j1 <= (i4+1)*deserialization_factor -1; j1=j1+1)
                                    fifo_data_out[j1] <= ram_array2[j1];
                            3'b011:
                                for (j1 = i4*deserialization_factor; j1 <= (i4+1)*deserialization_factor -1; j1=j1+1)
                                    fifo_data_out[j1] <= ram_array3[j1];
                            default:
                                $display ("Error! Invalid rdPtr value.");
                        endcase
                        rdPtr[i4] <= (rdPtr[i4] + 1) % 4;
                    end
                end
            end
        end
    end 
    always @ (posedge dpagclk)
    begin : DPA_BIT_SLIP
        for (i5 = 0; i5 <= number_of_channels-1; i5 = i5 + 1)
        begin
            if ((dpagclk[i5] == 1'b1) && (dpagclk_pre[i5] == 1'b0))
            begin
                if ((sync_reset[i5] == 1'b1) || (rx_reset[i5] == 1'b1) ||
                    (rx_dpll_reset[i5] == 1'b1))
                begin
                    for(j2 = deserialization_factor*i5; j2 <= deserialization_factor*(i5+1) -1; j2=j2+1)
                    begin
                        rxpdat2[j2] <= 1'b0;
                        rxpdat3[j2] <= 1'b0;
                        rxpdatout[j2] <= 1'b0;
                    end
                    bitslip_count[i5] <= 0;
                    bitslip_count_reg[i5] <= 0;
                end
                else
                begin
                    if ((rx_channel_data_align[i5] == 1'b1) && (rx_channel_data_align_pre[i5] == 1'b0))
                        bitslip_count[i5] <= (bitslip_count[i5] + 1) % deserialization_factor;
                    bitslip_count_reg[i5] <= bitslip_count[i5];
                    rxpdat2 <= rxpdat1;
                    rxpdat3 <= rxpdat2;
                    for(j2 = deserialization_factor*i5 + bitslip_count_reg[i5]; j2 <= deserialization_factor*(i5+1) -1; j2=j2+1)
                        rxpdatout[j2] <=  rxpdat3[j2-bitslip_count_reg[i5]];
                    for(j2 = deserialization_factor*i5 ; j2 <= deserialization_factor*i5 + bitslip_count_reg[i5] -1; j2=j2+1)
                        rxpdatout[j2] <=  rxpdat2[j2+ deserialization_factor -bitslip_count_reg[i5]];
                end
                rx_channel_data_align_pre[i5] <= rx_channel_data_align[i5];
            end
        end
    end 
    always @ (posedge dpagclk)
    begin : SYNC_REGISTER
        for (i8 = 0; i8 < number_of_channels; i8 = i8+1)
        begin
            if ((dpagclk[i8] == 1'b1) && (dpagclk_pre[i8] == 1'b0))
            begin
                for (j3 = 0; j3 < deserialization_factor; j3 = j3+1)
                    rx_out_reg[i8*deserialization_factor + j3] <= rxpdatout[i8*deserialization_factor + j3];
            end
        end
    end 
    always @ (dpagclk)
    begin
        dpagclk_pre <= dpagclk;
    end
    assign dpagclk = (use_coreclock_input == "ON") ? rx_coreclk : {number_of_channels{rx_slowclk}};
    assign rxpdat1 = (enable_dpa_fifo == "ON") ? fifo_data_out  : serdes_data_out;
    assign serdes_data_out = rx_parallel_load_reg;
    assign fifo_data_in = serdes_data_out;
    assign fifo_write_clk = clkout_tmp;
    assign rx_dpa_locked = {number_of_channels {1'b1}};
    assign rx_out = (registered_output == "ON") ? rx_out_reg : rxpdatout;
endmodule

