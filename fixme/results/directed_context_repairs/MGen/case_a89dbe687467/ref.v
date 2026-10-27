`timescale 1ns/1ps
 
module ref_alt_exc_dpram (portadatain,
                ref_portadataout,
                portaaddr,
                portawe,
                portaena,
                portaclk,
                portbdatain,
                ref_portbdataout,
                portbaddr,
                portbwe,
                portbena,
                portbclk
                );
    parameter   operation_mode = "SINGLE_PORT" ;
    parameter   addrwidth      = 14            ;
    parameter   width          = 32            ;
    parameter   depth          = 16384         ;
    parameter   ramblock       = 65535         ;
    parameter   output_mode    = "UNREG"       ;
    parameter   lpm_file       = "NONE"        ;
    parameter lpm_type = "alt_exc_dpram";
    parameter   lpm_hint       = "UNUSED";
    reg [width-1:0]        dpram_content[depth-1:0];
    input                   portawe           ,
                            portbwe           ,
                            portaena          ,
                            portbena          ,
                            portaclk          ,
                            portbclk          ;
    input  [width-1:0]     portadatain       ;
    input  [width-1:0]     portbdatain       ;
    input  [addrwidth-1:0]   portaaddr         ;
    input  [addrwidth-1:0]   portbaddr         ;
    output [width-1:0]      ref_portadataout      ,
                            ref_portbdataout      ;
    reg                    portaclk_in_last  ;
    reg                    portbclk_in_last  ;
    wire                   portaclk_in       ;
    wire                   portbclk_in       ;
    wire                   portawe_in        ;
    wire                   portbwe_in        ;
    wire                   portaena_in       ;
    wire                   portbena_in       ;
    wire   [width-1:0]     portadatain_in    ;
    wire   [width-1:0]     portbdatain_in    ;
    wire   [width-1:0]     portadatain_tmp   ;
    wire   [width-1:0]     portbdatain_tmp   ;
    wire   [addrwidth-1:0]   portaaddr_in      ;
    wire   [addrwidth-1:0]   portbaddr_in      ;
    reg    [width-1:0]     portadataout_tmp  ;
    reg    [width-1:0]     portbdataout_tmp  ;
    reg    [width-1:0]     portadataout_reg  ;
    reg    [width-1:0]     portbdataout_reg  ;
    reg    [width-1:0]     portadataout_reg_out  ;
    reg    [width-1:0]     portbdataout_reg_out  ;
    wire   [width-1:0]     portadataout_tmp2 ;
    wire   [width-1:0]     portbdataout_tmp2 ;
    reg                    portawe_latched   ;
    reg                    portbwe_latched   ;
    reg    [addrwidth-1:0]   portaaddr_latched ;
    reg    [addrwidth-1:0]   portbaddr_latched ;
    assign portadatain_in = portadatain;
    assign portaaddr_in   = portaaddr;
    assign portaena_in    = portaena;
    assign portaclk_in    = portaclk;
    assign portawe_in     = portawe;
    assign portbdatain_in = portbdatain;
    assign portbaddr_in   = portbaddr;
    assign portbena_in    = portbena;
    assign portbclk_in    = portbclk;
    assign portbwe_in     = portbwe;
    initial
    begin
        if (lpm_file != "NONE" && lpm_file != "none") $readmemh(lpm_file, dpram_content);
        portaclk_in_last = 0;
        portbclk_in_last = 0;
    end
    always @(portaclk_in)
    begin
        if (portaclk_in != 0 && portaclk_in_last == 0)  
        begin
            portawe_latched   = portawe_in   ;
            portaaddr_latched = portaaddr_in ;
            if (portawe_latched == 'b0)
            begin
                if (portaaddr_latched == portbaddr_latched && portbwe_latched != 'b0)
                begin
                    portadataout_reg = portadataout_tmp;
                    portadataout_tmp = 'bx;
                end
                else
                begin
                    portadataout_reg = portadataout_tmp;
                    portadataout_tmp = dpram_content[portaaddr_latched];
                end
            end
            else
            begin
                if (portaaddr_latched == portbaddr_latched && portawe_latched != 'b0 && portbwe_latched != 'b0)
                begin
                    portadataout_reg                 = portadataout_tmp ;
                    dpram_content[portaaddr_latched] = 'bx              ;
                    portadataout_tmp                 = 'bx              ;
                end
                else
                begin
                    portadataout_reg                 = portadataout_tmp;
                    dpram_content[portaaddr_latched] = portadatain_tmp ;
                    portadataout_tmp                 = 'bx             ;
                end
            end 
        end 
        portaclk_in_last = portaclk_in;
    end 
    always @(portbclk_in)
    begin
        if (portbclk_in != 0 && portbclk_in_last == 0 && (operation_mode == "DUAL_PORT" || operation_mode == "dual_port"))  
        begin
            portbwe_latched   = portbwe_in   ;
            portbaddr_latched = portbaddr_in ;
            if (portbwe_latched == 'b0)
            begin
                if (portbaddr_latched == portaaddr_latched && portawe_latched != 'b0)
                begin
                    portbdataout_reg = portbdataout_tmp;
                    portbdataout_tmp = 'bx;
                end
                else
                begin
                    portbdataout_reg = portbdataout_tmp;
                    portbdataout_tmp = dpram_content[portbaddr_latched];
                end
            end
            else
            begin
                if (portbaddr_latched == portaaddr_latched && portbwe_latched != 'b0 && portawe_latched != 'b0)
                begin
                    portbdataout_reg                 = portbdataout_tmp ;
                    dpram_content[portbaddr_latched] = 'bx              ;
                    portbdataout_tmp                 = 'bx              ;
                end
                else
                begin
                    portbdataout_reg                 = portbdataout_tmp;
                    dpram_content[portbaddr_latched] = portbdatain_tmp ;
                    portbdataout_tmp                 = 'bx             ;
                end
            end 
        end 
        portbclk_in_last = portbclk_in;
    end 
    always @(portaena_in or portadataout_reg)
    begin
        if (output_mode == "REG" || output_mode == "reg")
            if ( portaena_in == 1'b1 )
                portadataout_reg_out = portadataout_reg ;
    end
    always @(portbena_in or portbdataout_reg)
    begin
        if (output_mode == "REG" || output_mode == "reg")
            if ( portbena_in == 1'b1 )
                portbdataout_reg_out = portbdataout_reg ;
    end
    assign portadataout_tmp2 = (output_mode == "REG" || output_mode == "reg") ? portadataout_reg_out[width-1:0] : portadataout_tmp[width-1:0];
    assign portbdataout_tmp2 = (output_mode == "REG" || output_mode == "reg") ? portbdataout_reg_out[width-1:0] : portbdataout_tmp[width-1:0];
    assign portadatain_tmp[width-1:0] = portadatain;
    assign portbdatain_tmp[width-1:0] = portbdatain;
    assign ref_portadataout = portadataout_tmp2;
    assign ref_portbdataout = portbdataout_tmp2;
endmodule

