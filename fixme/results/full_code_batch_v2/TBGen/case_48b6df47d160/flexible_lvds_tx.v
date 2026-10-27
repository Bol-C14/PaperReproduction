`timescale 1ns/1ps

module flexible_lvds_tx (
    tx_in,          
    tx_fastclk,     
    tx_slowclk,     
    tx_regclk,      
    tx_locked,      
    tx_out          
);
    parameter number_of_channels = 1;
    parameter deserialization_factor = 4;
    parameter registered_input = "ON";
    parameter REGISTER_WIDTH = deserialization_factor*number_of_channels;
    parameter DOUBLE_DESER = deserialization_factor*2;
    input [REGISTER_WIDTH -1: 0] tx_in;
    input tx_fastclk;
    input tx_slowclk;
    input tx_regclk;
    input tx_locked;
    output [number_of_channels -1 :0] tx_out;
    reg [REGISTER_WIDTH -1 : 0]     tx_reg;
    reg [(REGISTER_WIDTH*2) -1 : 0] tx_reg2;
    reg [REGISTER_WIDTH -1 : 0]     tx_shift_reg;
    reg [(REGISTER_WIDTH*2) -1 : 0] tx_shift_reg2;
    reg [REGISTER_WIDTH -1 :0] h_sync_a;
    reg [(REGISTER_WIDTH*2) -1 :0] sync_b_reg;
    reg [number_of_channels -1 :0] dataout_h;
    reg [number_of_channels -1 :0] dataout_l;
    reg [number_of_channels -1 :0] dataout_tmp;
    reg [number_of_channels -1 :0] tx_ddio_out;
    wire [REGISTER_WIDTH -1 : 0] tx_in_int;
    wire [(REGISTER_WIDTH*2) -1 : 0] tx_in_int2;
    integer i1;
    integer i2;
    integer i3;
    integer x;
    integer x2;
    integer loadcnt;
    initial
    begin : INITIALIZATION
        tx_reg = {REGISTER_WIDTH{1'b0}};
        tx_reg2 = {(REGISTER_WIDTH*2){1'b0}};
        tx_shift_reg = {REGISTER_WIDTH{1'b0}};
        tx_shift_reg2 = {(REGISTER_WIDTH*2){1'b0}};
        dataout_h = {number_of_channels{1'b0}};
        dataout_l = {number_of_channels{1'b0}};
        dataout_tmp = {number_of_channels{1'b0}};
        tx_ddio_out = {number_of_channels{1'b0}};
        h_sync_a = {REGISTER_WIDTH{1'b0}};
        sync_b_reg = {(REGISTER_WIDTH*2){1'b0}};
        loadcnt = 0;
    end 
    always @ (posedge tx_fastclk)
    begin : DDIO_OUT_POS
        if ((deserialization_factor % 2) == 0)
        begin
            for (i1 = 0;  i1 < number_of_channels; i1 = i1 +1)
            begin
                dataout_h[i1] <= tx_shift_reg[(i1+1)*deserialization_factor-1];
                dataout_l[i1] <= tx_shift_reg[(i1+1)*deserialization_factor-2];
                dataout_tmp[i1] <= tx_shift_reg[(i1+1)*deserialization_factor-1];
            end
        end
        else
        begin
            for (i1 = 0;  i1 < number_of_channels; i1 = i1 +1)
            begin
                dataout_h[i1] <= tx_shift_reg2[(i1+1)*DOUBLE_DESER-1];
                dataout_l[i1] <= tx_shift_reg2[(i1+1)*DOUBLE_DESER-2];
                dataout_tmp[i1] <= tx_shift_reg2[(i1+1)*DOUBLE_DESER-1];
            end
        end
    end 
    always @ (negedge tx_fastclk)
    begin : DDIO_OUT_NEG
        dataout_tmp <= dataout_l;
    end 
    always @ (posedge tx_fastclk)
    begin  : SHIFTREG
        begin
            if ((deserialization_factor % 2) == 0)
            begin
                loadcnt <= (loadcnt + 1) % (deserialization_factor/2);
                if(loadcnt == 0)
                    tx_shift_reg <= tx_in_int;
                else
                begin
                    for (i2= 0; i2 < number_of_channels; i2 = i2+1)
                    begin
                        for (x=deserialization_factor-1; x >1; x=x-1)
                            tx_shift_reg[x + (i2 * deserialization_factor)] <=
                                tx_shift_reg [x-2 + (i2 * deserialization_factor)];
                    end
                end
            end
            else 
            begin
                loadcnt <= (loadcnt + 1) % deserialization_factor;
                if(loadcnt == 0)
                    tx_shift_reg2 <= tx_in_int2;
                else
                begin
                    for (i2= 0; i2 < number_of_channels; i2 = i2+1)
                    begin
                        for (x=DOUBLE_DESER-1; x >1; x=x-1)
                            tx_shift_reg2[x + (i2 * DOUBLE_DESER)] <=
                                tx_shift_reg2 [x-2 + (i2 * DOUBLE_DESER)];
                    end
                end
            end
        end
    end 
    always @ (posedge tx_slowclk)
    begin : SYNC_REG_POS
            h_sync_a <= tx_in;
    end 
    always @ (negedge tx_slowclk)
    begin : SYNC_REG_NEG
        for (i3= 0; i3 < number_of_channels; i3 = i3+1)
        begin
            for (x2=0; x2 < deserialization_factor; x2=x2+1)
            begin
                sync_b_reg[x2 + (((i3 * 2) + 1) * deserialization_factor)] <=
                    h_sync_a[x2 + (i3 * deserialization_factor)];
                sync_b_reg[x2 + (i3 * DOUBLE_DESER)] <=
                    tx_in[x2 + (i3 * deserialization_factor)];
            end
        end
    end 
    always @ (posedge tx_regclk)
    begin : IN_REG
        if ((deserialization_factor % 2) == 0)
            tx_reg  <= tx_in;
        else
            tx_reg2 <= sync_b_reg;
    end 
    assign tx_in_int  = (registered_input == "OFF") ? tx_in : tx_reg;
    assign tx_in_int2 = (registered_input == "OFF") ? sync_b_reg : tx_reg2;
    assign tx_out = dataout_tmp;
endmodule
