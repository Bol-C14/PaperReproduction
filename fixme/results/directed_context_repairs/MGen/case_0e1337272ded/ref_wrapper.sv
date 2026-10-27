`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    output longint unsigned ref_asi_internal_d__dpi,
    output longint unsigned ref_nucleus_asi_d__dpi,
    output longint unsigned ref_primary_asi_d__dpi,
    output longint unsigned ref_secondary_asi_d__dpi,
    output longint unsigned ref_lendian_asi_d__dpi,
    output longint unsigned ref_nofault_asi_d__dpi,
    output longint unsigned ref_quad_asi_d__dpi,
    output longint unsigned ref_binit_quad_asi_d__dpi,
    output longint unsigned ref_dcache_byp_asi_d__dpi,
    output longint unsigned ref_tlb_lng_ltncy_asi_d__dpi,
    output longint unsigned ref_tlb_byp_asi_d__dpi,
    output longint unsigned ref_as_if_user_asi_d__dpi,
    output longint unsigned ref_atomic_asi_d__dpi,
    output longint unsigned ref_blk_asi_d__dpi,
    output longint unsigned ref_dc_diagnstc_asi_d__dpi,
    output longint unsigned ref_dtagv_diagnstc_asi_d__dpi,
    output longint unsigned ref_wr_only_asi_d__dpi,
    output longint unsigned ref_rd_only_asi_d__dpi,
    output longint unsigned ref_unimp_asi_d__dpi,
    output longint unsigned ref_ifu_nontlb_asi_d__dpi,
    output longint unsigned ref_recognized_asi_d__dpi,
    output longint unsigned ref_ifill_tlb_asi_d__dpi,
    output longint unsigned ref_dfill_tlb_asi_d__dpi,
    output longint unsigned ref_rd_only_ltlb_asi_d__dpi,
    output longint unsigned ref_wr_only_ltlb_asi_d__dpi,
    output longint unsigned ref_phy_use_ec_asi_d__dpi,
    output longint unsigned ref_phy_byp_ec_asi_d__dpi,
    output longint unsigned ref_mmu_rd_only_asi_d__dpi,
    output longint unsigned ref_intrpt_disp_asi_d__dpi,
    output longint unsigned ref_dmmu_asi58_d__dpi,
    output longint unsigned ref_immu_asi50_d__dpi,
    input longint unsigned asi_d
);

module ref_lsu_asi_decode (
    ref_asi_internal_d,
    ref_nucleus_asi_d,
    ref_primary_asi_d,
    ref_secondary_asi_d,
    ref_lendian_asi_d,
    ref_nofault_asi_d,
    ref_quad_asi_d,
    ref_binit_quad_asi_d,
    ref_dcache_byp_asi_d,
    ref_tlb_lng_ltncy_asi_d,
    ref_tlb_byp_asi_d,
    ref_as_if_user_asi_d,
    ref_atomic_asi_d,
    ref_blk_asi_d,
    ref_dc_diagnstc_asi_d,
    ref_dtagv_diagnstc_asi_d,
    ref_wr_only_asi_d,
    ref_rd_only_asi_d,
    ref_unimp_asi_d,
    ref_ifu_nontlb_asi_d,
    ref_recognized_asi_d,
    ref_ifill_tlb_asi_d,
    ref_dfill_tlb_asi_d,
    ref_rd_only_ltlb_asi_d,
    ref_wr_only_ltlb_asi_d,
    ref_phy_use_ec_asi_d,
    ref_phy_byp_ec_asi_d,
    ref_mmu_rd_only_asi_d,
    ref_intrpt_disp_asi_d,
    ref_dmmu_asi58_d,
    ref_immu_asi50_d,
    asi_d
);
output reg ref_asi_internal_d;
output reg ref_nucleus_asi_d;
output reg ref_primary_asi_d;
output reg ref_secondary_asi_d;
output reg ref_lendian_asi_d;
output reg ref_nofault_asi_d;
output reg ref_quad_asi_d;
output reg ref_binit_quad_asi_d;
output reg ref_dcache_byp_asi_d;
output reg ref_tlb_lng_ltncy_asi_d;
output reg ref_tlb_byp_asi_d;
output reg ref_as_if_user_asi_d;
output reg ref_atomic_asi_d;
output reg ref_blk_asi_d;
output reg ref_dc_diagnstc_asi_d;
output reg ref_dtagv_diagnstc_asi_d;
output reg ref_wr_only_asi_d;
output reg ref_rd_only_asi_d;
output reg ref_unimp_asi_d;
output reg ref_ifu_nontlb_asi_d;
output reg ref_recognized_asi_d;
output reg ref_ifill_tlb_asi_d;
output reg ref_dfill_tlb_asi_d;
output reg ref_rd_only_ltlb_asi_d;
output reg ref_wr_only_ltlb_asi_d;
output reg ref_phy_use_ec_asi_d;
output reg ref_phy_byp_ec_asi_d;
output reg ref_mmu_rd_only_asi_d;
output reg ref_intrpt_disp_asi_d;
output reg ref_dmmu_asi58_d;
output reg ref_immu_asi50_d;
input [7:0] asi_d;
longint unsigned ref_asi_internal_d__dpi;
longint unsigned ref_nucleus_asi_d__dpi;
longint unsigned ref_primary_asi_d__dpi;
longint unsigned ref_secondary_asi_d__dpi;
longint unsigned ref_lendian_asi_d__dpi;
longint unsigned ref_nofault_asi_d__dpi;
longint unsigned ref_quad_asi_d__dpi;
longint unsigned ref_binit_quad_asi_d__dpi;
longint unsigned ref_dcache_byp_asi_d__dpi;
longint unsigned ref_tlb_lng_ltncy_asi_d__dpi;
longint unsigned ref_tlb_byp_asi_d__dpi;
longint unsigned ref_as_if_user_asi_d__dpi;
longint unsigned ref_atomic_asi_d__dpi;
longint unsigned ref_blk_asi_d__dpi;
longint unsigned ref_dc_diagnstc_asi_d__dpi;
longint unsigned ref_dtagv_diagnstc_asi_d__dpi;
longint unsigned ref_wr_only_asi_d__dpi;
longint unsigned ref_rd_only_asi_d__dpi;
longint unsigned ref_unimp_asi_d__dpi;
longint unsigned ref_ifu_nontlb_asi_d__dpi;
longint unsigned ref_recognized_asi_d__dpi;
longint unsigned ref_ifill_tlb_asi_d__dpi;
longint unsigned ref_dfill_tlb_asi_d__dpi;
longint unsigned ref_rd_only_ltlb_asi_d__dpi;
longint unsigned ref_wr_only_ltlb_asi_d__dpi;
longint unsigned ref_phy_use_ec_asi_d__dpi;
longint unsigned ref_phy_byp_ec_asi_d__dpi;
longint unsigned ref_mmu_rd_only_asi_d__dpi;
longint unsigned ref_intrpt_disp_asi_d__dpi;
longint unsigned ref_dmmu_asi58_d__dpi;
longint unsigned ref_immu_asi50_d__dpi;

always @(*) begin
    ref_model_eval(ref_asi_internal_d__dpi, ref_nucleus_asi_d__dpi, ref_primary_asi_d__dpi, ref_secondary_asi_d__dpi, ref_lendian_asi_d__dpi, ref_nofault_asi_d__dpi, ref_quad_asi_d__dpi, ref_binit_quad_asi_d__dpi, ref_dcache_byp_asi_d__dpi, ref_tlb_lng_ltncy_asi_d__dpi, ref_tlb_byp_asi_d__dpi, ref_as_if_user_asi_d__dpi, ref_atomic_asi_d__dpi, ref_blk_asi_d__dpi, ref_dc_diagnstc_asi_d__dpi, ref_dtagv_diagnstc_asi_d__dpi, ref_wr_only_asi_d__dpi, ref_rd_only_asi_d__dpi, ref_unimp_asi_d__dpi, ref_ifu_nontlb_asi_d__dpi, ref_recognized_asi_d__dpi, ref_ifill_tlb_asi_d__dpi, ref_dfill_tlb_asi_d__dpi, ref_rd_only_ltlb_asi_d__dpi, ref_wr_only_ltlb_asi_d__dpi, ref_phy_use_ec_asi_d__dpi, ref_phy_byp_ec_asi_d__dpi, ref_mmu_rd_only_asi_d__dpi, ref_intrpt_disp_asi_d__dpi, ref_dmmu_asi58_d__dpi, ref_immu_asi50_d__dpi, asi_d);
    ref_asi_internal_d = ref_asi_internal_d__dpi[0];
    ref_nucleus_asi_d = ref_nucleus_asi_d__dpi[0];
    ref_primary_asi_d = ref_primary_asi_d__dpi[0];
    ref_secondary_asi_d = ref_secondary_asi_d__dpi[0];
    ref_lendian_asi_d = ref_lendian_asi_d__dpi[0];
    ref_nofault_asi_d = ref_nofault_asi_d__dpi[0];
    ref_quad_asi_d = ref_quad_asi_d__dpi[0];
    ref_binit_quad_asi_d = ref_binit_quad_asi_d__dpi[0];
    ref_dcache_byp_asi_d = ref_dcache_byp_asi_d__dpi[0];
    ref_tlb_lng_ltncy_asi_d = ref_tlb_lng_ltncy_asi_d__dpi[0];
    ref_tlb_byp_asi_d = ref_tlb_byp_asi_d__dpi[0];
    ref_as_if_user_asi_d = ref_as_if_user_asi_d__dpi[0];
    ref_atomic_asi_d = ref_atomic_asi_d__dpi[0];
    ref_blk_asi_d = ref_blk_asi_d__dpi[0];
    ref_dc_diagnstc_asi_d = ref_dc_diagnstc_asi_d__dpi[0];
    ref_dtagv_diagnstc_asi_d = ref_dtagv_diagnstc_asi_d__dpi[0];
    ref_wr_only_asi_d = ref_wr_only_asi_d__dpi[0];
    ref_rd_only_asi_d = ref_rd_only_asi_d__dpi[0];
    ref_unimp_asi_d = ref_unimp_asi_d__dpi[0];
    ref_ifu_nontlb_asi_d = ref_ifu_nontlb_asi_d__dpi[0];
    ref_recognized_asi_d = ref_recognized_asi_d__dpi[0];
    ref_ifill_tlb_asi_d = ref_ifill_tlb_asi_d__dpi[0];
    ref_dfill_tlb_asi_d = ref_dfill_tlb_asi_d__dpi[0];
    ref_rd_only_ltlb_asi_d = ref_rd_only_ltlb_asi_d__dpi[0];
    ref_wr_only_ltlb_asi_d = ref_wr_only_ltlb_asi_d__dpi[0];
    ref_phy_use_ec_asi_d = ref_phy_use_ec_asi_d__dpi[0];
    ref_phy_byp_ec_asi_d = ref_phy_byp_ec_asi_d__dpi[0];
    ref_mmu_rd_only_asi_d = ref_mmu_rd_only_asi_d__dpi[0];
    ref_intrpt_disp_asi_d = ref_intrpt_disp_asi_d__dpi[0];
    ref_dmmu_asi58_d = ref_dmmu_asi58_d__dpi[0];
    ref_immu_asi50_d = ref_immu_asi50_d__dpi[0];
end
endmodule
