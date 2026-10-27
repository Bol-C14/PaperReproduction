`timescale 1ns/1ps

module altsqrt (
    radical,  
    clk,      
    ena,      
    aclr,     
    q,        
    remainder 
);
    parameter q_port_width = 1; 
    parameter r_port_width = 1; 
    parameter width = 1;        
    parameter pipeline = 0;     
    parameter lpm_hint= "UNUSED";
    parameter lpm_type = "altsqrt";
    input [width - 1 : 0] radical;
    input clk;
    input ena;
    input aclr;
    output [q_port_width - 1 : 0] q;
    output [r_port_width - 1 : 0] remainder;
    reg[q_port_width - 1 : 0] q_temp;
    reg[q_port_width - 1 : 0] q_pipeline[(pipeline +1) : 0];
    reg[r_port_width - 1 : 0] r_temp;
    reg[r_port_width - 1 : 0] remainder_pipeline[(pipeline +1) : 0];
    tri1 clk;
    tri1 ena;
    tri0 aclr;
    integer value1;
    integer value2;
    integer index;
    integer q_index;
    integer q_value_temp;
    integer r_value_temp;
    integer i1;
    integer pipe_ptr;
    initial
    begin : INITIALIZE
        if(width < 1)
        begin
            $display("width (%d) must be greater than 0.(ERROR)", width);
            $finish;
        end
        pipe_ptr = 0;
    end 
    always @(radical)
    begin : SQUARE_ROOT
        value1 = 0;
        value2 = 0;
        q_index = (width - 1) / 2;
        q_value_temp = 0;
        r_value_temp = 0;
        q_temp = {q_port_width{1'b0}};
        r_temp = {r_port_width{1'b0}};
        if((width % 2) == 1)
        begin
            index = width + 1;
            value1 = 0;
            value2 = (radical[index - 2] === 1'b1) ? 1'b1 : 1'b0;
        end
        else if (width > 1)
        begin
            index = width;
            value1 = (radical[index - 1] === 1'b1) ? 1'b1 : 1'b0;
            value2 = (radical[index - 2] === 1'b1) ? 1'b1 : 1'b0;
        end
        for(index = index - 2; index >= 0; index = index - 2)
        begin
            r_value_temp =  (r_value_temp * 4) + (2 * value1) + value2;
            if (r_value_temp >= ((4 * q_value_temp)  + 1))
            begin
                r_value_temp = r_value_temp - (4 * q_value_temp)  - 1;
                q_value_temp = (2 * q_value_temp) + 1;
                q_temp[q_index] = 1'b1;
            end
            else  
            begin
                q_value_temp = 2 * q_value_temp;
                q_temp[q_index] = 1'b0;
            end
            if(index >= 2)
            begin
                value1 = (radical[index - 1] === 1'b1)? 1: 0;
                value2 = (radical[index - 2] === 1'b1)? 1: 0;
            end
            q_index = q_index - 1;
        end
        r_temp = r_value_temp;
    end
    always @(posedge clk or posedge aclr)
    begin
        if (aclr) 
        begin
            for (i1 = 0; i1 < (pipeline + 1); i1 = i1 + 1)
            begin
                q_pipeline[i1] <= 0;
                remainder_pipeline[i1] <= 0;
            end
        end
        else if (ena == 1)
        begin          
            remainder_pipeline[pipe_ptr] <= r_temp;
            q_pipeline[pipe_ptr] <= q_temp;
            if (pipeline > 1)
                pipe_ptr <= (pipe_ptr + 1) % pipeline;
        end
    end
    assign q = (pipeline > 0) ? q_pipeline[pipe_ptr] : q_temp;
    assign remainder = (pipeline > 0) ? remainder_pipeline[pipe_ptr] : r_temp;
endmodule
