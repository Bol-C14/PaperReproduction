`timescale 1ns/1ps

module ALTERA_MF_HINT_EVALUATION;
function [8*200:1] GET_PARAMETER_VALUE;
    input [8*200:1] given_string;  
    input [8*50:1] compare_param_name; 
    integer param_value_char_count; 
    integer param_name_char_count;  
    integer white_space_count;
    reg extract_param_value; 
    reg extract_param_name;  
    reg param_found; 
    reg include_white_space; 
    reg [8*200:1] reg_string; 
    reg [8*50:1] param_name;  
    reg [8*20:1] param_value; 
    reg [8:1] tmp; 
begin
    reg_string = given_string;
    param_value_char_count = 0;
    param_name_char_count =0;
    extract_param_value = 1;
    extract_param_name = 0;
    param_found = 0;
    include_white_space = 0;
    white_space_count = 0;
    tmp = reg_string[8:1];
    while ((tmp != 0 ) && (param_found != 1))
    begin
        tmp = reg_string[8:1];
        if((tmp != 32) || (include_white_space == 1))
        begin
            if(tmp == 32)
            begin
                white_space_count = 1;
            end
            else if(tmp == 61)  
            begin
                extract_param_value = 0;
                extract_param_name =  1;  
                include_white_space = 0;  
                white_space_count = 0;
                param_value = param_value >> (8 * (20 - param_value_char_count));
                param_value_char_count = 0;
            end
            else if (tmp == 44) 
            begin
                extract_param_value = 1; 
                extract_param_name =  0;
                param_name = param_name >> (8 * (50 - param_name_char_count));
                param_name_char_count = 0;
                if(param_name == compare_param_name)
                    param_found = 1;  
            end
            else
            begin
                if(extract_param_value == 1)
                begin
                    param_value_char_count = param_value_char_count + white_space_count + 1;
                    include_white_space = 1;
                    if(white_space_count > 0)
                    begin
                        param_value = {8'b100000, param_value[20*8:9]};
                        white_space_count = 0;
                    end
                    param_value = {tmp, param_value[20*8:9]};
                end
                else if(extract_param_name == 1)
                begin
                    param_name = {tmp, param_name[50*8:9]};
                    param_name_char_count = param_name_char_count + 1;
                end
            end
        end
        reg_string = reg_string >> 8;  
    end
    if(extract_param_name == 1)
    begin
        param_name = param_name >> (8 * (50 - param_name_char_count));
        if(param_name == compare_param_name)
            param_found = 1;
    end
    if (param_found == 1)
        GET_PARAMETER_VALUE = param_value;   
    else
        GET_PARAMETER_VALUE = "";  
end
endfunction
endmodule
