`timescale 1ns/1ps

module flow_ctrl 
(
Reset               ,
Clk                 ,
tx_pause_en         ,
xoff_cpu            ,
xon_cpu             ,
pause_quanta        ,
pause_quanta_val    ,
pause_apply         ,
pause_quanta_sub    ,
xoff_gen            ,
xoff_gen_complete   ,
xon_gen             ,
xon_gen_complete    
);
input           Reset               ;
input           Clk                 ;
input           tx_pause_en         ;
input           xoff_cpu            ;
input           xon_cpu             ;
input   [15:0]  pause_quanta        ;
input           pause_quanta_val    ;
output          pause_apply         ;
input           pause_quanta_sub    ;
output          xoff_gen            ;
input           xoff_gen_complete   ;
output          xon_gen             ;
input           xon_gen_complete    ;
reg             xoff_cpu_dl1            ;
reg             xoff_cpu_dl2            ;
reg             xon_cpu_dl1             ;   
reg             xon_cpu_dl2             ;
reg [15:0]      pause_quanta_dl1        ;
reg             pause_quanta_val_dl1    ;
reg             pause_quanta_val_dl2    ;       
reg             pause_apply             ;
reg             xoff_gen                ;
reg             xon_gen                 ;
reg [15:0]      pause_quanta_counter    ;
reg             tx_pause_en_dl1         ;
reg             tx_pause_en_dl2         ;
always @ (posedge Clk or posedge Reset)
    if (Reset)
        begin
        xoff_cpu_dl1        <=0;
        xoff_cpu_dl2        <=0;
        end
    else
        begin
        xoff_cpu_dl1        <=xoff_cpu;
        xoff_cpu_dl2        <=xoff_cpu_dl1;
        end
always @ (posedge Clk or posedge Reset)
    if (Reset)
        begin
        xon_cpu_dl1     <=0;
        xon_cpu_dl2     <=0;
        end
    else
        begin
        xon_cpu_dl1     <=xon_cpu;
        xon_cpu_dl2     <=xon_cpu_dl1;
        end     
always @ (posedge Clk or posedge Reset)
    if (Reset)
        begin
        pause_quanta_dl1        <=0;
        end
    else
        begin
        pause_quanta_dl1        <=pause_quanta;
        end  
always @ (posedge Clk or posedge Reset)
    if (Reset)
        begin
        pause_quanta_val_dl1    <=0;
        pause_quanta_val_dl2    <=0;
        end
    else
        begin
        pause_quanta_val_dl1    <=pause_quanta_val;
        pause_quanta_val_dl2    <=pause_quanta_val_dl1;
        end                      
always @ (posedge Clk or posedge Reset)
    if (Reset)
        begin           
        tx_pause_en_dl1     <=0;
        tx_pause_en_dl2     <=0; 
        end
    else
        begin           
        tx_pause_en_dl1     <=tx_pause_en;
        tx_pause_en_dl2     <=tx_pause_en_dl1; 
        end     
always @ (posedge Clk or posedge Reset)
    if (Reset)
        xoff_gen        <=0;
    else if (xoff_gen_complete)
        xoff_gen        <=0;
    else if (xoff_cpu_dl1&&!xoff_cpu_dl2)
        xoff_gen        <=1;
always @ (posedge Clk or posedge Reset)
    if (Reset)
        xon_gen     <=0;
    else if (xon_gen_complete)
        xon_gen     <=0;
    else if (xon_cpu_dl1&&!xon_cpu_dl2)
        xon_gen     <=1;                     
always @ (posedge Clk or posedge Reset)
    if (Reset)
        pause_quanta_counter    <=0;
    else if(pause_quanta_val_dl1&&!pause_quanta_val_dl2)
        pause_quanta_counter    <=pause_quanta_dl1; 
    else if(pause_quanta_sub&&pause_quanta_counter!=0)
        pause_quanta_counter    <=pause_quanta_counter-1;
always @ (posedge Clk or posedge Reset)
    if (Reset)
        pause_apply     <=0;
    else if(pause_quanta_counter==0)
        pause_apply     <=0;
    else if (tx_pause_en_dl2)
        pause_apply     <=1;
endmodule
