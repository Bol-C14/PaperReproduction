`timescale 1ns/1ps
 
module ref_altfp_mult (
    clock,      
    clk_en,     
    aclr,       
    dataa,      
    datab,      
    ref_result,     
    ref_overflow,   
    ref_underflow,  
    ref_zero,       
    ref_denormal,   
    ref_indefinite, 
    ref_nan         
);
    parameter width_exp = 8;
    parameter width_man = 23;
    parameter dedicated_multiplier_circuitry = "AUTO";
    parameter reduced_functionality = "NO";
    parameter pipeline = 5;
    parameter lpm_hint = "UNUSED";
    parameter lpm_type = "altfp_mult";
    parameter LATENCY = pipeline -1;
    parameter WIDTH_MAN_EXP = width_exp + width_man;
    input [WIDTH_MAN_EXP : 0] dataa;
    input [WIDTH_MAN_EXP : 0] datab;
    input clock;
    input clk_en;
    input aclr;
    output [WIDTH_MAN_EXP : 0] ref_result;
    output ref_overflow;
    output ref_underflow;
    output ref_zero;
    output ref_denormal;
    output ref_indefinite;
    output ref_nan;
    reg[width_man : 0] mant_dataa;
    reg[width_man : 0] mant_datab;
    reg[(2 * width_man) + 1 : 0] mant_ref_result;
    reg cout;
    reg ref_zero_mant_dataa;
    reg ref_zero_mant_datab;
    reg ref_zero_dataa;
    reg ref_zero_datab;
    reg inf_dataa;
    reg inf_datab;
    reg ref_nan_dataa;
    reg ref_nan_datab;
    reg den_dataa;
    reg den_datab;
    reg no_multiply;
    reg mant_ref_result_msb;
    reg no_rounding;
    reg sticky_bit;
    reg round_bit;
    reg guard_bit;
    reg carry;
    reg[WIDTH_MAN_EXP : 0] ref_result_pipe[LATENCY : 0];
    reg[LATENCY : 0] ref_overflow_pipe;
    reg[LATENCY : 0] ref_underflow_pipe;
    reg[LATENCY : 0] ref_zero_pipe;
    reg[LATENCY : 0] ref_denormal_pipe;
    reg[LATENCY : 0] ref_indefinite_pipe;
    reg[LATENCY : 0] ref_nan_pipe;
    reg[WIDTH_MAN_EXP : 0] temp_ref_result;
    reg ref_overflow_bit;
    reg ref_underflow_bit;
    reg ref_zero_bit;
    reg ref_denormal_bit;
    reg ref_indefinite_bit;
    reg ref_nan_bit;
    tri1 clk_en;
    tri0 aclr;
    integer exp_dataa;
    integer exp_datab;
    integer exp_ref_result;
    integer i0;
    integer i1;
    integer i2;
    integer i3;
    integer i4;
    integer i5;
    task add_bits;
        input  [width_man : 0] val1;
        inout  [(2 * width_man) + 1 : 0] temp_mant_ref_result;
        output cout; 
        reg co; 
        begin
            co = 1'b0;
            for(i0 = 0; i0 <= width_man; i0 = i0 + 1)
            begin
                if (co == 1'b0)
                begin
                    if (val1[i0] != temp_mant_ref_result[i0 + width_man + 1])
                    begin
                        temp_mant_ref_result[i0 + width_man + 1] = 1'b1;
                    end
                    else
                    begin
                        co = val1[i0] & temp_mant_ref_result[i0 + width_man + 1];
                        temp_mant_ref_result[i0 + width_man + 1] = 1'b0;
                    end
                end
                else 
                begin
                    co = val1[i0] | temp_mant_ref_result[i0 + width_man + 1];
                    if (val1[i0] != temp_mant_ref_result[i0 + width_man + 1])
                    begin
                        temp_mant_ref_result[i0 + width_man + 1] = 1'b0;
                    end
                    else
                    begin
                        temp_mant_ref_result[i0 + width_man + 1] = 1'b1;
                    end
                end
            end 
            cout = co;
        end
    endtask 
    function bit_all_0;
        input [(2 * width_man) + 1: 0] val;
        input index1;
        integer index1;
        input index2;
        integer index2;
        reg all_0;  
        begin
            begin : LOOP_1
                all_0 = 1'b1;
                for (i1 = index1; i1 <= index2; i1 = i1 + 1)
                begin
                    if ((val[i1]) == 1'b1)
                    begin
                        all_0 = 1'b0;
                        disable LOOP_1;  
                    end
                end
            end
            bit_all_0 = all_0;
        end
    endfunction 
    function integer exponential_value;
        input base_number;
        input exponent_number;
        integer base_number;
        integer exponent_number;
        integer value; 
        begin
            value = 1;
            for (i2 = 0; i2 < exponent_number; i2 = i2 + 1)
            begin
                value = base_number * value;
            end
            exponential_value = value;
        end
    endfunction 
    initial
    begin : INITIALIZATION
        for(i3 = LATENCY; i3 >= 0; i3 = i3 - 1)
        begin
            ref_result_pipe[i3] = 0;
            ref_overflow_pipe[i3] = 1'b0;
            ref_underflow_pipe[i3] = 1'b0;
            ref_zero_pipe[i3] = 1'b0;
            ref_denormal_pipe[i3] = 1'b0;
            ref_indefinite_pipe[i3] = 1'b0;
            ref_nan_pipe[i3] = 1'b0;
        end
        if (WIDTH_MAN_EXP >= 64)
        begin
            $display("ERROR: The sum of width_exp(%d) and width_man(%d) must be less 64!", width_exp, width_man);
            $finish;
        end
        if (width_exp < 8)
        begin
            $display("ERROR: width_exp(%d) must be at least 8!", width_exp);
            $finish;
        end
        if (width_man < 23)
        begin
            $display("ERROR: width_man(%d) must be at least 23!", width_man);
            $finish;
        end
        if (~((width_exp >= 11) || ((width_exp == 8) && (width_man == 23))))
        begin
            $display("ERROR: Found width_exp(%d) inside the range of Single Precision. width_exp must be 8 and width_man must be 23 for Single Presicion!", width_exp);
            $finish;
        end
        if (~((width_man >= 31) || ((width_exp == 8) && (width_man == 23))))
        begin
            $display("ERROR: Found width_man(%d) inside the range of Single Precision. width_exp must be 8 and width_man must be 23 for Single Presicion!", width_man);
            $finish;
        end
        if (width_exp >= width_man)
        begin
            $display("ERROR: width_exp(%d) must be less than width_man(%d)!", width_exp, width_man);
            $finish;
        end
        if ((pipeline != 5) && (pipeline != 6))
        begin
            $display("ERROR: The legal value for PIPELINE is 5 or 6!");
            $finish;
        end
        if ((reduced_functionality != "NO") && (reduced_functionality != "YES"))
        begin
            $display("ERROR: reduced_functionality value must be \"YES\" or \"NO\"!");
            $finish;
        end
        if (reduced_functionality != "NO")
        begin
            $display("Info: The Clearbox support is available for reduced functionality Floating Point Multiplier.");
        end
    end 
    always @(dataa or datab)
    begin : MULTIPLY_FP
        temp_ref_result = {(WIDTH_MAN_EXP + 1){1'b0}};
        ref_overflow_bit = 1'b0;
        ref_underflow_bit = 1'b0;
        ref_zero_bit = 1'b0;
        ref_denormal_bit = 1'b0;
        ref_indefinite_bit = 1'b0;
        ref_nan_bit = 1'b0;            
        mant_ref_result = {((2 * width_man) + 2){1'b0}};
        exp_dataa = 0;
        exp_datab = 0;
        exp_dataa = dataa[width_exp + width_man -1:width_man];
        exp_datab = datab[width_exp + width_man -1:width_man];
        ref_zero_mant_dataa = 1'b1;
        begin : LOOP_3
            for (i4 = 0; i4 <= width_man - 1; i4 = i4 + 1)
            begin
                if ((dataa[i4]) == 1'b1)
                begin
                    ref_zero_mant_dataa = 1'b0;
                    disable LOOP_3;
                end
            end
        end 
        ref_zero_mant_datab = 1'b1;
        begin : LOOP_4
            for (i4 = 0; i4 <= width_man -1; i4 = i4 + 1)
            begin
                if ((datab[i4]) == 1'b1)
                begin
                    ref_zero_mant_datab = 1'b0;
                    disable LOOP_4;
                end
            end
        end 
        ref_zero_dataa = 1'b0;
        den_dataa = 1'b0;
        inf_dataa = 1'b0;
        ref_nan_dataa = 1'b0;
        if (exp_dataa == 0)
        begin
            if ((ref_zero_mant_dataa == 1'b1)
                || (reduced_functionality != "NO"))
            begin
                ref_zero_dataa = 1'b1;  
            end
            else
            begin
                den_dataa = 1'b1; 
            end
        end
        else if (exp_dataa == (exponential_value(2, width_exp) - 1))
        begin
            if (ref_zero_mant_dataa == 1'b1)
            begin
                inf_dataa = 1'b1;  
            end
            else
            begin
                ref_nan_dataa = 1'b1; 
            end
        end
        ref_zero_datab = 1'b0;
        den_datab = 1'b0;
        inf_datab = 1'b0;
        ref_nan_datab = 1'b0;
        if (exp_datab == 0)
        begin
            if ((ref_zero_mant_datab == 1'b1)
                || (reduced_functionality != "NO"))
            begin
                ref_zero_datab = 1'b1; 
            end
            else
            begin
                den_datab = 1'b1; 
            end
        end
        else if (exp_datab == (exponential_value(2, width_exp) - 1))
        begin
            if (ref_zero_mant_datab == 1'b1)
            begin
                inf_datab = 1'b1; 
            end
            else
            begin
                ref_nan_datab = 1'b1; 
            end
        end
        no_multiply = 1'b0;
        if (ref_nan_dataa || ref_nan_datab || (inf_dataa && ref_zero_datab) ||
            (inf_datab && ref_zero_dataa))
        begin
            ref_nan_bit = 1'b1; 
            for (i4 = width_man - 1; i4 <= WIDTH_MAN_EXP - 1; i4 = i4 + 1)
            begin
                temp_ref_result[i4] = 1'b1;
            end
            no_multiply = 1'b1; 
        end
        else if (ref_zero_dataa)
        begin
            ref_zero_bit = 1'b1; 
            temp_ref_result[WIDTH_MAN_EXP : 0] = 0;
            no_multiply = 1'b1;
        end
        else if (ref_zero_datab)
        begin
            ref_zero_bit = 1'b1; 
            temp_ref_result[WIDTH_MAN_EXP : 0] = 0;
            no_multiply = 1'b1;
        end
        else if (inf_dataa)
        begin
            ref_overflow_bit = 1'b1; 
            temp_ref_result[WIDTH_MAN_EXP : 0] = dataa;
            no_multiply = 1'b1;
        end
        else if (inf_datab)
        begin
            ref_overflow_bit = 1'b1; 
            temp_ref_result[WIDTH_MAN_EXP : 0] = datab;
            no_multiply = 1'b1;
        end
        if (no_multiply == 1'b0)
        begin
            exp_ref_result = exp_dataa + exp_datab - (exponential_value(2, width_exp -1) -1);
            mant_dataa[width_man : 0] = {1'b1, dataa[width_man -1 : 0]};
            mant_datab[width_man : 0] = {1'b1, datab[width_man -1 : 0]};
            for (i4 = 0; i4 <= width_man; i4 = i4 + 1)
            begin
                cout = 1'b0;
                if ((mant_dataa[i4]) == 1'b1)
                begin
                    add_bits(mant_datab, mant_ref_result, cout);
                end
                mant_ref_result = mant_ref_result >> 1;
                mant_ref_result[2*width_man + 1] = cout;
            end
            sticky_bit = 1'b0;
            mant_ref_result_msb = mant_ref_result[2*width_man + 1];
            if (mant_ref_result_msb == 1'b1)
            begin
                sticky_bit = mant_ref_result[0]; 
                mant_ref_result = mant_ref_result >> 1;
                exp_ref_result = exp_ref_result + 1;
            end
            round_bit = mant_ref_result[width_man - 1];
            guard_bit = mant_ref_result[width_man];
            no_rounding = 1'b0;
            if (round_bit == 1'b0)
            begin
                no_rounding = 1'b1; 
            end
            else
            begin
                if (reduced_functionality == "NO")
                begin
                    for(i4 = 0; i4 <= width_man - 2; i4 = i4 + 1)
                    begin
                        sticky_bit = sticky_bit | mant_ref_result[i4];
                    end
                end
                else
                begin
                    sticky_bit = (mant_ref_result[width_man - 2] &
                                    mant_ref_result_msb);
                end
                if ((sticky_bit == 1'b0) && (guard_bit == 1'b0))
                begin
                    no_rounding = 1'b1;
                end
            end
            if (no_rounding == 1'b0)
            begin
                carry = 1'b1;
                for(i4 = width_man; i4 <= 2 * width_man + 1; i4 = i4 + 1)
                begin
                    if (carry == 1'b1)
                    begin
                        if (mant_ref_result[i4] == 1'b0)
                        begin
                            mant_ref_result[i4] = 1'b1;
                            carry = 1'b0;
                        end
                        else
                        begin
                            mant_ref_result[i4] = 1'b0;
                        end
                    end
                end
                if (mant_ref_result[(2 * width_man) + 1] == 1'b1)
                begin
                    mant_ref_result = mant_ref_result >> 1;
                    exp_ref_result = exp_ref_result + 1;
                end
            end
            if ((!bit_all_0(mant_ref_result, 0, (2 * width_man) + 1)) &&
                (mant_ref_result[2 * width_man] == 1'b0))
            begin
                while ((mant_ref_result[2 * width_man] == 1'b0) &&
                        (exp_ref_result != 0))
                begin
                    mant_ref_result = mant_ref_result << 1;
                    exp_ref_result = exp_ref_result - 1;
                end
            end
            else if ((exp_ref_result < 0) && (exp_ref_result >= -(2*width_man)))
            begin
                while(exp_ref_result != 0)
                begin
                    mant_ref_result = mant_ref_result >> 1;
                    exp_ref_result = exp_ref_result + 1;
                end
            end
            if (den_dataa || den_datab)
            begin
                ref_indefinite_bit = 1'b1; 
            end
            else if (exp_ref_result >= (exponential_value(2, width_exp) -1))
            begin
                ref_overflow_bit = 1'b1; 
            end
            else if (exp_ref_result < 0)
            begin
                ref_underflow_bit = 1'b1; 
                ref_zero_bit = 1'b1; 
            end
            else if (exp_ref_result == 0)
            begin
                ref_underflow_bit = 1'b1; 
                if (bit_all_0(mant_ref_result, width_man + 1, 2 * width_man))
                begin
                    ref_zero_bit = 1'b1; 
                end
                else
                begin
                    ref_denormal_bit = 1'b1; 
                end
            end
            if (exp_ref_result < 0) 
            begin
                for(i4 = 0; i4 <= width_man - 1; i4 = i4 + 1)
                begin
                    temp_ref_result[i4] = 1'b0;
                end
            end
            else if (exp_ref_result == 0) 
            begin
                if (reduced_functionality == "NO")
                begin
                    temp_ref_result[width_man - 1 : 0] = mant_ref_result[2 * width_man : width_man + 1];
                end
                else
                begin
                    temp_ref_result[width_man - 1 : 0] = 0;
                end
            end
            else if (exp_ref_result >= exponential_value(2, width_exp) -1)
            begin
                temp_ref_result[width_man - 1 : 0] = {width_man{1'b0}};
            end
            else 
            begin
                temp_ref_result[width_man - 1 : 0] = mant_ref_result[(2 * width_man - 1) : width_man];
            end
            if (exp_ref_result == 0)
            begin
                for(i4 = width_man; i4 <= WIDTH_MAN_EXP - 1; i4 = i4 + 1)
                begin
                    temp_ref_result[i4] = 1'b0;
                end
            end
            else if (exp_ref_result >= (exponential_value(2, width_exp) -1))
            begin
                for(i4 = width_man; i4 <= WIDTH_MAN_EXP - 1; i4 = i4 + 1)
                begin
                    temp_ref_result[i4] = 1'b1;
                end
            end
            else
            begin
                for(i4 = width_man; i4 <= WIDTH_MAN_EXP - 1; i4 = i4 + 1)
                begin
                    if ((exp_ref_result % 2) == 1)
                    begin
                        temp_ref_result[i4] = 1'b1;
                    end
                    else
                    begin
                        temp_ref_result[i4] = 1'b0;
                    end
                    exp_ref_result = exp_ref_result / 2;
                end
            end
        end 
        temp_ref_result[WIDTH_MAN_EXP] = dataa[WIDTH_MAN_EXP] ^ datab[WIDTH_MAN_EXP];
    end 
    always @(posedge clock or posedge aclr)
    begin : PIPELINE_REGS
        if (aclr == 1'b1)
        begin
            for (i5 = LATENCY; i5 >= 0; i5 = i5 - 1)
            begin
                ref_result_pipe[i5] <= {WIDTH_MAN_EXP{1'b0}};
                ref_overflow_pipe[i5] <= 1'b0;
                ref_underflow_pipe[i5] <= 1'b0;
                ref_zero_pipe[i5] <= 1'b1;
                ref_denormal_pipe[i5] <= 1'b0;
                ref_indefinite_pipe[i5] <= 1'b0;
                ref_nan_pipe[i5] <= 1'b0;
            end
        end
        else if (clk_en == 1'b1)
        begin
            ref_result_pipe[0] <= temp_ref_result;
            ref_overflow_pipe[0] <= ref_overflow_bit;
            ref_underflow_pipe[0] <= ref_underflow_bit;
            ref_zero_pipe[0] <= ref_zero_bit;
            ref_denormal_pipe[0] <= ref_denormal_bit;
            ref_indefinite_pipe[0] <= ref_indefinite_bit;
            ref_nan_pipe[0] <= ref_nan_bit;
            for(i5=LATENCY; i5 >= 1; i5 = i5 - 1)
            begin
                ref_result_pipe[i5] <= ref_result_pipe[i5 - 1];
                ref_overflow_pipe[i5] <= ref_overflow_pipe[i5 - 1];
                ref_underflow_pipe[i5] <= ref_underflow_pipe[i5 - 1];
                ref_zero_pipe[i5] <= ref_zero_pipe[i5 - 1];
                ref_denormal_pipe[i5] <= ref_denormal_pipe[i5 - 1];
                ref_indefinite_pipe[i5] <= ref_indefinite_pipe[i5 - 1];
                ref_nan_pipe[i5] <= ref_nan_pipe[i5 - 1];
            end
        end
    end 
assign ref_result = ref_result_pipe[LATENCY];
assign ref_overflow = ref_overflow_pipe[LATENCY];
assign ref_underflow = ref_underflow_pipe[LATENCY];
assign ref_zero = (reduced_functionality == "NO") ? ref_zero_pipe[LATENCY] : 1'b0;
assign ref_denormal = (reduced_functionality == "NO") ? ref_denormal_pipe[LATENCY] : 1'b0;
assign ref_indefinite = (reduced_functionality == "NO") ? ref_indefinite_pipe[LATENCY] : 1'b0;
assign ref_nan = ref_nan_pipe[LATENCY];
endmodule

