`timescale 1ns/1ps
 
module ref_lsu_asi_decode (
   ref_asi_internal_d, ref_nucleus_asi_d, ref_primary_asi_d, ref_secondary_asi_d, 
   ref_lendian_asi_d, ref_nofault_asi_d, ref_quad_asi_d, ref_binit_quad_asi_d, 
   ref_dcache_byp_asi_d, ref_tlb_lng_ltncy_asi_d, ref_tlb_byp_asi_d, 
   ref_as_if_user_asi_d, ref_atomic_asi_d, ref_blk_asi_d, ref_dc_diagnstc_asi_d, 
   ref_dtagv_diagnstc_asi_d, ref_wr_only_asi_d, ref_rd_only_asi_d, ref_unimp_asi_d, 
   ref_ifu_nontlb_asi_d, ref_recognized_asi_d, ref_ifill_tlb_asi_d, 
   ref_dfill_tlb_asi_d, ref_rd_only_ltlb_asi_d, ref_wr_only_ltlb_asi_d, 
   ref_phy_use_ec_asi_d, ref_phy_byp_ec_asi_d, ref_mmu_rd_only_asi_d, 
   ref_intrpt_disp_asi_d, ref_dmmu_asi58_d, ref_immu_asi50_d, 
   asi_d
   );
input 	[7:0]	asi_d ;
output		ref_asi_internal_d ;
output		ref_nucleus_asi_d ;
output		ref_primary_asi_d ;
output		ref_secondary_asi_d ;
output		ref_lendian_asi_d ;
output		ref_nofault_asi_d ;
output		ref_quad_asi_d ;
output		ref_binit_quad_asi_d ;
output		ref_dcache_byp_asi_d ;
output		ref_tlb_lng_ltncy_asi_d ;
output		ref_tlb_byp_asi_d ;
output		ref_as_if_user_asi_d ;
output		ref_atomic_asi_d ;
output		ref_blk_asi_d ;
output		ref_dc_diagnstc_asi_d;
output		ref_dtagv_diagnstc_asi_d;
output		ref_wr_only_asi_d ;
output		ref_rd_only_asi_d ;
output		ref_unimp_asi_d ;
output		ref_ifu_nontlb_asi_d ;	
output		ref_recognized_asi_d ;
output		ref_ifill_tlb_asi_d ;	
output		ref_dfill_tlb_asi_d ;	
output		ref_rd_only_ltlb_asi_d ;	
output		ref_wr_only_ltlb_asi_d ;	
output		ref_phy_use_ec_asi_d ;
output		ref_phy_byp_ec_asi_d ;
output		ref_mmu_rd_only_asi_d ;	
output		ref_intrpt_disp_asi_d ;
output		ref_dmmu_asi58_d ;
output		ref_immu_asi50_d;
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
assign	ref_asi_internal_d =
	(asi_d[7:0] == 8'h40) |	
	(asi_d[7:0] == 8'h45) |	
	(asi_d[7:0] == 8'h50) | 
	itsb_8k_ptr	      | 
	itsb_64k_ptr	      | 
	ref_dmmu_asi58_d |
	(asi_d[7:0] == 8'h21) | 
	(asi_d[7:0] == 8'h20) | 
	(asi_d[7:0] == 8'h25) | 
	(asi_d[7:0] == 8'h4F) | 
	dtsb_8k_ptr 	      | 
	dtsb_64k_ptr	      | 
	dtsb_dir_ptr	      | 
	(asi_d[7:0] == 8'h72) | 
	ref_intrpt_disp_asi_d     | 
	(asi_d[7:0] == 8'h74) | 
	(asi_d[7:0] == 8'h44) | 
	(asi_d[7:0] == 8'h31) | 
	(asi_d[7:0] == 8'h32) | 
	(asi_d[7:0] == 8'h39) | 
	(asi_d[7:0] == 8'h3A) | 
	(asi_d[7:0] == 8'h33) | 
	(asi_d[7:0] == 8'h3B) | 
	(asi_d[7:0] == 8'h35) | 
	(asi_d[7:0] == 8'h36) | 
	(asi_d[7:0] == 8'h3D) | 
	(asi_d[7:0] == 8'h3E) | 
	(asi_d[7:0] == 8'h37) | 
	(asi_d[7:0] == 8'h3F) | 
	ref_dc_diagnstc_asi_d     | 
	ref_dtagv_diagnstc_asi_d  | 
	ref_tlb_lng_ltncy_asi_d   |
	ref_ifu_nontlb_asi_d      ;	
assign	ref_ifu_nontlb_asi_d = 
	(asi_d[7:0] == 8'h42) | 
	(asi_d[7:0] == 8'h43) | 
	(asi_d[7:0] == 8'h4B) | 
	(asi_d[7:0] == 8'h4C) | 
	(asi_d[7:0] == 8'h4D) | 
	(asi_d[7:0] == 8'h66) | 
	(asi_d[7:0] == 8'h67) ; 
assign	ref_dc_diagnstc_asi_d = (asi_d[7:0] == 8'h46) ;
assign	ref_dtagv_diagnstc_asi_d = (asi_d[7:0] == 8'h47) ;
assign	idemap = (asi_d[7:0] == 8'h57) ; 
assign	ddemap = (asi_d[7:0] == 8'h5F) ; 
assign	ddata_in = (asi_d[7:0] == 8'h5C) ; 
assign	ddaccess = (asi_d[7:0] == 8'h5D) ; 
assign	dtag_read = (asi_d[7:0] == 8'h5E) ; 
assign	idata_in = (asi_d[7:0] == 8'h54) ; 
assign	idaccess = (asi_d[7:0] == 8'h55) ; 
assign	invld_all = (asi_d[7:0] == 8'h60) ; 
assign	itag_read = (asi_d[7:0] == 8'h56) ; 
assign	ref_tlb_lng_ltncy_asi_d = 
	idemap 		| ddemap 	| ddata_in 	| 
	ddaccess 	| dtag_read 	| idata_in 	| 
	idaccess 	| invld_all 	| itag_read 	;
assign	ref_wr_only_ltlb_asi_d = 
	ddata_in 	|	idata_in 	|
	idemap		|	ddemap		|
	invld_all ;
assign	ref_rd_only_ltlb_asi_d =
	dtag_read	|	itag_read	;
assign	ref_ifill_tlb_asi_d =	
	idata_in	| 	idaccess	;
assign	ref_dfill_tlb_asi_d =	
	ddata_in	|	ddaccess	;
assign	nucleus_asi_exact_d =
	(asi_d[7:0] == 8'h04) |	
	(asi_d[7:0] == 8'h0C) ; 
assign	ref_nucleus_asi_d =
	 nucleus_asi_exact_d |
	(asi_d[7:0] == 8'h24) | 
	(asi_d[7:0] == 8'h2C) ; 
assign	asi_if_user_prim_d =
	(asi_d[7:0] == 8'h10) |	
	(asi_d[7:0] == 8'h18) ;	
assign	asi_if_user_prim_all_d =
	 asi_if_user_prim_d   |		
	(asi_d[7:0] == 8'h22) |	
	(asi_d[7:0] == 8'h2A) ;	
assign	prim_asi_exact_d =
	(asi_d[7:0] == 8'h80) |	
	(asi_d[7:0] == 8'h88) ;	
assign	ref_primary_asi_d =
	 asi_if_user_prim_all_d   |	
	 prim_asi_exact_d     |	
	(asi_d[7:0] == 8'h82) |	
	(asi_d[7:0] == 8'h8A) |	
	(asi_d[7:0] == 8'hE2) |	
	(asi_d[7:0] == 8'hEA) |	
	blk_asif_usr_p | blk_asif_usr_plittle | 
	blk_plittle | blk_p | 
	blk_cmt_p |	
  unimp_CD_prm ;  
assign	asi_if_user_sec_d =
	(asi_d[7:0] == 8'h11) | 
	(asi_d[7:0] == 8'h19) ; 
assign	asi_if_user_sec_all_d =
	 asi_if_user_sec_d   |		
	(asi_d[7:0] == 8'h23) |	
	(asi_d[7:0] == 8'h2B) ;	
assign	ref_as_if_user_asi_d = asi_if_user_prim_all_d | asi_if_user_sec_all_d |
blk_asif_usr_p | blk_asif_usr_plittle | blk_asif_usr_s | blk_asif_usr_slittle ;
assign	sec_asi_exact_d =
	(asi_d[7:0] == 8'h81) | 
	(asi_d[7:0] == 8'h89) ; 
assign	ref_secondary_asi_d =
	 asi_if_user_sec_all_d    |
	 sec_asi_exact_d      |		
	(asi_d[7:0] == 8'h83) | 
	(asi_d[7:0] == 8'h8B) | 
	(asi_d[7:0] == 8'hE3) |	
	(asi_d[7:0] == 8'hEB) |	
	blk_asif_usr_s | blk_asif_usr_slittle | 
	blk_slittle |  blk_s | 
	blk_cmt_s |  
  unimp_CD_sec; 
assign	ref_lendian_asi_d =
	(asi_d[7:0] == 8'h0C) | 
	(asi_d[7:0] == 8'h2C) | 
	(asi_d[7:0] == 8'h18) |	
	(asi_d[7:0] == 8'h8A) |	
	(asi_d[7:0] == 8'h8B) | 
	(asi_d[7:0] == 8'h2A) |	
	(asi_d[7:0] == 8'hEA) |	
	(asi_d[7:0] == 8'h19) | 
	(asi_d[7:0] == 8'h89) | 
	(asi_d[7:0] == 8'h88) |	
	(asi_d[7:0] == 8'h2B) |	
	(asi_d[7:0] == 8'hEB) |	
	real_mem_little |
	real_io_little	|
	blk_asif_usr_plittle  | blk_asif_usr_slittle |	
	blk_plittle	      | blk_slittle |		
	quad_ldd_real_little  | 
	binit_nucleus_little_d ;
assign	ref_nofault_asi_d =
	(asi_d[7:0] == 8'h82) |	
	(asi_d[7:0] == 8'h8A) |	
	(asi_d[7:0] == 8'h83) | 
	(asi_d[7:0] == 8'h8B) ; 
assign	binit_nucleus_d =
	(asi_d[7:0] == 8'h27) ;	
assign	binit_nucleus_little_d =
	(asi_d[7:0] == 8'h2F) ;	
assign	ref_binit_quad_asi_d =
   	binit_nucleus_d |	
	binit_nucleus_little_d |
	(asi_d[7:0] == 8'h22) |	
	(asi_d[7:0] == 8'h2A) |	
	(asi_d[7:0] == 8'h23) |	
	(asi_d[7:0] == 8'h2B) |	
	(asi_d[7:0] == 8'hE2) |	
	(asi_d[7:0] == 8'hEA) |	
	(asi_d[7:0] == 8'hE3) |	
	(asi_d[7:0] == 8'hEB) ;	
assign	quad_ldd_real = 
	(asi_d[7:0] == 8'h26) ; 
assign	quad_ldd_real_little = 
	(asi_d[7:0] == 8'h2E) ; 
assign	ref_quad_asi_d =
	ref_binit_quad_asi_d      | 
	quad_ldd_real 	      | 
	quad_ldd_real_little  | 
	(asi_d[7:0] == 8'h24) | 
	(asi_d[7:0] == 8'h2C) ; 
assign	real_io_little = (asi_d[7:0] == 8'h1D) ;
assign	real_mem_little = (asi_d[7:0] == 8'h1C) ;
assign	phy_byp_ec_asi =
	(asi_d[7:0] == 8'h15) |	
	real_io_little ;	
assign	phy_use_ec_asi =
	(asi_d[7:0] == 8'h14) |	
	real_mem_little ;	
assign	ref_phy_use_ec_asi_d = phy_use_ec_asi ;
assign	ref_phy_byp_ec_asi_d = phy_byp_ec_asi ;
assign	ref_tlb_byp_asi_d = 
		phy_byp_ec_asi | phy_use_ec_asi | 
		quad_ldd_real  | quad_ldd_real_little ;
assign	ref_atomic_asi_d = nucleus_asi_exact_d | prim_asi_exact_d | sec_asi_exact_d | 
		asi_if_user_prim_d | asi_if_user_sec_d | phy_use_ec_asi ;
assign	ref_dcache_byp_asi_d = ref_tlb_byp_asi_d ;
assign	ref_rd_only_asi_d =
	(asi_d[7:0] == 8'h82) |	
	(asi_d[7:0] == 8'h8A) |	
	(asi_d[7:0] == 8'h83) | 
	(asi_d[7:0] == 8'h8B) | 
	(asi_d[7:0] == 8'h74) ; 
assign	ref_wr_only_asi_d =
	(asi_d[7:0] == 8'h73) ; 
assign	blk_asif_usr_p = (asi_d[7:0] == 8'h16) ; 
assign	blk_asif_usr_plittle = (asi_d[7:0] == 8'h1E) ; 
assign	blk_asif_usr_s = (asi_d[7:0] == 8'h17) ; 
assign	blk_asif_usr_slittle = (asi_d[7:0] == 8'h1F) ; 
assign	blk_plittle = (asi_d[7:0] == 8'hF8) ; 
assign	blk_slittle = (asi_d[7:0] == 8'hF9) ; 
assign	blk_cmt_p = (asi_d[7:0] == 8'hE0) ; 
assign	blk_cmt_s = (asi_d[7:0] == 8'hE1) ; 
assign	blk_p = (asi_d[7:0] == 8'hF0) ; 
assign	blk_s = (asi_d[7:0] == 8'hF1) ; 
assign	ref_blk_asi_d = 
	blk_asif_usr_p 	| blk_asif_usr_s |
	blk_plittle	| blk_slittle	 |
	blk_p		| blk_s		 |
	blk_asif_usr_plittle  | blk_asif_usr_slittle |	
	blk_plittle	      | blk_slittle ;		
wire	unimp_C ;
assign	unimp_C =
	((asi_d[7:4]==4'hC) & 
		~((asi_d[3:0]==4'h6) |
		  (asi_d[3:0]==4'h7) |
		  (asi_d[3:0]==4'hE) |
		  (asi_d[3:0]==4'hF))) ;
wire	unimp_D ;
assign	unimp_D =
	((asi_d[7:4]==4'hD) & 
		~((asi_d[3:0]==4'h4) |
		  (asi_d[3:0]==4'h5) |
		  (asi_d[3:0]==4'h6) |
		  (asi_d[3:0]==4'h7) |
		  (asi_d[3:0]==4'hC) |
		  (asi_d[3:0]==4'hD) |
		  (asi_d[3:0]==4'hE) |
		  (asi_d[3:0]==4'hF))) ;
assign  unimp_CD_prm =
(asi_d[7:0] == 8'hC0) |
(asi_d[7:0] == 8'hC2) |
(asi_d[7:0] == 8'hC4) |
(asi_d[7:0] == 8'hC8) |
(asi_d[7:0] == 8'hCA) |
(asi_d[7:0] == 8'hCC) |
(asi_d[7:0] == 8'hD0) |
(asi_d[7:0] == 8'hD2) |
(asi_d[7:0] == 8'hD8) |
(asi_d[7:0] == 8'hDA) ;
assign  unimp_CD_sec = 
(asi_d[7:0] == 8'hC1) |
(asi_d[7:0] == 8'hC3) |
(asi_d[7:0] == 8'hC5) |
(asi_d[7:0] == 8'hC9) |
(asi_d[7:0] == 8'hCB) |
(asi_d[7:0] == 8'hCD) |
(asi_d[7:0] == 8'hD1) |
(asi_d[7:0] == 8'hD3) |
(asi_d[7:0] == 8'hD9) |
(asi_d[7:0] == 8'hDB) ;
assign	ref_unimp_asi_d =
 	unimp_C | unimp_D | 
	blk_cmt_p | blk_cmt_s ;
assign	ref_recognized_asi_d = 
	ref_asi_internal_d | ref_nucleus_asi_d |  ref_primary_asi_d | ref_secondary_asi_d | ref_lendian_asi_d |
	ref_nofault_asi_d | ref_quad_asi_d | ref_tlb_byp_asi_d | ref_unimp_asi_d | ref_blk_asi_d ;
endmodule

