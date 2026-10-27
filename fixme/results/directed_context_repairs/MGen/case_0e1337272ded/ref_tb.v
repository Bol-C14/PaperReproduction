 `timescale 1ns / 1ps

module tb;

    reg clk;
    reg rst_n;

    // Input signal
    reg [7:0] asi_d;

    // Output signals
    wire asi_internal_d,ref_asi_internal_d;
    wire nucleus_asi_d,ref_nucleus_asi_d;
    wire primary_asi_d,ref_primary_asi_d;
    wire secondary_asi_d,ref_secondary_asi_d;
    wire lendian_asi_d,ref_lendian_asi_d;
    wire nofault_asi_d,ref_nofault_asi_d;
    wire quad_asi_d,ref_quad_asi_d;
    wire binit_quad_asi_d,ref_binit_quad_asi_d;
    wire dcache_byp_asi_d,ref_dcache_byp_asi_d;
    wire tlb_lng_ltncy_asi_d,ref_tlb_lng_ltncy_asi_d;
    wire tlb_byp_asi_d,ref_tlb_byp_asi_d;
    wire as_if_user_asi_d,ref_as_if_user_asi_d;
    wire atomic_asi_d,ref_atomic_asi_d;
    wire blk_asi_d,ref_blk_asi_d;
    wire dc_diagnstc_asi_d,ref_dc_diagnstc_asi_d;
    wire dtagv_diagnstc_asi_d,ref_dtagv_diagnstc_asi_d;
    wire wr_only_asi_d,ref_wr_only_asi_d;
    wire rd_only_asi_d,ref_rd_only_asi_d;
    wire unimp_asi_d,ref_unimp_asi_d;
    wire ifu_nontlb_asi_d,ref_ifu_nontlb_asi_d;
    wire recognized_asi_d,ref_recognized_asi_d;
    wire ifill_tlb_asi_d,ref_ifill_tlb_asi_d;
    wire dfill_tlb_asi_d,ref_dfill_tlb_asi_d;
    wire rd_only_ltlb_asi_d,ref_rd_only_ltlb_asi_d;
    wire wr_only_ltlb_asi_d,ref_wr_only_ltlb_asi_d;
    wire phy_use_ec_asi_d,ref_phy_use_ec_asi_d;
    wire phy_byp_ec_asi_d,ref_phy_byp_ec_asi_d;
    wire mmu_rd_only_asi_d,ref_mmu_rd_only_asi_d;
    wire intrpt_disp_asi_d,ref_intrpt_disp_asi_d;
    wire dmmu_asi58_d,ref_dmmu_asi58_d;
    wire immu_asi50_d,ref_immu_asi50_d;

wire	quad_ldd_real, quad_ldd_real_little ;
wire	asi_if_user_prim_all_d,asi_if_user_sec_all_d ;
wire	asi_if_user_prim_d,asi_if_user_sec_d ;
wire	nucleus_asi_exact_d ;
wire	prim_asi_exact_d ;
wire	phy_use_ec_asi ;
wire	phy_byp_ec_asi ;
wire	sec_asi_exact_d ;
wire	idemap,ddemap,ddata_in,ddaccess ;
wire	dtag_read,idata_in,idaccess,invld_all,itag_read ;
wire	blk_asif_usr_plittle, blk_asif_usr_slittle ;
wire	blk_plittle, blk_slittle ;
wire	blk_asif_usr_p, blk_asif_usr_s ;
wire	blk_cmt_p, blk_cmt_s; 
wire	blk_p, blk_s ;
wire	binit_nucleus_d, binit_nucleus_little_d ;
wire	real_mem_little,real_io_little ;
wire	unimp_CD_prm;
wire	unimp_CD_sec;
wire	dtsb_8k_ptr, dtsb_64k_ptr, dtsb_dir_ptr;
wire	itsb_8k_ptr, itsb_64k_ptr;
wire	unimp_C ;
wire	unimp_D ;
assign	dtsb_8k_ptr = (asi_d[7:0] == 8'h59) ;
assign	dtsb_64k_ptr = (asi_d[7:0] == 8'h5A) ;
assign	dtsb_dir_ptr = (asi_d[7:0] == 8'h5B) ;
assign	itsb_8k_ptr = (asi_d[7:0] == 8'h51) ;
assign	itsb_64k_ptr = (asi_d[7:0] == 8'h52) ;
assign	ref_mmu_rd_only_asi_d =
	dtsb_8k_ptr | dtsb_64k_ptr | dtsb_dir_ptr | itsb_8k_ptr | itsb_64k_ptr ;
assign ref_intrpt_disp_asi_d = (asi_d[7:0] == 8'h73) ; 
assign	ref_dmmu_asi58_d =	(asi_d[7:0] == 8'h58) ; 
assign  ref_immu_asi50_d =  (asi_d[7:0] == 8'h50) ;


    wire       match;
    integer    total_tests = 0;
    integer    failed_tests = 0;

    assign match = ({ref_asi_internal_d,ref_nucleus_asi_d,ref_primary_asi_d,ref_secondary_asi_d,ref_lendian_asi_d,ref_nofault_asi_d,ref_quad_asi_d,ref_binit_quad_asi_d,ref_dcache_byp_asi_d,
ref_tlb_lng_ltncy_asi_d,ref_tlb_byp_asi_d,ref_as_if_user_asi_d,ref_atomic_asi_d,ref_blk_asi_d,ref_dc_diagnstc_asi_d,ref_dtagv_diagnstc_asi_d,ref_wr_only_asi_d,ref_rd_only_asi_d,ref_unimp_asi_d,
ref_ifu_nontlb_asi_d,ref_recognized_asi_d,ref_ifill_tlb_asi_d,ref_dfill_tlb_asi_d,ref_rd_only_ltlb_asi_d,ref_wr_only_ltlb_asi_d,ref_phy_use_ec_asi_d,ref_phy_byp_ec_asi_d,ref_mmu_rd_only_asi_d,
ref_intrpt_disp_asi_d,ref_dmmu_asi58_d,ref_immu_asi50_d} ===  {asi_internal_d,nucleus_asi_d,primary_asi_d,secondary_asi_d,lendian_asi_d,nofault_asi_d,quad_asi_d,binit_quad_asi_d,dcache_byp_asi_d,tlb_lng_ltncy_asi_d,tlb_byp_asi_d,as_if_user_asi_d,atomic_asi_d,
blk_asi_d,dc_diagnstc_asi_d,dtagv_diagnstc_asi_d,wr_only_asi_d,rd_only_asi_d,unimp_asi_d,ifu_nontlb_asi_d,recognized_asi_d,ifill_tlb_asi_d,dfill_tlb_asi_d,rd_only_ltlb_asi_d,wr_only_ltlb_asi_d,
phy_use_ec_asi_d,phy_byp_ec_asi_d,mmu_rd_only_asi_d,intrpt_disp_asi_d,dmmu_asi58_d,immu_asi50_d});

    // Instantiate the lsu_asi_decode module
    top uut (
        .asi_d(asi_d),
        .asi_internal_d(asi_internal_d),
        .nucleus_asi_d(nucleus_asi_d),
        .primary_asi_d(primary_asi_d),
        .secondary_asi_d(secondary_asi_d),
        .lendian_asi_d(lendian_asi_d),
        .nofault_asi_d(nofault_asi_d),
        .quad_asi_d(quad_asi_d),
        .binit_quad_asi_d(binit_quad_asi_d),
        .dcache_byp_asi_d(dcache_byp_asi_d),
        .tlb_lng_ltncy_asi_d(tlb_lng_ltncy_asi_d),
        .tlb_byp_asi_d(tlb_byp_asi_d),
        .as_if_user_asi_d(as_if_user_asi_d),
        .atomic_asi_d(atomic_asi_d),
        .blk_asi_d(blk_asi_d),
        .dc_diagnstc_asi_d(dc_diagnstc_asi_d),
        .dtagv_diagnstc_asi_d(dtagv_diagnstc_asi_d),
        .wr_only_asi_d(wr_only_asi_d),
        .rd_only_asi_d(rd_only_asi_d),
        .unimp_asi_d(unimp_asi_d),
        .ifu_nontlb_asi_d(ifu_nontlb_asi_d),
        .recognized_asi_d(recognized_asi_d),
        .ifill_tlb_asi_d(ifill_tlb_asi_d),
        .dfill_tlb_asi_d(dfill_tlb_asi_d),
        .rd_only_ltlb_asi_d(rd_only_ltlb_asi_d),
        .wr_only_ltlb_asi_d(wr_only_ltlb_asi_d),
        .phy_use_ec_asi_d(phy_use_ec_asi_d),
        .phy_byp_ec_asi_d(phy_byp_ec_asi_d),
        .mmu_rd_only_asi_d(mmu_rd_only_asi_d),
        .intrpt_disp_asi_d(intrpt_disp_asi_d),
        .dmmu_asi58_d(dmmu_asi58_d),
        .immu_asi50_d(immu_asi50_d)
    );

    ref_lsu_asi_decode ref_model (
        .asi_d(asi_d),
        .ref_asi_internal_d(ref_asi_internal_d),
        .ref_nucleus_asi_d(ref_nucleus_asi_d),
        .ref_primary_asi_d(ref_primary_asi_d),
        .ref_secondary_asi_d(ref_secondary_asi_d),
        .ref_lendian_asi_d(ref_lendian_asi_d),
        .ref_nofault_asi_d(ref_nofault_asi_d),
        .ref_quad_asi_d(ref_quad_asi_d),
        .ref_binit_quad_asi_d(ref_binit_quad_asi_d),
        .ref_dcache_byp_asi_d(ref_dcache_byp_asi_d),
        .ref_tlb_lng_ltncy_asi_d(ref_tlb_lng_ltncy_asi_d),
        .ref_tlb_byp_asi_d(ref_tlb_byp_asi_d),
        .ref_as_if_user_asi_d(ref_as_if_user_asi_d),
        .ref_atomic_asi_d(ref_atomic_asi_d),
        .ref_blk_asi_d(ref_blk_asi_d),
        .ref_dc_diagnstc_asi_d(ref_dc_diagnstc_asi_d),
        .ref_dtagv_diagnstc_asi_d(ref_dtagv_diagnstc_asi_d),
        .ref_wr_only_asi_d(ref_wr_only_asi_d),
        .ref_rd_only_asi_d(ref_rd_only_asi_d),
        .ref_unimp_asi_d(ref_unimp_asi_d),
        .ref_ifu_nontlb_asi_d(ref_ifu_nontlb_asi_d),
        .ref_recognized_asi_d(ref_recognized_asi_d),
        .ref_ifill_tlb_asi_d(ref_ifill_tlb_asi_d),
        .ref_dfill_tlb_asi_d(ref_dfill_tlb_asi_d),
        .ref_rd_only_ltlb_asi_d(ref_rd_only_ltlb_asi_d),
        .ref_wr_only_ltlb_asi_d(ref_wr_only_ltlb_asi_d),
        .ref_phy_use_ec_asi_d(ref_phy_use_ec_asi_d),
        .ref_phy_byp_ec_asi_d(ref_phy_byp_ec_asi_d),
        .ref_mmu_rd_only_asi_d(ref_mmu_rd_only_asi_d),
        .ref_intrpt_disp_asi_d(ref_intrpt_disp_asi_d),
        .ref_dmmu_asi58_d(ref_dmmu_asi58_d),
        .ref_immu_asi50_d(ref_immu_asi50_d)
    );


    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst_n = 0;
        #10 rst_n = 1;
    end

    reg [7:0] test_vector [0:255];
    integer i;

    initial begin
        for (i = 0; i < 256; i = i + 1) begin
            test_vector[i] = i;
        end

        for (i = 0; i < 256; i = i + 1) begin
            #10 asi_d = test_vector[i];
            #10 check_outputs(test_vector[i]);
            #10 compare();
        end


        // Test Case 1: Test internal ASI
        asi_d = 8'h40; #10; // Expect asi_internal_d = 1
        compare();
        if (asi_internal_d !== 1) $display("Test Case 1 Failed: Expected 1, got %b", asi_internal_d);

        // Test Case 2: Test nucleus ASI
        asi_d = 8'h04; #10; // Expect nucleus_asi_d = 1
        compare();
        if (nucleus_asi_d !== 1) $display("Test Case 2 Failed: Expected 1, got %b", nucleus_asi_d);

        // Test Case 3: Test primary ASI
        asi_d = 8'h82; #10; // Expect primary_asi_d = 1
        compare();
        if (primary_asi_d !== 1) $display("Test Case 3 Failed: Expected 1, got %b", primary_asi_d);

        // Test Case 4: Test secondary ASI
        asi_d = 8'h89; #10; // Expect secondary_asi_d = 1
        compare();
        if (secondary_asi_d !== 1) $display("Test Case 4 Failed: Expected 1, got %b", secondary_asi_d);

        // Test Case 5: Test little-endian ASI
        asi_d = 8'h2C; #10; // Expect lendian_asi_d = 1
        compare();
        if (lendian_asi_d !== 1) $display("Test Case 5 Failed: Expected 1, got %b", lendian_asi_d);

        // Test Case 6: No-fault ASI
        asi_d = 8'h82; #10; // Expect nofault_asi_d = 1
        compare();
        if (nofault_asi_d !== 1) $display("Test Case 6 Failed: Expected 1, got %b", nofault_asi_d);
        
        // Test Case 7: Quad ASI
        asi_d = 8'h26; #10; // Expect quad_asi_d = 1
        compare();
        if (quad_asi_d !== 1) $display("Test Case 7 Failed: Expected 1, got %b", quad_asi_d);

        // Test Case 8: Unimplemented ASI
        asi_d = 8'hC0; #10; // Expect unimp_asi_d = 1
        compare();
        if (unimp_asi_d !== 1) $display("Test Case 8 Failed: Expected 1, got %b", unimp_asi_d);

        // Test Case 9: Recognized ASI
        asi_d = 8'h40; #10; // Expect recognized_asi_d = 1
        compare();
        if (recognized_asi_d !== 1) $display("Test Case 9 Failed: Expected 1, got %b", recognized_asi_d);

        // Test Case 10: Clear ASI
        asi_d = 8'hFF; #10; // Expect all outputs to be 0
        compare();
        if (asi_internal_d !== 0 || nucleus_asi_d !== 0 || primary_asi_d !== 0 || 
            secondary_asi_d !== 0 || lendian_asi_d !== 0 || nofault_asi_d !== 0 || 
            quad_asi_d !== 0 || unimp_asi_d !== 0 || recognized_asi_d !== 0) begin
            $display("Test Case 10 Failed: Expected all outputs 0, got outputs.");
        end
        $display("\033[1;34mAll tests completed.\033[0m");
        $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests);
	    $display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
        $finish;
    end

    task check_outputs;
        input [7:0] asi_d_val;
        reg expected_asi_internal_d;
        reg expected_nucleus_asi_d;
        reg expected_primary_asi_d;
        reg expected_secondary_asi_d;
        reg expected_lendian_asi_d;
        reg expected_nofault_asi_d;
        reg expected_quad_asi_d;
        reg expected_binit_quad_asi_d;
        reg expected_dcache_byp_asi_d;
        reg expected_tlb_lng_ltncy_asi_d;
        reg expected_tlb_byp_asi_d;
        reg expected_as_if_user_asi_d;
        reg expected_atomic_asi_d;
        reg expected_blk_asi_d;
        reg expected_dc_diagnstc_asi_d;
        reg expected_dtagv_diagnstc_asi_d;
        reg expected_wr_only_asi_d;
        reg expected_rd_only_asi_d;
        reg expected_unimp_asi_d;
        reg expected_ifu_nontlb_asi_d;
        reg expected_recognized_asi_d;
        reg expected_ifill_tlb_asi_d;
        reg expected_dfill_tlb_asi_d;
        reg expected_rd_only_ltlb_asi_d;
        reg expected_wr_only_ltlb_asi_d;
        reg expected_phy_use_ec_asi_d;
        reg expected_phy_byp_ec_asi_d;
        reg expected_mmu_rd_only_asi_d;
        reg expected_intrpt_disp_asi_d;
        reg expected_dmmu_asi58_d;
        reg expected_immu_asi50_d;


expected_asi_internal_d = (asi_d_val == 8'h40) || 
                          (asi_d_val == 8'h45) || 
                          (asi_d_val == 8'h50) || 
                          itsb_8k_ptr || 
                          itsb_64k_ptr || 
                          dmmu_asi58_d ||
                          (asi_d_val == 8'h21) || 
                          (asi_d_val == 8'h20) || 
                          (asi_d_val == 8'h25) || 
                          (asi_d_val == 8'h4F) || 
                          dtsb_8k_ptr || 
                          dtsb_64k_ptr || 
                          dtsb_dir_ptr || 
                          (asi_d_val == 8'h72) || 
                          intrpt_disp_asi_d || 
                          (asi_d_val == 8'h74) || 
                          (asi_d_val == 8'h44) || 
                          (asi_d_val == 8'h31) || 
                          (asi_d_val == 8'h32) || 
                          (asi_d_val == 8'h39) || 
                          (asi_d_val == 8'h3A) || 
                          (asi_d_val == 8'h33) || 
                          (asi_d_val == 8'h3B) || 
                          (asi_d_val == 8'h35) || 
                          (asi_d_val == 8'h36) || 
                          (asi_d_val == 8'h3D) || 
                          (asi_d_val == 8'h3E) || 
                          (asi_d_val == 8'h37) || 
                          (asi_d_val == 8'h3F) || 
                          dc_diagnstc_asi_d || 
                          dtagv_diagnstc_asi_d || 
                          tlb_lng_ltncy_asi_d || 
                          ifu_nontlb_asi_d;

expected_nucleus_asi_d = (asi_d_val == 8'h04) || 
                         (asi_d_val == 8'h0C) || 
                         (asi_d_val == 8'h24) || 
                         (asi_d_val == 8'h2C);

expected_primary_asi_d = asi_if_user_prim_all_d || 
                         prim_asi_exact_d || 
                         (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'hE2) || 
                         (asi_d_val == 8'hEA) || 
                         blk_asif_usr_p || 
                         blk_asif_usr_plittle || 
                         blk_plittle || 
                         blk_p || 
                         blk_cmt_p || 
                         unimp_CD_prm;

expected_secondary_asi_d = asi_if_user_sec_all_d || 
                           sec_asi_exact_d || 
                           (asi_d_val == 8'h83) || 
                           (asi_d_val == 8'h8B) || 
                           (asi_d_val == 8'hE3) || 
                           (asi_d_val == 8'hEB) || 
                           blk_asif_usr_s || 
                           blk_asif_usr_slittle || 
                           blk_slittle || 
                           blk_s || 
                           blk_cmt_s || 
                           unimp_CD_sec;

expected_lendian_asi_d = (asi_d_val == 8'h0C) || 
                         (asi_d_val == 8'h2C) || 
                         (asi_d_val == 8'h18) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h8B) || 
                         (asi_d_val == 8'h2A) || 
                         (asi_d_val == 8'hEA) || 
                         (asi_d_val == 8'h19) || 
                         (asi_d_val == 8'h89) || 
                         (asi_d_val == 8'h88) || 
                         (asi_d_val == 8'h2B) || 
                         (asi_d_val == 8'hEB) || 
                         real_mem_little || 
                         real_io_little || 
                         blk_asif_usr_plittle || 
                         blk_asif_usr_slittle || 
                         blk_plittle || 
                         blk_slittle || 
                         quad_ldd_real_little || 
                         binit_nucleus_little_d;

expected_nofault_asi_d = (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h83) || 
                         (asi_d_val == 8'h8B);

expected_quad_asi_d = binit_quad_asi_d || 
                      quad_ldd_real || 
                      quad_ldd_real_little || 
                      (asi_d_val == 8'h24) || 
                      (asi_d_val == 8'h2C);

expected_tlb_byp_asi_d = phy_byp_ec_asi || 
                         phy_use_ec_asi || 
                         quad_ldd_real || 
                         quad_ldd_real_little;

expected_atomic_asi_d = nucleus_asi_exact_d || 
                        prim_asi_exact_d || 
                        sec_asi_exact_d || 
                        asi_if_user_prim_d || 
                        asi_if_user_sec_d || 
                        phy_use_ec_asi;

expected_dcache_byp_asi_d = tlb_byp_asi_d;

expected_rd_only_asi_d = (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h83) || 
                         (asi_d_val == 8'h8B) || 
                         (asi_d_val == 8'h74);

expected_wr_only_asi_d = (asi_d_val == 8'h73);

expected_blk_asi_d = blk_asif_usr_p || 
                      blk_asif_usr_s || 
                      blk_plittle || 
                      blk_slittle || 
                      blk_p || 
                      blk_s || 
                      blk_asif_usr_plittle || 
                      blk_asif_usr_slittle || 
                      blk_plittle || 
                      blk_slittle;

expected_asi_internal_d = (asi_d_val == 8'h40) || 
                          (asi_d_val == 8'h45) || 
                          (asi_d_val == 8'h50) || 
                          itsb_8k_ptr || 
                          itsb_64k_ptr || 
                          dmmu_asi58_d ||
                          (asi_d_val == 8'h21) || 
                          (asi_d_val == 8'h20) || 
                          (asi_d_val == 8'h25) || 
                          (asi_d_val == 8'h4F) || 
                          dtsb_8k_ptr || 
                          dtsb_64k_ptr || 
                          dtsb_dir_ptr || 
                          (asi_d_val == 8'h72) || 
                          intrpt_disp_asi_d || 
                          (asi_d_val == 8'h74) || 
                          (asi_d_val == 8'h44) || 
                          (asi_d_val == 8'h31) || 
                          (asi_d_val == 8'h32) || 
                          (asi_d_val == 8'h39) || 
                          (asi_d_val == 8'h3A) || 
                          (asi_d_val == 8'h33) || 
                          (asi_d_val == 8'h3B) || 
                          (asi_d_val == 8'h35) || 
                          (asi_d_val == 8'h36) || 
                          (asi_d_val == 8'h3D) || 
                          (asi_d_val == 8'h3E) || 
                          (asi_d_val == 8'h37) || 
                          (asi_d_val == 8'h3F) || 
                          dc_diagnstc_asi_d || 
                          dtagv_diagnstc_asi_d || 
                          tlb_lng_ltncy_asi_d || 
                          ifu_nontlb_asi_d;

expected_nucleus_asi_d = nucleus_asi_exact_d ||
                         (asi_d_val == 8'h24) || 
                         (asi_d_val == 8'h2C);

expected_primary_asi_d = asi_if_user_prim_all_d || 
                         prim_asi_exact_d || 
                         (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'hE2) || 
                         (asi_d_val == 8'hEA) || 
                         blk_asif_usr_p || 
                         blk_asif_usr_plittle || 
                         blk_plittle || 
                         blk_p || 
                         blk_cmt_p || 
                         unimp_CD_prm;

expected_secondary_asi_d = asi_if_user_sec_all_d || 
                           sec_asi_exact_d || 
                           (asi_d_val == 8'h83) || 
                           (asi_d_val == 8'h8B) || 
                           (asi_d_val == 8'hE3) || 
                           (asi_d_val == 8'hEB) || 
                           blk_asif_usr_s || 
                           blk_asif_usr_slittle || 
                           blk_slittle || 
                           blk_s || 
                           blk_cmt_s || 
                           unimp_CD_sec;

expected_lendian_asi_d = (asi_d_val == 8'h0C) || 
                         (asi_d_val == 8'h2C) || 
                         (asi_d_val == 8'h18) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h8B) || 
                         (asi_d_val == 8'h2A) || 
                         (asi_d_val == 8'hEA) || 
                         (asi_d_val == 8'h19) || 
                         (asi_d_val == 8'h89) || 
                         (asi_d_val == 8'h88) || 
                         (asi_d_val == 8'h2B) || 
                         (asi_d_val == 8'hEB) || 
                         real_mem_little || 
                         real_io_little || 
                         blk_asif_usr_plittle || 
                         blk_asif_usr_slittle || 
                         blk_plittle || 
                         blk_slittle || 
                         quad_ldd_real_little || 
                         binit_nucleus_little_d;

expected_nofault_asi_d = (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h83) || 
                         (asi_d_val == 8'h8B);

expected_quad_asi_d = binit_quad_asi_d || 
                      quad_ldd_real || 
                      quad_ldd_real_little || 
                      (asi_d_val == 8'h24) || 
                      (asi_d_val == 8'h2C);

expected_binit_quad_asi_d = binit_nucleus_d || 
                            binit_nucleus_little_d ||
                            (asi_d_val == 8'h22) || 
                            (asi_d_val == 8'h2A) || 
                            (asi_d_val == 8'h23) || 
                            (asi_d_val == 8'h2B) || 
                            (asi_d_val == 8'hE2) || 
                            (asi_d_val == 8'hEA) || 
                            (asi_d_val == 8'hE3) || 
                            (asi_d_val == 8'hEB);

expected_dcache_byp_asi_d = tlb_byp_asi_d;

expected_tlb_byp_asi_d = phy_byp_ec_asi || phy_use_ec_asi || 
                         quad_ldd_real || quad_ldd_real_little;

expected_atomic_asi_d = nucleus_asi_exact_d || prim_asi_exact_d || sec_asi_exact_d || 
                         asi_if_user_prim_d || asi_if_user_sec_d || phy_use_ec_asi;


expected_blk_asi_d = blk_asif_usr_p || blk_asif_usr_s || 
                      blk_plittle || blk_slittle || 
                      blk_p || blk_s || 
                      blk_asif_usr_plittle || blk_asif_usr_slittle || 
                      blk_plittle || blk_slittle;

expected_dc_diagnstc_asi_d = (asi_d_val == 8'h46);

expected_dtagv_diagnstc_asi_d = (asi_d_val == 8'h47);

expected_wr_only_asi_d = (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h83) || 
                         (asi_d_val == 8'h8B) || 
                         (asi_d_val == 8'h74);

expected_rd_only_asi_d = (asi_d_val == 8'h82) || 
                         (asi_d_val == 8'h8A) || 
                         (asi_d_val == 8'h83) || 
                         (asi_d_val == 8'h8B) || 
                         (asi_d_val == 8'h73);

expected_unimp_asi_d = unimp_C || unimp_D || 
                        blk_cmt_p || blk_cmt_s;

expected_recognized_asi_d = asi_internal_d || nucleus_asi_d || 
                             primary_asi_d || secondary_asi_d || 
                             lendian_asi_d || nofault_asi_d || 
                             quad_asi_d || tlb_byp_asi_d || 
                             unimp_asi_d || blk_asi_d;

        if (asi_internal_d != expected_asi_internal_d ||
            nucleus_asi_d != expected_nucleus_asi_d ||
            primary_asi_d != expected_primary_asi_d ||
            secondary_asi_d != expected_secondary_asi_d ||
            lendian_asi_d != expected_lendian_asi_d ||
            nofault_asi_d != expected_nofault_asi_d ||
            quad_asi_d != expected_quad_asi_d ||
            binit_quad_asi_d != expected_binit_quad_asi_d ||
            dcache_byp_asi_d != expected_dcache_byp_asi_d ||
            tlb_lng_ltncy_asi_d != expected_tlb_lng_ltncy_asi_d ||
            tlb_byp_asi_d != expected_tlb_byp_asi_d ||
            as_if_user_asi_d != expected_as_if_user_asi_d ||
            atomic_asi_d != expected_atomic_asi_d ||
            blk_asi_d != expected_blk_asi_d ||
            dc_diagnstc_asi_d != expected_dc_diagnstc_asi_d ||
            dtagv_diagnstc_asi_d != expected_dtagv_diagnstc_asi_d ||
            wr_only_asi_d != expected_wr_only_asi_d ||
            rd_only_asi_d != expected_rd_only_asi_d ||
            unimp_asi_d != expected_unimp_asi_d ||
            ifu_nontlb_asi_d != expected_ifu_nontlb_asi_d ||
            recognized_asi_d != expected_recognized_asi_d ||
            ifill_tlb_asi_d != expected_ifill_tlb_asi_d ||
            dfill_tlb_asi_d != expected_dfill_tlb_asi_d ||
            rd_only_ltlb_asi_d != expected_rd_only_ltlb_asi_d ||
            wr_only_ltlb_asi_d != expected_wr_only_ltlb_asi_d ||
            phy_use_ec_asi_d != expected_phy_use_ec_asi_d ||
            phy_byp_ec_asi_d != expected_phy_byp_ec_asi_d ||
            mmu_rd_only_asi_d != expected_mmu_rd_only_asi_d ||
            intrpt_disp_asi_d != expected_intrpt_disp_asi_d ||
            dmmu_asi58_d != expected_dmmu_asi58_d ||
            immu_asi50_d != expected_immu_asi50_d) begin
            $display("Test Failed for asi_d = %h", asi_d_val);
        end else begin
            $display("Test Passed for asi_d = %h", asi_d_val);
        end
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


    initial begin
        $dumpfile("sim.fsdb");
        $dumpvars(0);
    end

endmodule
