`timescale 1ns/1ps
 
module top (
   asi_internal_d, nucleus_asi_d, primary_asi_d, secondary_asi_d, 
   lendian_asi_d, nofault_asi_d, quad_asi_d, binit_quad_asi_d, 
   dcache_byp_asi_d, tlb_lng_ltncy_asi_d, tlb_byp_asi_d, 
   as_if_user_asi_d, atomic_asi_d, blk_asi_d, dc_diagnstc_asi_d, 
   dtagv_diagnstc_asi_d, wr_only_asi_d, rd_only_asi_d, unimp_asi_d, 
   ifu_nontlb_asi_d, recognized_asi_d, ifill_tlb_asi_d, 
   dfill_tlb_asi_d, rd_only_ltlb_asi_d, wr_only_ltlb_asi_d, 
   phy_use_ec_asi_d, phy_byp_ec_asi_d, mmu_rd_only_asi_d, 
   intrpt_disp_asi_d, dmmu_asi58_d, immu_asi50_d, 
   asi_d
   );
input 	[7:0]	asi_d ;
output		asi_internal_d ;
output		nucleus_asi_d ;
output		primary_asi_d ;
output		secondary_asi_d ;
output		lendian_asi_d ;
output		nofault_asi_d ;
output		quad_asi_d ;
output		binit_quad_asi_d ;
output		dcache_byp_asi_d ;
output		tlb_lng_ltncy_asi_d ;
output		tlb_byp_asi_d ;
output		as_if_user_asi_d ;
output		atomic_asi_d ;
output		blk_asi_d ;
output		dc_diagnstc_asi_d;
output		dtagv_diagnstc_asi_d;
output		wr_only_asi_d ;
output		rd_only_asi_d ;
output		unimp_asi_d ;
output		ifu_nontlb_asi_d ;	
output		recognized_asi_d ;
output		ifill_tlb_asi_d ;	
output		dfill_tlb_asi_d ;	
output		rd_only_ltlb_asi_d ;	
output		wr_only_ltlb_asi_d ;	
output		phy_use_ec_asi_d ;
output		phy_byp_ec_asi_d ;
output		mmu_rd_only_asi_d ;	
output		intrpt_disp_asi_d ;
output		dmmu_asi58_d ;
output    immu_asi50_d;
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
   wire unimp_CD_prm;
   wire unimp_CD_sec;
wire	dtsb_8k_ptr, dtsb_64k_ptr, dtsb_dir_ptr;
wire	itsb_8k_ptr, itsb_64k_ptr;
assign	dtsb_8k_ptr = (asi_d[7:0] == 8'h59) ;
assign	dtsb_64k_ptr = (asi_d[7:0] == 8'h5A) ;
assign	dtsb_dir_ptr = (asi_d[7:0] == 8'h5B) ;
assign	itsb_8k_ptr = (asi_d[7:0] == 8'h51) ;
assign	itsb_64k_ptr = (asi_d[7:0] == 8'h52) ;
assign	mmu_rd_only_asi_d =
	dtsb_8k_ptr | dtsb_64k_ptr | dtsb_dir_ptr | itsb_8k_ptr | itsb_64k_ptr ;
assign intrpt_disp_asi_d = (asi_d[7:0] == 8'h73) ; 
assign	dmmu_asi58_d =	(asi_d[7:0] == 8'h58) ; 
assign  immu_asi50_d =  (asi_d[7:0] == 8'h50) ;
assign	asi_internal_d =
	(asi_d[7:0] == 8'h40) |	
	(asi_d[7:0] == 8'h45) |	
	(asi_d[7:0] == 8'h50) | 
	itsb_8k_ptr	      | 
	itsb_64k_ptr	      | 
	dmmu_asi58_d |
	(asi_d[7:0] == 8'h21) | 
	(asi_d[7:0] == 8'h20) | 
	(asi_d[7:0] == 8'h25) | 
	(asi_d[7:0] == 8'h4F) | 
	dtsb_8k_ptr 	      | 
	dtsb_64k_ptr	      | 
	dtsb_dir_ptr	      | 
	(asi_d[7:0] == 8'h72) | 
	intrpt_disp_asi_d     | 
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
	dc_diagnstc_asi_d     | 
	dtagv_diagnstc_asi_d  | 
	tlb_lng_ltncy_asi_d   |
	ifu_nontlb_asi_d      ;	
assign	ifu_nontlb_asi_d = 
	(asi_d[7:0] == 8'h42) | 
	(asi_d[7:0] == 8'h43) | 
	(asi_d[7:0] == 8'h4B) | 
	(asi_d[7:0] == 8'h4C) | 
	(asi_d[7:0] == 8'h4D) | 
	(asi_d[7:0] == 8'h66) | 
	(asi_d[7:0] == 8'h67) ; 
assign	dc_diagnstc_asi_d = (asi_d[7:0] == 8'h46) ;
assign	dtagv_diagnstc_asi_d = (asi_d[7:0] == 8'h47) ;
assign	idemap = (asi_d[7:0] == 8'h57) ; 
assign	ddemap = (asi_d[7:0] == 8'h5F) ; 
assign	ddata_in = (asi_d[7:0] == 8'h5C) ; 
assign	ddaccess = (asi_d[7:0] == 8'h5D) ; 
assign	dtag_read = (asi_d[7:0] == 8'h5E) ; 
assign	idata_in = (asi_d[7:0] == 8'h54) ; 
assign	idaccess = (asi_d[7:0] == 8'h55) ; 
assign	invld_all = (asi_d[7:0] == 8'h60) ; 
assign	itag_read = (asi_d[7:0] == 8'h56) ; 
assign	tlb_lng_ltncy_asi_d = 
	idemap 		| ddemap 	| ddata_in 	| 
	ddaccess 	| dtag_read 	| idata_in 	| 
	idaccess 	| invld_all 	| itag_read 	;
assign	wr_only_ltlb_asi_d = 
	ddata_in 	|	idata_in 	|
	idemap		|	ddemap		|
	invld_all ;
assign	rd_only_ltlb_asi_d =
	dtag_read	|	itag_read	;
assign	ifill_tlb_asi_d =	
	idata_in	| 	idaccess	;
assign	dfill_tlb_asi_d =	
	ddata_in	|	ddaccess	;
assign	nucleus_asi_exact_d =
	(asi_d[7:0] == 8'h04) |	
	(asi_d[7:0] == 8'h0C) ; 
assign	nucleus_asi_d =
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
assign	primary_asi_d =
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
assign	as_if_user_asi_d = asi_if_user_prim_all_d | asi_if_user_sec_all_d |
blk_asif_usr_p | blk_asif_usr_plittle | blk_asif_usr_s | blk_asif_usr_slittle ;
assign	sec_asi_exact_d =
	(asi_d[7:0] == 8'h81) | 
	(asi_d[7:0] == 8'h89) ; 
assign	secondary_asi_d =
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
assign	lendian_asi_d =
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
assign	nofault_asi_d =
	(asi_d[7:0] == 8'h82) |	
	(asi_d[7:0] == 8'h8A) |	
	(asi_d[7:0] == 8'h83) | 
	(asi_d[7:0] == 8'h8B) ; 
assign	binit_nucleus_d =
	(asi_d[7:0] == 8'h27) ;	
assign	binit_nucleus_little_d =
	(asi_d[7:0] == 8'h2F) ;	
assign	binit_quad_asi_d =
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
assign	quad_asi_d =
	binit_quad_asi_d      | 
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
assign	phy_use_ec_asi_d = phy_use_ec_asi ;
assign	phy_byp_ec_asi_d = phy_byp_ec_asi ;
assign	tlb_byp_asi_d = 
		phy_byp_ec_asi | phy_use_ec_asi | 
		quad_ldd_real  | quad_ldd_real_little ;
assign	atomic_asi_d = nucleus_asi_exact_d | prim_asi_exact_d | sec_asi_exact_d | 
		asi_if_user_prim_d | asi_if_user_sec_d | phy_use_ec_asi ;
assign	dcache_byp_asi_d = tlb_byp_asi_d ;
assign	rd_only_asi_d =
	(asi_d[7:0] == 8'h82) |	
	(asi_d[7:0] == 8'h8A) |	
	(asi_d[7:0] == 8'h83) | 
	(asi_d[7:0] == 8'h8B) | 
	(asi_d[7:0] == 8'h74) ; 
assign	wr_only_asi_d =
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
assign	blk_asi_d = 
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
assign	unimp_asi_d =
 	unimp_C | unimp_D | 
	blk_cmt_p | blk_cmt_s ;
assign	recognized_asi_d = 
	asi_internal_d | nucleus_asi_d |  primary_asi_d | secondary_asi_d | lendian_asi_d |
	nofault_asi_d | quad_asi_d | tlb_byp_asi_d | unimp_asi_d | blk_asi_d ;
endmodule

