`timescale 1ns/1ps

module mt48lc8m16a2 (Dq, Addr, Ba, Clk, Cke, Cs_n, Ras_n, Cas_n, We_n, Dqm);
    parameter addr_bits =      12;
    parameter data_bits =      16;
    parameter col_bits  =       9;
    parameter mem_sizes = 2097151;                                  
    inout     [data_bits - 1 : 0] Dq;
    input     [addr_bits - 1 : 0] Addr;
    input                 [1 : 0] Ba;
    input                         Clk;
    input                         Cke;
    input                         Cs_n;
    input                         Ras_n;
    input                         Cas_n;
    input                         We_n;
    input                 [1 : 0] Dqm;
    reg       [data_bits - 1 : 0] Bank0 [0 : mem_sizes];
    reg       [data_bits - 1 : 0] Bank1 [0 : mem_sizes];
    reg       [data_bits - 1 : 0] Bank2 [0 : mem_sizes];
    reg       [data_bits - 1 : 0] Bank3 [0 : mem_sizes];
    reg                   [1 : 0] Bank_addr [0 : 3];                
    reg        [col_bits - 1 : 0] Col_addr [0 : 3];                 
    reg                   [3 : 0] Command [0 : 3];                  
    reg                   [1 : 0] Dqm_reg0, Dqm_reg1;               
    reg       [addr_bits - 1 : 0] B0_row_addr, B1_row_addr, B2_row_addr, B3_row_addr;
    reg       [addr_bits - 1 : 0] Mode_reg;
    reg       [data_bits - 1 : 0] Dq_reg, Dq_dqm;
    reg        [col_bits - 1 : 0] Col_temp, Burst_counter;
    reg                           Act_b0, Act_b1, Act_b2, Act_b3;   
    reg                           Pc_b0, Pc_b1, Pc_b2, Pc_b3;       
    reg                   [1 : 0] Bank_precharge     [0 : 3];       
    reg                           A10_precharge      [0 : 3];       
    reg                           Auto_precharge     [0 : 3];       
    reg                           Read_precharge     [0 : 3];       
    reg                           Write_precharge    [0 : 3];       
    integer                       Count_precharge    [0 : 3];       
    reg                           RW_interrupt_read  [0 : 3];       
    reg                           RW_interrupt_write [0 : 3];       
    reg                           Data_in_enable;
    reg                           Data_out_enable;
    reg                   [1 : 0] Bank, Previous_bank;
    reg       [addr_bits - 1 : 0] Row;
    reg        [col_bits - 1 : 0] Col, Col_brst;
    reg                           CkeZ, Sys_clk;
    wire      Active_enable    = ~Cs_n & ~Ras_n &  Cas_n &  We_n;
    wire      Aref_enable      = ~Cs_n & ~Ras_n & ~Cas_n &  We_n;
    wire      Burst_term       = ~Cs_n &  Ras_n &  Cas_n & ~We_n;
    wire      Mode_reg_enable  = ~Cs_n & ~Ras_n & ~Cas_n & ~We_n;
    wire      Prech_enable     = ~Cs_n & ~Ras_n &  Cas_n & ~We_n;
    wire      Read_enable      = ~Cs_n &  Ras_n & ~Cas_n &  We_n;
    wire      Write_enable     = ~Cs_n &  Ras_n & ~Cas_n & ~We_n;
    wire      Burst_length_1   = ~Mode_reg[2] & ~Mode_reg[1] & ~Mode_reg[0];
    wire      Burst_length_2   = ~Mode_reg[2] & ~Mode_reg[1] &  Mode_reg[0];
    wire      Burst_length_4   = ~Mode_reg[2] &  Mode_reg[1] & ~Mode_reg[0];
    wire      Burst_length_8   = ~Mode_reg[2] &  Mode_reg[1] &  Mode_reg[0];
    wire      Cas_latency_2    = ~Mode_reg[6] &  Mode_reg[5] & ~Mode_reg[4];
    wire      Cas_latency_3    = ~Mode_reg[6] &  Mode_reg[5] &  Mode_reg[4];
    wire      Write_burst_mode = Mode_reg[9];
    reg	      Debug;                         
    wire      Dq_chk           = Sys_clk & Data_in_enable;      
    assign    Dq               = Dq_reg;                        
    `define   ACT       0
    `define   NOP       1
    `define   READ      2
    `define   READ_A    3
    `define   WRITE     4
    `define   WRITE_A   5
    `define   PRECH     6
    `define   A_REF     7
    `define   BST       8
    `define   LMR       9
    parameter tAC  =   6.0;
    parameter tHZ  =   7.0;
    parameter tOH  =   2.7;
    parameter tMRD =   2.0;     
    parameter tRAS =  44.0;
    parameter tRC  =  66.0;
    parameter tRCD =  20.0;
    parameter tRP  =  20.0;
    parameter tRRD =  15.0;
    parameter tWRa =   7.5;     
    parameter tWRp =  15.0;     
    integer   MRD_chk;
    integer   WR_counter [0 : 3];
    time      WR_chk [0 : 3];
    time      RC_chk, RRD_chk;
    time      RAS_chk0, RAS_chk1, RAS_chk2, RAS_chk3;
    time      RCD_chk0, RCD_chk1, RCD_chk2, RCD_chk3;
    time      RP_chk0, RP_chk1, RP_chk2, RP_chk3;
    initial begin
       Debug = 1'b0;
        Dq_reg = {data_bits{1'bz}};
        {Data_in_enable, Data_out_enable} = 0;
        {Act_b0, Act_b1, Act_b2, Act_b3} = 4'b0000;
        {Pc_b0, Pc_b1, Pc_b2, Pc_b3} = 4'b0000;
        {WR_chk[0], WR_chk[1], WR_chk[2], WR_chk[3]} = 0;
        {WR_counter[0], WR_counter[1], WR_counter[2], WR_counter[3]} = 0;
        {RW_interrupt_read[0], RW_interrupt_read[1], RW_interrupt_read[2], RW_interrupt_read[3]} = 0;
        {RW_interrupt_write[0], RW_interrupt_write[1], RW_interrupt_write[2], RW_interrupt_write[3]} = 0;
        {MRD_chk, RC_chk, RRD_chk} = 0;
        {RAS_chk0, RAS_chk1, RAS_chk2, RAS_chk3} = 0;
        {RCD_chk0, RCD_chk1, RCD_chk2, RCD_chk3} = 0;
        {RP_chk0, RP_chk1, RP_chk2, RP_chk3} = 0;
        $timeformat (-9, 0, " ns", 12);
    end
    always begin
        @ (posedge Clk) begin
            Sys_clk = CkeZ;
            CkeZ = Cke;
        end
        @ (negedge Clk) begin
            Sys_clk = 1'b0;
        end
    end
    always @ (posedge Sys_clk) begin
        Command[0] = Command[1];
        Command[1] = Command[2];
        Command[2] = Command[3];
        Command[3] = `NOP;
        Col_addr[0] = Col_addr[1];
        Col_addr[1] = Col_addr[2];
        Col_addr[2] = Col_addr[3];
        Col_addr[3] = {col_bits{1'b0}};
        Bank_addr[0] = Bank_addr[1];
        Bank_addr[1] = Bank_addr[2];
        Bank_addr[2] = Bank_addr[3];
        Bank_addr[3] = 2'b0;
        Bank_precharge[0] = Bank_precharge[1];
        Bank_precharge[1] = Bank_precharge[2];
        Bank_precharge[2] = Bank_precharge[3];
        Bank_precharge[3] = 2'b0;
        A10_precharge[0] = A10_precharge[1];
        A10_precharge[1] = A10_precharge[2];
        A10_precharge[2] = A10_precharge[3];
        A10_precharge[3] = 1'b0;
        Dqm_reg0 = Dqm_reg1;
        Dqm_reg1 = Dqm;
        if (Auto_precharge[0] == 1'b1) begin
            Count_precharge[0] = Count_precharge[0] + 1;
        end
        if (Auto_precharge[1] == 1'b1) begin
            Count_precharge[1] = Count_precharge[1] + 1;
        end
        if (Auto_precharge[2] == 1'b1) begin
            Count_precharge[2] = Count_precharge[2] + 1;
        end
        if (Auto_precharge[3] == 1'b1) begin
            Count_precharge[3] = Count_precharge[3] + 1;
        end
        MRD_chk = MRD_chk + 1;
        WR_counter[0] = WR_counter[0] + 1;
        WR_counter[1] = WR_counter[1] + 1;
        WR_counter[2] = WR_counter[2] + 1;
        WR_counter[3] = WR_counter[3] + 1;
        if (Aref_enable == 1'b1) begin
            if (Debug) $display ("at time %t AREF : Auto Refresh", $time);
            if ($time - RC_chk < tRC) begin
                $display ("at time %t ERROR: tRC violation during Auto Refresh", $time);
            end
            if ($time - RP_chk0 < tRP || $time - RP_chk1 < tRP || $time - RP_chk2 < tRP || $time - RP_chk3 < tRP) begin
                $display ("at time %t ERROR: tRP violation during Auto Refresh", $time);
            end
            if (Pc_b0 == 1'b0 || Pc_b1 == 1'b0 || Pc_b2 == 1'b0 || Pc_b3 == 1'b0) begin
                $display ("at time %t ERROR: All banks must be Precharge before Auto Refresh", $time);
            end
            RC_chk = $time;
        end
        if (Mode_reg_enable == 1'b1) begin
            if (Pc_b0 == 1'b1 && Pc_b1 == 1'b1 && Pc_b2 == 1'b1 && Pc_b3 == 1'b1) begin
                Mode_reg = Addr;
                if (Debug) begin
                    $display ("at time %t LMR  : Load Mode Register", $time);
                    if (Addr[6 : 4] == 3'b010)
                        $display ("                            CAS Latency      = 2");
                    else if (Addr[6 : 4] == 3'b011)
                        $display ("                            CAS Latency      = 3");
                    else
                        $display ("                            CAS Latency      = Reserved");
                    if (Addr[2 : 0] == 3'b000)
                        $display ("                            Burst Length     = 1");
                    else if (Addr[2 : 0] == 3'b001)
                        $display ("                            Burst Length     = 2");
                    else if (Addr[2 : 0] == 3'b010)
                        $display ("                            Burst Length     = 4");
                    else if (Addr[2 : 0] == 3'b011)
                        $display ("                            Burst Length     = 8");
                    else if (Addr[3 : 0] == 4'b0111)
                        $display ("                            Burst Length     = Full");
                    else
                        $display ("                            Burst Length     = Reserved");
                    if (Addr[3] == 1'b0)
                        $display ("                            Burst Type       = Sequential");
                    else if (Addr[3] == 1'b1)
                        $display ("                            Burst Type       = Interleaved");
                    else
                        $display ("                            Burst Type       = Reserved");
                    if (Addr[9] == 1'b0)
                        $display ("                            Write Burst Mode = Programmed Burst Length");
                    else if (Addr[9] == 1'b1)
                        $display ("                            Write Burst Mode = Single Location Access");
                    else
                        $display ("                            Write Burst Mode = Reserved");
                end
            end else begin
                $display ("at time %t ERROR: all banks must be Precharge before Load Mode Register", $time);
            end
            if ($time - RC_chk < tRC) begin
                $display ("at time %t ERROR: tRC violation during Load Mode Register", $time);
            end
            if (MRD_chk < tMRD) begin
                $display ("at time %t ERROR: tMRD violation during Load Mode Register", $time);
            end
            MRD_chk = 0;
        end
        if (Active_enable == 1'b1) begin
            if (Ba == 2'b00 && Pc_b0 == 1'b1) begin
                {Act_b0, Pc_b0} = 2'b10;
                B0_row_addr = Addr [addr_bits - 1 : 0];
                RCD_chk0 = $time;
                RAS_chk0 = $time;
                if (Debug) $display ("at time %t ACT  : Bank = 0 Row = %d", $time, Addr);
                if ($time - RP_chk0 < tRP) begin
                   $display ("at time %t ERROR: tRP violation during Activate bank 0", $time);
                end
            end else if (Ba == 2'b01 && Pc_b1 == 1'b1) begin
                {Act_b1, Pc_b1} = 2'b10;
                B1_row_addr = Addr [addr_bits - 1 : 0];
                RCD_chk1 = $time;
                RAS_chk1 = $time;
                if (Debug) $display ("at time %t ACT  : Bank = 1 Row = %d", $time, Addr);
                if ($time - RP_chk1 < tRP) begin
                    $display ("at time %t ERROR: tRP violation during Activate bank 1", $time);
                end
            end else if (Ba == 2'b10 && Pc_b2 == 1'b1) begin
                {Act_b2, Pc_b2} = 2'b10;
                B2_row_addr = Addr [addr_bits - 1 : 0];
                RCD_chk2 = $time;
                RAS_chk2 = $time;
                if (Debug) $display ("at time %t ACT  : Bank = 2 Row = %d", $time, Addr);
                if ($time - RP_chk2 < tRP) begin
                    $display ("at time %t ERROR: tRP violation during Activate bank 2", $time);
                end
            end else if (Ba == 2'b11 && Pc_b3 == 1'b1) begin
                {Act_b3, Pc_b3} = 2'b10;
                B3_row_addr = Addr [addr_bits - 1 : 0];
                RCD_chk3 = $time;
                RAS_chk3 = $time;
                if (Debug) $display ("at time %t ACT  : Bank = 3 Row = %d", $time, Addr);
                if ($time - RP_chk3 < tRP) begin
                    $display ("at time %t ERROR: tRP violation during Activate bank 3", $time);
                end
            end else if (Ba == 2'b00 && Pc_b0 == 1'b0) begin
                $display ("at time %t ERROR: Bank 0 is not Precharged.", $time);
            end else if (Ba == 2'b01 && Pc_b1 == 1'b0) begin
                $display ("at time %t ERROR: Bank 1 is not Precharged.", $time);
            end else if (Ba == 2'b10 && Pc_b2 == 1'b0) begin
                $display ("at time %t ERROR: Bank 2 is not Precharged.", $time);
            end else if (Ba == 2'b11 && Pc_b3 == 1'b0) begin
                $display ("at time %t ERROR: Bank 3 is not Precharged.", $time);
            end
            if ((Previous_bank != Ba) && ($time - RRD_chk < tRRD)) begin
                $display ("at time %t ERROR: tRRD violation during Activate bank = %d", $time, Ba);
            end
            if (MRD_chk < tMRD ) begin
                $display ("at time %t ERROR: tMRD violation during Activate bank = %d", $time, Ba);
            end
            if ($time - RC_chk < tRC) begin
                $display ("at time %t ERROR: tRC violation during Activate bank = %d", $time, Ba);
            end
            RRD_chk = $time;
            Previous_bank = Ba;
        end
        if (Prech_enable == 1'b1) begin
            if (Addr[10] == 1'b1) begin
                {Pc_b0, Pc_b1, Pc_b2, Pc_b3} = 4'b1111;
                {Act_b0, Act_b1, Act_b2, Act_b3} = 4'b0000;
                RP_chk0 = $time;
                RP_chk1 = $time;
                RP_chk2 = $time;
                RP_chk3 = $time;
                if (Debug) $display ("at time %t PRE  : Bank = ALL",$time);
                if (($time - RAS_chk0 < tRAS) || ($time - RAS_chk1 < tRAS) ||
                    ($time - RAS_chk2 < tRAS) || ($time - RAS_chk3 < tRAS)) begin
                    $display ("at time %t ERROR: tRAS violation during Precharge all bank", $time);
                end
                if (($time - WR_chk[0] < tWRp) || ($time - WR_chk[1] < tWRp) ||
                    ($time - WR_chk[2] < tWRp) || ($time - WR_chk[3] < tWRp)) begin
                    $display ("at time %t ERROR: tWR violation during Precharge all bank", $time);
                end
            end else if (Addr[10] == 1'b0) begin
                if (Ba == 2'b00) begin
                    {Pc_b0, Act_b0} = 2'b10;
                    RP_chk0 = $time;
                    if (Debug) $display ("at time %t PRE  : Bank = 0",$time);
                    if ($time - RAS_chk0 < tRAS) begin
                        $display ("at time %t ERROR: tRAS violation during Precharge bank 0", $time);
                    end
                end else if (Ba == 2'b01) begin
                    {Pc_b1, Act_b1} = 2'b10;
                    RP_chk1 = $time;
                    if (Debug) $display ("at time %t PRE  : Bank = 1",$time);
                    if ($time - RAS_chk1 < tRAS) begin
                        $display ("at time %t ERROR: tRAS violation during Precharge bank 1", $time);
                    end
                end else if (Ba == 2'b10) begin
                    {Pc_b2, Act_b2} = 2'b10;
                    RP_chk2 = $time;
                    if (Debug) $display ("at time %t PRE  : Bank = 2",$time);
                    if ($time - RAS_chk2 < tRAS) begin
                        $display ("at time %t ERROR: tRAS violation during Precharge bank 2", $time);
                    end
                end else if (Ba == 2'b11) begin
                    {Pc_b3, Act_b3} = 2'b10;
                    RP_chk3 = $time;
                    if (Debug) $display ("at time %t PRE  : Bank = 3",$time);
                    if ($time - RAS_chk3 < tRAS) begin
                        $display ("at time %t ERROR: tRAS violation during Precharge bank 3", $time);
                    end
                end
                if ($time - WR_chk[Ba] < tWRp) begin
                    $display ("at time %t ERROR: tWR violation during Precharge bank %d", $time, Ba);
                end
            end
            if (Data_in_enable == 1'b1 && (Bank == Ba || Addr[10] == 1'b1)) begin
                Data_in_enable = 1'b0;
            end
            if (Cas_latency_3 == 1'b1) begin
                Command[2] = `PRECH;
                Bank_precharge[2] = Ba;
                A10_precharge[2] = Addr[10];
            end else if (Cas_latency_2 == 1'b1) begin
                Command[1] = `PRECH;
                Bank_precharge[1] = Ba;
                A10_precharge[1] = Addr[10];
            end
        end
        if (Burst_term == 1'b1) begin
            if (Data_in_enable == 1'b1) begin
                Data_in_enable = 1'b0;
            end
            if (Cas_latency_3 == 1'b1) begin
                Command[2] = `BST;
            end else if (Cas_latency_2 == 1'b1) begin
                Command[1] = `BST;
            end
            if (Debug) $display ("at time %t BST  : Burst Terminate",$time);
        end
        if (Read_enable == 1'b1 || Write_enable == 1'b1) begin
            if ((Ba == 2'b00 && Pc_b0 == 1'b1) || (Ba == 2'b01 && Pc_b1 == 1'b1) ||
                (Ba == 2'b10 && Pc_b2 == 1'b1) || (Ba == 2'b11 && Pc_b3 == 1'b1)) begin
                $display("at time %t ERROR: Cannot Read or Write - Bank %d is not Activated", $time, Ba);
            end
            if ((Ba == 2'b00) && ($time - RCD_chk0 < tRCD))
	      begin
                 $display("at time %t ERROR: tRCD violation during Read or Write to Bank 0", $time);
	      end
            if ((Ba == 2'b01) && ($time - RCD_chk1 < tRCD))
	      begin
                 $display("at time %t ERROR: tRCD violation during Read or Write to Bank 1", $time);
	      end
            if ((Ba == 2'b10) && ($time - RCD_chk2 < tRCD))
	      begin
                 $display("at time %t ERROR: tRCD violation during Read or Write to Bank 2", $time);
	      end
            if ((Ba == 2'b11) && ($time - RCD_chk3 < tRCD))
	      begin
                 $display("at time %t ERROR: tRCD violation during Read or Write to Bank 3", $time);
	      end
            if (Read_enable == 1'b1) begin
                if (Cas_latency_3 == 1'b1) begin
                    if (Addr[10] == 1'b1) begin
                        Command[2] = `READ_A;
                    end else begin
                        Command[2] = `READ;
                    end
                    Col_addr[2] = Addr;
                    Bank_addr[2] = Ba;
                end else if (Cas_latency_2 == 1'b1) begin
                    if (Addr[10] == 1'b1) begin
                        Command[1] = `READ_A;
                    end else begin
                        Command[1] = `READ;
                    end
                    Col_addr[1] = Addr;
                    Bank_addr[1] = Ba;
                end
                if (Data_in_enable == 1'b1) begin
                    Data_in_enable = 1'b0;
                end
            end else if (Write_enable == 1'b1) begin
                if (Addr[10] == 1'b1) begin
                    Command[0] = `WRITE_A;
                end else begin
                    Command[0] = `WRITE;
                end
                Col_addr[0] = Addr;
                Bank_addr[0] = Ba;
                if (Data_in_enable == 1'b1) begin
                    Data_in_enable = 1'b0;
                end
                if (Data_out_enable == 1'b1) begin
                    Data_out_enable = 1'b0;
                end
            end
            if (Auto_precharge[Bank] == 1'b1 && Write_precharge[Bank] == 1'b1) begin
                RW_interrupt_write[Bank] = 1'b1;
                if (Debug) $display ("at time %t NOTE : Read/Write Bank %d interrupt Write Bank %d with Autoprecharge", $time, Ba, Bank);
            end
            if (Auto_precharge[Bank] == 1'b1 && Read_precharge[Bank] == 1'b1) begin
                RW_interrupt_read[Bank] = 1'b1;
                if (Debug) $display ("at time %t NOTE : Read/Write Bank %d interrupt Read Bank %d with Autoprecharge", $time, Ba, Bank);
            end
            if (Addr[10] == 1'b1) begin
                Auto_precharge[Ba] = 1'b1;
                Count_precharge[Ba] = 0;
                if (Read_enable == 1'b1) begin
                    Read_precharge[Ba] = 1'b1;
                end else if (Write_enable == 1'b1) begin
                    Write_precharge[Ba] = 1'b1;
                end
            end
        end
        if ((Auto_precharge[0] == 1'b1) && (Read_precharge[0] == 1'b1)) begin
            if ((($time - RAS_chk0 >= tRAS) &&                                                      
                ((Burst_length_1 == 1'b1 && Count_precharge[0] >= 1) ||                             
                 (Burst_length_2 == 1'b1 && Count_precharge[0] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge[0] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge[0] >= 8))) ||
                 (RW_interrupt_read[0] == 1'b1)) begin                                              
                    Pc_b0 = 1'b1;
                    Act_b0 = 1'b0;
                    RP_chk0 = $time;
                    Auto_precharge[0] = 1'b0;
                    Read_precharge[0] = 1'b0;
                    RW_interrupt_read[0] = 1'b0;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 0", $time);
            end
        end
        if ((Auto_precharge[1] == 1'b1) && (Read_precharge[1] == 1'b1)) begin
            if ((($time - RAS_chk1 >= tRAS) &&
                ((Burst_length_1 == 1'b1 && Count_precharge[1] >= 1) || 
                 (Burst_length_2 == 1'b1 && Count_precharge[1] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge[1] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge[1] >= 8))) ||
                 (RW_interrupt_read[1] == 1'b1)) begin
                    Pc_b1 = 1'b1;
                    Act_b1 = 1'b0;
                    RP_chk1 = $time;
                    Auto_precharge[1] = 1'b0;
                    Read_precharge[1] = 1'b0;
                    RW_interrupt_read[1] = 1'b0;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 1", $time);
            end
        end
        if ((Auto_precharge[2] == 1'b1) && (Read_precharge[2] == 1'b1)) begin
            if ((($time - RAS_chk2 >= tRAS) &&
                ((Burst_length_1 == 1'b1 && Count_precharge[2] >= 1) || 
                 (Burst_length_2 == 1'b1 && Count_precharge[2] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge[2] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge[2] >= 8))) ||
                 (RW_interrupt_read[2] == 1'b1)) begin
                    Pc_b2 = 1'b1;
                    Act_b2 = 1'b0;
                    RP_chk2 = $time;
                    Auto_precharge[2] = 1'b0;
                    Read_precharge[2] = 1'b0;
                    RW_interrupt_read[2] = 1'b0;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 2", $time);
            end
        end
        if ((Auto_precharge[3] == 1'b1) && (Read_precharge[3] == 1'b1)) begin
            if ((($time - RAS_chk3 >= tRAS) &&
                ((Burst_length_1 == 1'b1 && Count_precharge[3] >= 1) || 
                 (Burst_length_2 == 1'b1 && Count_precharge[3] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge[3] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge[3] >= 8))) ||
                 (RW_interrupt_read[3] == 1'b1)) begin
                    Pc_b3 = 1'b1;
                    Act_b3 = 1'b0;
                    RP_chk3 = $time;
                    Auto_precharge[3] = 1'b0;
                    Read_precharge[3] = 1'b0;
                    RW_interrupt_read[3] = 1'b0;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 3", $time);
            end
        end
        if (Command[0] == `PRECH) begin                         
            if (Bank_precharge[0] == Bank || A10_precharge[0] == 1'b1) begin
                if (Data_out_enable == 1'b1) begin
                    Data_out_enable = 1'b0;
                end
            end
        end else if (Command[0] == `BST) begin                  
            if (Data_out_enable == 1'b1) begin
                Data_out_enable = 1'b0;
            end
        end
        if (Data_out_enable == 1'b0) begin
            Dq_reg <= #tOH {data_bits{1'bz}};
        end
        if (Command[0] == `READ || Command[0] == `READ_A) begin
            Bank = Bank_addr[0];
            Col = Col_addr[0];
            Col_brst = Col_addr[0];
            if (Bank_addr[0] == 2'b00) begin
                Row = B0_row_addr;
            end else if (Bank_addr[0] == 2'b01) begin
                Row = B1_row_addr;
            end else if (Bank_addr[0] == 2'b10) begin
                Row = B2_row_addr;
            end else if (Bank_addr[0] == 2'b11) begin
                Row = B3_row_addr;
            end
            Burst_counter = 0;
            Data_in_enable = 1'b0;
            Data_out_enable = 1'b1;
        end else if (Command[0] == `WRITE || Command[0] == `WRITE_A) begin
            Bank = Bank_addr[0];
            Col = Col_addr[0];
            Col_brst = Col_addr[0];
            if (Bank_addr[0] == 2'b00) begin
                Row = B0_row_addr;
            end else if (Bank_addr[0] == 2'b01) begin
                Row = B1_row_addr;
            end else if (Bank_addr[0] == 2'b10) begin
                Row = B2_row_addr;
            end else if (Bank_addr[0] == 2'b11) begin
                Row = B3_row_addr;
            end
            Burst_counter = 0;
            Data_in_enable = 1'b1;
            Data_out_enable = 1'b0;
        end
        if (Data_in_enable == 1'b1) begin                                   
            if (Bank == 2'b00) Dq_dqm [15 : 0] = Bank0 [{Row, Col}];
            if (Bank == 2'b01) Dq_dqm [15 : 0] = Bank1 [{Row, Col}];
            if (Bank == 2'b10) Dq_dqm [15 : 0] = Bank2 [{Row, Col}];
            if (Bank == 2'b11) Dq_dqm [15 : 0] = Bank3 [{Row, Col}];
            if (Dqm[0] == 1'b0) Dq_dqm [ 7 : 0] = Dq [ 7 : 0];
            if (Dqm[1] == 1'b0) Dq_dqm [15 : 8] = Dq [15 : 8];
            if (Bank == 2'b00) Bank0 [{Row, Col}] = Dq_dqm [15 : 0];
            if (Bank == 2'b01) Bank1 [{Row, Col}] = Dq_dqm [15 : 0];
            if (Bank == 2'b10) Bank2 [{Row, Col}] = Dq_dqm [15 : 0];
            if (Bank == 2'b11) Bank3 [{Row, Col}] = Dq_dqm [15 : 0];
            if (Dqm == 2'b11) begin
                if (Debug) $display("at time %t WRITE: Bank = %d Row = %d, Col = %d, Data = Hi-Z due to DQM", $time, Bank, Row, Col);
            end else begin
                if (Debug) $display("at time %t WRITE: Bank = %d Row = %d, Col = %d, Data = %h, Dqm = %b", $time, Bank, Row, Col, Dq_dqm, Dqm);
                WR_chk [Bank] = $time;
                WR_counter [Bank] = 0;
            end
            #tHZ Burst;
        end else if (Data_out_enable == 1'b1) begin                         
            if (Bank == 2'b00) Dq_dqm [15 : 0] = Bank0 [{Row, Col}];
            if (Bank == 2'b01) Dq_dqm [15 : 0] = Bank1 [{Row, Col}];
            if (Bank == 2'b10) Dq_dqm [15 : 0] = Bank2 [{Row, Col}];
            if (Bank == 2'b11) Dq_dqm [15 : 0] = Bank3 [{Row, Col}];
            if (Dqm_reg0[0] == 1'b1) Dq_dqm [ 7 : 0] = 8'bz;
            if (Dqm_reg0[1] == 1'b1) Dq_dqm [15 : 8] = 8'bz;
            Dq_reg [15 : 0] = #tAC Dq_dqm [15 : 0];
            if (Dqm_reg0 == 2'b11) begin
                if (Debug) $display("at time %t READ : Bank = %d Row = %d, Col = %d, Data = Hi-Z due to DQM", $time, Bank, Row, Col);
            end else begin
                if (Debug) $display("at time %t READ : Bank = %d Row = %d, Col = %d, Data = %h, Dqm = %b", $time, Bank, Row, Col, Dq_reg, Dqm_reg0);
            end
            Burst;
        end
    end
    always @ (WR_counter[0]) begin
        if ((Auto_precharge[0] == 1'b1) && (Write_precharge[0] == 1'b1)) begin
            if ((($time - RAS_chk0 >= tRAS) &&                                                          
               (((Burst_length_1 == 1'b1 || Write_burst_mode == 1'b1) && Count_precharge [0] >= 1) ||   
                 (Burst_length_2 == 1'b1 && Count_precharge [0] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge [0] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge [0] >= 8))) ||
                 (RW_interrupt_write[0] == 1'b1 && WR_counter[0] >= 2)) begin                           
                    Auto_precharge[0] = 1'b0;
                    Write_precharge[0] = 1'b0;
                    RW_interrupt_write[0] = 1'b0;
                    #tWRa;                          
                    Pc_b0 = 1'b1;
                    Act_b0 = 1'b0;
                    RP_chk0 = $time;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 0", $time);
            end
        end
    end
    always @ (WR_counter[1]) begin
        if ((Auto_precharge[1] == 1'b1) && (Write_precharge[1] == 1'b1)) begin
            if ((($time - RAS_chk1 >= tRAS) &&
               (((Burst_length_1 == 1'b1 || Write_burst_mode == 1'b1) && Count_precharge [1] >= 1) || 
                 (Burst_length_2 == 1'b1 && Count_precharge [1] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge [1] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge [1] >= 8))) ||
                 (RW_interrupt_write[1] == 1'b1 && WR_counter[1] >= 2)) begin
                    Auto_precharge[1] = 1'b0;
                    Write_precharge[1] = 1'b0;
                    RW_interrupt_write[1] = 1'b0;
                    #tWRa;                          
                    Pc_b1 = 1'b1;
                    Act_b1 = 1'b0;
                    RP_chk1 = $time;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 1", $time);
            end
        end
    end
    always @ (WR_counter[2]) begin
        if ((Auto_precharge[2] == 1'b1) && (Write_precharge[2] == 1'b1)) begin
            if ((($time - RAS_chk2 >= tRAS) &&
               (((Burst_length_1 == 1'b1 || Write_burst_mode == 1'b1) && Count_precharge [2] >= 1) || 
                 (Burst_length_2 == 1'b1 && Count_precharge [2] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge [2] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge [2] >= 8))) ||
                 (RW_interrupt_write[2] == 1'b1 && WR_counter[2] >= 2)) begin
                    Auto_precharge[2] = 1'b0;
                    Write_precharge[2] = 1'b0;
                    RW_interrupt_write[2] = 1'b0;
                    #tWRa;                          
                    Pc_b2 = 1'b1;
                    Act_b2 = 1'b0;
                    RP_chk2 = $time;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 2", $time);
            end
        end
    end
    always @ (WR_counter[3]) begin
        if ((Auto_precharge[3] == 1'b1) && (Write_precharge[3] == 1'b1)) begin
            if ((($time - RAS_chk3 >= tRAS) &&
               (((Burst_length_1 == 1'b1 || Write_burst_mode == 1'b1) && Count_precharge [3] >= 1) || 
                 (Burst_length_2 == 1'b1 && Count_precharge [3] >= 2) ||
                 (Burst_length_4 == 1'b1 && Count_precharge [3] >= 4) ||
                 (Burst_length_8 == 1'b1 && Count_precharge [3] >= 8))) ||
                 (RW_interrupt_write[3] == 1'b1 && WR_counter[3] >= 2)) begin
                    Auto_precharge[3] = 1'b0;
                    Write_precharge[3] = 1'b0;
                    RW_interrupt_write[3] = 1'b0;
                    #tWRa;                          
                    Pc_b3 = 1'b1;
                    Act_b3 = 1'b0;
                    RP_chk3 = $time;
                    if (Debug) $display ("at time %t NOTE : Start Internal Auto Precharge for Bank 3", $time);
            end
        end
    end
    task Burst;
        begin
            Burst_counter = Burst_counter + 1;
            if (Mode_reg[3] == 1'b0) begin                                  
                Col_temp = Col + 1;
            end else if (Mode_reg[3] == 1'b1) begin                         
                Col_temp[2] =  Burst_counter[2] ^  Col_brst[2];
                Col_temp[1] =  Burst_counter[1] ^  Col_brst[1];
                Col_temp[0] =  Burst_counter[0] ^  Col_brst[0];
            end
            if (Burst_length_2) begin                                       
                Col [0] = Col_temp [0];
            end else if (Burst_length_4) begin                              
                Col [1 : 0] = Col_temp [1 : 0];
            end else if (Burst_length_8) begin                              
                Col [2 : 0] = Col_temp [2 : 0];
            end else begin                                                  
                Col = Col_temp;
            end
            if (Write_burst_mode == 1'b1) begin
                Data_in_enable = 1'b0;
            end
            if (Burst_length_1 == 1'b1) begin
                if (Burst_counter >= 1) begin
                    Data_in_enable = 1'b0;
                    Data_out_enable = 1'b0;
                end
            end else if (Burst_length_2 == 1'b1) begin
                if (Burst_counter >= 2) begin
                    Data_in_enable = 1'b0;
                    Data_out_enable = 1'b0;
                end
            end else if (Burst_length_4 == 1'b1) begin
                if (Burst_counter >= 4) begin
                    Data_in_enable = 1'b0;
                    Data_out_enable = 1'b0;
                end
            end else if (Burst_length_8 == 1'b1) begin
                if (Burst_counter >= 8) begin
                    Data_in_enable = 1'b0;
                    Data_out_enable = 1'b0;
                end
            end
        end
    endtask
    specify
        specparam
                    tAH  =  0.8,                                        
                    tAS  =  1.5,                                        
                    tCH  =  2.5,                                        
                    tCL  =  2.5,                                        
                    tCK  = 10,                                          
                    tDH  =  0.8,                                        
                    tDS  =  1.5,                                        
                    tCKH =  0.8,                                        
                    tCKS =  1.5,                                        
                    tCMH =  0.8,                                        
                    tCMS =  1.5;                                        
        $width    (posedge Clk,           tCH);
        $width    (negedge Clk,           tCL);
        $period   (negedge Clk,           tCK);
        $period   (posedge Clk,           tCK);
        $setuphold(posedge Clk,    Cke,   tCKS, tCKH);
        $setuphold(posedge Clk,    Cs_n,  tCMS, tCMH);
        $setuphold(posedge Clk,    Cas_n, tCMS, tCMH);
        $setuphold(posedge Clk,    Ras_n, tCMS, tCMH);
        $setuphold(posedge Clk,    We_n,  tCMS, tCMH);
        $setuphold(posedge Clk,    Addr,  tAS,  tAH);
        $setuphold(posedge Clk,    Ba,    tAS,  tAH);
        $setuphold(posedge Clk,    Dqm,   tCMS, tCMH);
        $setuphold(posedge Dq_chk, Dq,    tDS,  tDH);
    endspecify
endmodule
