`timescale 1ns/1ps
 
module altaccumulate_ref (cin, data, add_sub, clock, sload, clken, sign_data, aclr,
                        result, cout, overflow);
    parameter width_in = 4;     
    parameter width_out = 8;    
    parameter lpm_representation = "UNSIGNED";
    parameter extra_latency = 0;
    parameter use_wys = "ON";
    parameter lpm_hint = "UNUSED";
    parameter lpm_type = "altaccumulate";
    input cin;
    input [width_in-1:0] data;  
    input add_sub;              
    input clock;                
    input sload;                
    input clken;                
    input sign_data;            
    input aclr;                 
    output [width_out-1:0] result;  
    output cout;
    output overflow;
    reg [width_out:0] temp_sum;
    reg overflow;
    reg overflow_int;
    reg cout_int;
    reg cout_delayed;
    reg [width_out-1:0] result;
    reg [width_out+1:0] result_int;
    reg [(width_out - width_in) : 0] zeropad;
    reg borrow;
    reg cin_int;
    reg [width_out-1:0] fb_int;
    reg [width_out -1:0] data_int;
    reg [width_out+1:0] result_pipe [extra_latency:0];
    reg [width_out+1:0] result_full;
    reg [width_out+1:0] result_full2;
    reg a;
    wire [width_out:0] temp_sum_wire;
    wire cout;
    wire cout_int_wire;
    wire cout_delayed_wire;
    wire overflow_int_wire;
    wire [width_out+1:0] result_int_wire;
    tri0 aclr_int;
    tri0 sign_data_int;
    tri0 sload_int;
    tri1 clken_int;
    tri1 add_sub_int;
    integer head;
    integer i;
    initial
    begin
        if( width_in <= 0 )
        begin
            $display("Error! Value of width_in parameter must be greater than 0.");
            $stop;
        end
        if( width_out <= 0 )
        begin
            $display("Error! Value of width_out parameter must be greater than 0.");
            $stop;
        end
        if( extra_latency > width_out )
        begin
            $display("Info: Value of extra_latency parameter should be lower than width_out parameter for better performance/utilization.");
        end
        if( width_in > width_out )
        begin
            $display("Error! Value of width_in parameter should be lower than or equal to width_out.");
            $stop;
        end
        result = 0;
        cout_delayed = 0;
        overflow = 0;
        head = 0;
        result_int = 0;
        for (i = 0; i <= extra_latency; i = i +1)
        begin
            result_pipe [i] = 0;
        end
    end
    always @(posedge clock or posedge aclr_int)
    begin
        if (aclr_int == 1)
        begin
            result_int = 0;
            result = 0;
            overflow = 0;
            cout_delayed = 0;
            for (i = 0; i <= extra_latency; i = i +1)
            begin
                result_pipe [i] = 0;
            end
        end
        else
        begin
            if (clken_int == 1)
            begin
                if (extra_latency > 0)
                begin
                    result_pipe [head] = {
                                            result_int [width_out+1],
                                            {cout_int_wire, result_int [width_out-1:0]}
                                        };
                    head = (head + 1) % (extra_latency);
                    result_full = result_pipe [head];
                    cout_delayed = result_full [width_out];
                    result = result_full [width_out-1:0];
                    overflow = result_full [width_out+1];
                end
                else
                begin
                    result = temp_sum_wire;
                    overflow = overflow_int_wire;
                end
                result_int = {overflow_int_wire, {cout_int_wire, temp_sum_wire [width_out-1:0]}};
            end
        end
    end
    always @ (data or cin or add_sub_int or sign_data_int or
                result_int_wire [width_out -1:0] or sload_int)
    begin
        if ((lpm_representation == "SIGNED") || (sign_data_int == 1))
        begin
            zeropad = (data [width_in-1] ==0) ? 0 : -1;
        end
        else
        begin
            zeropad = 0;
        end
        fb_int = (sload_int == 1'b1) ? 0 : result_int_wire [width_out-1:0];
        data_int = {zeropad, data};
        if ((add_sub_int == 1) || (sload_int == 1))
        begin
            cin_int = ((sload_int == 1'b1) ? 0 : ((cin === 1'bz) ? 0 : cin));
            temp_sum = fb_int + data_int + cin_int;
            cout_int = temp_sum [width_out];
        end
        else
        begin
            cin_int = (cin === 1'bz) ? 1 : cin;
            borrow = ~cin_int;
            temp_sum = fb_int - data_int - borrow;
            result_full2 = data_int + borrow;
            cout_int = (fb_int >= result_full2) ? 1 : 0;
        end
        if ((lpm_representation == "SIGNED") || (sign_data_int == 1))
        begin
            a = (data [width_in-1] ~^ fb_int [width_out-1]) ^ (~add_sub_int);
            overflow_int = a & (fb_int [width_out-1] ^ temp_sum[width_out-1]);
        end
        else
        begin
            overflow_int = (add_sub_int == 1) ? cout_int : ~cout_int;
        end
        if (sload_int == 1)
        begin
            cout_int = !add_sub_int;
            overflow_int = 0;
        end
    end
    assign sign_data_int = sign_data;
    assign sload_int =  sload;
    assign add_sub_int = add_sub;
    assign clken_int = clken;
    assign aclr_int = aclr;
    assign result_int_wire = result_int;
    assign temp_sum_wire = temp_sum;
    assign cout_int_wire = cout_int;
    assign overflow_int_wire = overflow_int;
    assign cout = (extra_latency == 0) ? cout_int_wire : cout_delayed_wire;
    assign cout_delayed_wire = cout_delayed;
endmodule

