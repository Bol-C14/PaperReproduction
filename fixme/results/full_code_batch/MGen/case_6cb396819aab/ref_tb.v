 `timescale 1ns / 1ps

module tb;

// Inputs
reg CLK_I;
reg RST_I;
//reg [3:0] TAG_I;
reg ACK_I;
reg [31:0] DAT_I;
reg ERR_I;
reg RTY_I;

// Outputs
//wire [3:0] TAG_O,ref_TAG_O;
wire [31:0] ADR_O,ref_ADR_O;
wire CYC_O,ref_CYC_O;
wire [31:0] DAT_O,ref_DAT_O;
wire [3:0] SEL_O,ref_SEL_O;
wire STB_O,ref_STB_O;
wire WE_O,ref_WE_O;

wire       match;
integer    total_tests = 0;
integer    failed_tests = 0;

assign match = ({ref_ADR_O, ref_CYC_O, ref_DAT_O, ref_SEL_O, ref_STB_O, ref_WE_O} === ({ref_ADR_O, ref_CYC_O, ref_DAT_O, ref_SEL_O, ref_STB_O, ref_WE_O} ^ {ADR_O, CYC_O, DAT_O, SEL_O, STB_O, WE_O} ^ {ref_ADR_O, ref_CYC_O, ref_DAT_O, ref_SEL_O, ref_STB_O, ref_WE_O}));

// Instantiate the Unit Under Test (UUT)
top uut (
    .CLK_I(CLK_I),
    .RST_I(RST_I),
    //.TAG_I(TAG_I),
    //.TAG_O(TAG_O),
    .ACK_I(ACK_I),
    .ADR_O(ADR_O),
    .CYC_O(CYC_O),
    .DAT_I(DAT_I),
    .DAT_O(DAT_O),
    .ERR_I(ERR_I),
    .RTY_I(RTY_I),
    .SEL_O(SEL_O),
    .STB_O(STB_O),
    .WE_O(WE_O)
);

ref_wb_master ref_model (
    .CLK_I(CLK_I),
    .RST_I(RST_I),
    //.TAG_I(TAG_I),
    //.ref_TAG_O(ref_TAG_O),
    .ACK_I(ACK_I),
    .ref_ADR_O(ref_ADR_O),
    .ref_CYC_O(ref_CYC_O),
    .DAT_I(DAT_I),
    .ref_DAT_O(ref_DAT_O),
    .ERR_I(ERR_I),
    .RTY_I(RTY_I),
    .ref_SEL_O(ref_SEL_O),
    .ref_STB_O(ref_STB_O),
    .ref_WE_O(ref_WE_O)
);

    initial begin
        CLK_I = 0;
        forever #5 CLK_I = ~CLK_I;
    end


    initial begin
        RST_I = 1;
        #10 RST_I = 0;
    end


    initial begin

        //TAG_I = 0;
        ACK_I = 0;
        DAT_I = 0;
        ERR_I = 0;
        RTY_I = 0;

          #20;
        ERR_I = 1;
        RTY_I = 1;
        RST_I = 1;

          #20;
        ERR_I = 0;
        RTY_I = 0;
        RST_I = 0;
          


        $display("Starting write test");
        wb_master_tb_wr(32'h0000_0000, 32'hDEADBEEF, 4'b1111);
          #10;
        ACK_I = 0;
          #10;
        wb_master_tb_wr(32'h0000_0004, 32'hCAFEBABE, 4'b1111);
          #10;
        ACK_I = 0;
          #10;


        $display("Starting read test");
        wb_master_tb_rd(32'h0000_0000);
          #10;
        ACK_I = 0;
          #10;
        wb_master_tb_rd(32'h0000_0004);
          #10;
        ACK_I = 0;
          #10;


        $display("Starting block write test");
        wb_master_tb_blkwr(32'h0000_0008, 32'h12345678, 4'b1111, 1);
          #10;
        ACK_I = 0;
          #10;
        wb_master_tb_blkwr(32'h0000_000C, 32'h87654321, 4'b1111, 1);
          #10;
        ACK_I = 0;
          #10;


        $display("Starting block read test");
        wb_master_tb_blkrd(32'h0000_0008);
          #10;
        ACK_I = 0;
          #10;
        wb_master_tb_blkrd(32'h0000_000C);
          #10;
        ACK_I = 0;
          #10;


        $display("Starting read-modify-write test");
        wb_master_tb_rmw(32'h0000_0010, 32'hAABBCCDD, 4'b1111);
          #10;
        ACK_I = 0;
          #10;

        repeat (100) begin
        wb_master_tb_wr($random, $random, $random);
        DAT_I = $random;
          #10;
        compare();
        ACK_I = 0;
          #10;
        end

        repeat (100) begin
        wb_master_tb_rd($random);
        DAT_I = $random;
          #10;
        compare();
        ACK_I = 0;
          #10;
        end

        repeat (100) begin
        wb_master_tb_blkwr($random, $random, $random, 1);
        DAT_I = $random;
          #10;
        compare();
        ACK_I = 0;
          #10;
        end

        repeat (100) begin
        wb_master_tb_blkrd($random);
        DAT_I = $random;
          #10;
        compare();
        ACK_I = 0;
          #10;
        end

        repeat (100) begin
        wb_master_tb_rmw($random, $random, $random);;
        DAT_I = $random;
          #10;
        compare();
        ACK_I = 0;
          #10;
        end


        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $display("All tests completed");
        $finish;
    end

    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

    // Ð´²Ù×÷ÈÎÎñ
    task wb_master_tb_wr;
        input [31:0] adr;
        input [31:0] dat;
        input [3:0] sel;

        fork
            DAT_I = dat;
            ACK_I = 0;
            uut.wr(adr, dat, sel);
            ref_model.wr(adr, dat, sel);
            #20 ACK_I = 1;
        join   
    endtask

    // ¶Á²Ù×÷ÈÎÎñ
    task wb_master_tb_rd;
        input [31:0] adr;
        reg [31:0] result;
        fork
            uut.rd(adr, result);
            ref_model.rd(adr, result);
            ACK_I = 0;
            #20 ACK_I = 1;
        join
    endtask

    // ¿éÐ´²Ù×÷ÈÎÎñ
    task wb_master_tb_blkwr;
        input [31:0] adr;
        input [31:0] dat;
        input [3:0] sel;
        input end_flag;
        fork
            DAT_I = dat;
            uut.blkwr(adr, dat, sel, end_flag);
            ref_model.blkwr(adr, dat, sel, end_flag);
            ACK_I = 0;
            #20 ACK_I = 1;
        join
    endtask

    // ¿é¶Á²Ù×÷ÈÎÎñ
    task wb_master_tb_blkrd;
        input [31:0] adr;
        reg [31:0] result;
        fork
            uut.blkrd(adr, 1, result);
            ref_model.blkrd(adr, 1, result);
            ACK_I = 0;
            #20 ACK_I = 1;
        join
    endtask

    // ¶Á-ÐÞ¸Ä-Ð´²Ù×÷ÈÎÎñ
    task wb_master_tb_rmw;
        input [31:0] adr;
        input [31:0] dat;
        input [3:0] sel;
        reg [31:0] result;
        fork
            uut.rmw(adr, dat, sel, result);
            ref_model.rmw(adr, dat, sel, result);
            ACK_I = 0;
            #20 ACK_I = 1;
        join
    endtask

task compare;
     total_tests = total_tests + 1;
     if (match)                                //condition to check DUT outputs and calculated 
                                                    //outputs from task are equal 
	   begin
	   $display("\033[1;32mtestcase is passed!!!\033[0m");
	   end
	   else begin
	   $display("\033[1;31mtestcase is failed!!!\033[0m");
         failed_tests = failed_tests + 1; 
         end
endtask

endmodule

