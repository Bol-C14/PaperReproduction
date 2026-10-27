`timescale 1ns/1ps

module tessera_sdram_ctrl (
	rst,
	clk,
	init_req,
	init_enter,
	init_exit,
	refresh_req,
	refresh_enter,
	refresh_exit,
	write_req,
	write_enter,
	write_valid,
	write_exit,
	write_address,
	read_req,
	read_enter,
	read_valid,
	read_exit,
	read_address,
	dma_req,
	dma_enter,
	dma_valid,
	dma_exit,
	dma_address,
	ctrl_cmd,
	ctrl_cs,
	ctrl_ba,
	ctrl_a,
	option
);
	input		rst;
	input		clk;
	input		init_req;
	output		init_enter;
	output		init_exit;
	input		refresh_req;
	output		refresh_enter;
	output		refresh_exit;
	input		write_req;
	output		write_enter;
	output		write_valid;
	output		write_exit;
	input	[31:0]	write_address;
	input		read_req;
	output		read_enter;
	output		read_valid;
	output		read_exit;
	input	[31:0]	read_address;
	input		dma_req;
	output		dma_enter;
	output		dma_valid;
	output		dma_exit;
	input	[31:0]	dma_address;
	output	[4:0]	ctrl_cmd;
	output	[1:0]	ctrl_cs;
	output	[1:0]	ctrl_ba;
	output	[12:0]	ctrl_a;
	input		option;
	parameter COMMAND_RES =5'b01000;
	parameter COMMAND_DES =5'b10000;
	parameter COMMAND_PAL =5'b11101;
	parameter COMMAND_MRS =5'b11111;
	parameter COMMAND_REF =5'b11110;
	parameter COMMAND_ACT =5'b11100;
	parameter COMMAND_WRI =5'b11011;
	parameter COMMAND_REA =5'b11010;
	parameter S0 ='d0;
	parameter S1 ='d1;
	parameter S2 ='d2;
	parameter S3 ='d3;
	parameter S4 ='d4;
	parameter S5 ='d5;
	parameter S6 ='d6;
	parameter S7 ='d7;
	parameter S8 ='d8;
	parameter S9 ='d9;
	parameter S10 ='d10;
	parameter S11 ='d11;
	parameter S12 ='d12;
	parameter S13 ='d13;
	parameter S14 ='d14;
	parameter S15 ='d15;
	wire	[31:0]	next_wri_adr;
	wire	[31:0]	next_rea_adr;
	wire	[31:0]	next_dma_adr;
	wire	[11:0]	next_wri_adr_col;
	wire	[11:0]	next_rea_adr_col;
	wire	[11:0]	next_dma_adr_col;
	wire	[12:0]	next_wri_adr_row;
	wire	[12:0]	next_rea_adr_row;
	wire	[12:0]	next_dma_adr_row;
	wire	[1:0]	next_wri_ba;
	wire	[1:0]	next_rea_ba;
	wire	[1:0]	next_dma_ba;
	wire	[1:0]	next_wri_cs;
	wire	[1:0]	next_rea_cs;
	wire	[1:0]	next_dma_cs;
	reg		pre_option;
	always @(posedge clk) pre_option <= option;
	assign next_wri_adr = {7'h00,pre_option,write_address[23:0]};	
	assign next_rea_adr = {7'h00,pre_option,read_address[23:0]};	
	assign next_dma_adr = {7'h00,pre_option,dma_address[23:0]};	
 	assign next_wri_adr_col		= {3'b000,next_wri_adr[9:2],1'b0};
	assign next_rea_adr_col		= {3'b000,next_rea_adr[9:2],1'b0};
	assign next_dma_adr_col		= {3'b000,next_dma_adr[9:2],1'b0};
	assign next_wri_adr_row		= {1'b0,next_wri_adr[21:10]};
	assign next_rea_adr_row		= {1'b0,next_rea_adr[21:10]};
	assign next_dma_adr_row		= {1'b0,next_dma_adr[21:10]};
	assign next_wri_ba		= next_wri_adr[23:22];
	assign next_rea_ba		= next_rea_adr[23:22];
	assign next_dma_ba		= next_dma_adr[23:22];
	assign next_wri_cs		= {next_wri_adr[24],!next_wri_adr[24]};
	assign next_rea_cs		= {next_rea_adr[24],!next_rea_adr[24]};
	assign next_dma_cs		= {next_dma_adr[24],!next_dma_adr[24]};
	wire		init_eve;
	wire		write_eve;
	wire		dma_eve;
	wire		refresh_eve;
	wire		read_eve;
	wire	[4:0]	next_execute;
	reg	[4:0]	gnt_execute;
	wire		init_syn;
	wire		refresh_syn;
	wire		dma_syn;
	wire		write_syn;
	wire		read_syn;
	wire		init_fin;
	wire		refresh_fin;
	wire		dma_fin;
	wire		write_fin;
	wire		read_fin;
	reg	[4:0]	ini_cmd;
	reg	[1:0]	ini_cs;
	reg	[1:0]	ini_ba;
	reg	[12:0]	ini_adr;
	reg	[3:0]	ini_sta;
	reg	[3:0]	ini_sub;
	reg		timer_enable;
	reg	[15:0]	timer;
	reg		timer_expire;
	reg	[4:0]	ref_cmd;
	reg	[1:0]	ref_cs;
	reg	[1:0]	ref_ba;
	reg	[12:0]	ref_adr;
	reg	[3:0]	ref_sta;
	reg	[4:0]	dma_cmd;
	reg	[1:0]	dma_cs;
	reg	[1:0]	dma_ba;
	reg	[12:0]	dma_adr;
	reg	[3:0]	dma_sta;
	reg	[3:0]	dma_sub;
	reg		dma_val;
	reg	[4:0]	wri_cmd;
	reg	[1:0]	wri_cs;
	reg	[1:0]	wri_ba;
	reg	[12:0]	wri_adr;
	reg	[3:0]	wri_sta;
	reg	[3:0]	wri_sub;
	reg		wri_val;
	reg	[4:0]	rea_cmd;
	reg	[1:0]	rea_cs;
	reg	[1:0]	rea_ba;
	reg	[12:0]	rea_adr;
	reg	[3:0]	rea_sta;
	reg	[3:0]	rea_sub;
	reg		rea_val;
	reg		init_enter;
	reg		refresh_enter;
	reg		dma_enter;
	reg		write_enter;
	reg		read_enter;
	reg		init_exit;
	reg		refresh_exit;
	reg		dma_exit;		
	reg		write_exit;
	reg		read_exit;
	assign    init_eve	=    init_req && !(   init_exit||   init_fin);
	assign   write_eve	=   write_req && !(  write_exit||  write_fin);
	assign     dma_eve	=     dma_req && !(    dma_exit||    dma_fin);
	assign refresh_eve	= refresh_req && !(refresh_exit||refresh_fin);
	assign    read_eve	=    read_req && !(   read_exit||   read_fin);
	assign next_execute = {
		 !(init_eve||refresh_eve||dma_eve||write_eve) &&    read_eve,	
		 !(init_eve||refresh_eve||dma_eve)            &&   write_eve,
		 !(init_eve||refresh_eve)                     &&     dma_eve,
		 !(init_eve)                                  && refresh_eve,
		                                                    init_eve	
	};
	always @(posedge clk or posedge rst)
		if (rst) gnt_execute <= 5'b00000;
		else if (
			!(
				|(gnt_execute[4:0]&{read_eve,write_eve,dma_eve,refresh_eve,init_eve})
			)
		) gnt_execute <= next_execute;
	assign    init_syn	= (gnt_execute[0]&&(ini_sta==S0));
	assign refresh_syn	= (gnt_execute[1]&&(ref_sta==S0));
	assign     dma_syn	= (gnt_execute[2]&&(dma_sta==S0));
	assign   write_syn	= (gnt_execute[3]&&(wri_sta==S0));
	assign    read_syn	= (gnt_execute[4]&&(rea_sta==S0));
	assign    init_fin	= (gnt_execute[0]&&(ini_sta==S15));
	assign refresh_fin	= (gnt_execute[1]&&(ref_sta==S6));
	assign     dma_fin	= (gnt_execute[2]&&(dma_sta==S6));
	assign   write_fin	= (gnt_execute[3]&&(wri_sta==S6));
	assign    read_fin	= (gnt_execute[4]&&(rea_sta==S6));
	always @(posedge clk or posedge rst)
		if (rst) begin
			init_enter	<= 1'b0;
			refresh_enter	<= 1'b0;
			dma_enter	<= 1'b0;
			write_enter	<= 1'b0;
			read_enter	<= 1'b0;
			init_exit	<= 1'b0;
			refresh_exit	<= 1'b0;
			dma_exit	<= 1'b0;
			write_exit	<= 1'b0;
			read_exit	<= 1'b0;
		end
		else begin
			init_enter	<=    init_syn;
			refresh_enter	<= refresh_syn;
			dma_enter	<=     dma_syn;
			write_enter	<=   write_syn;
			read_enter	<=    read_syn;
			init_exit	<= (!   init_req) ? 1'b0: (   init_fin) ? 1'b1:    init_exit;		
			refresh_exit	<= (!refresh_req) ? 1'b0: (refresh_fin) ? 1'b1: refresh_exit;		
			dma_exit	<= (!    dma_req) ? 1'b0: (    dma_fin) ? 1'b1:     dma_exit;		
			write_exit	<= (!  write_req) ? 1'b0: (  write_fin) ? 1'b1:   write_exit;		
			read_exit	<= (!   read_req) ? 1'b0: (   read_fin) ? 1'b1:    read_exit;		
		end
	assign ctrl_cmd = ~(ini_cmd | ref_cmd | dma_cmd | wri_cmd | rea_cmd);
	assign ctrl_cs		= ini_cs  | ref_cs  | dma_cs  | wri_cs  | rea_cs;
	assign ctrl_ba		= ini_ba  | ref_ba  | dma_ba  | wri_ba  | rea_ba;
	assign ctrl_a		= ini_adr | ref_adr | dma_adr | wri_adr | rea_adr;
	assign dma_valid	= dma_val;
	assign read_valid	= rea_val;
	assign write_valid	= wri_val;
	always @(posedge clk or posedge rst)
		if (rst)  timer_enable <= 1'b0;
		else      timer_enable <= (ini_sta==S1)||(ini_sta==S14);
	always @(posedge clk or posedge rst)
		if (rst) 		timer <= 16'd0;
		else if (!timer_enable)	timer <= 16'd0;
		else			timer <= timer + 16'd1;
	always @(posedge clk or posedge rst)
		if (rst)		timer_expire <= 1'b0;
		else if (!timer_enable)	timer_expire <= 1'b0;
		else 			timer_expire <= (timer==16'd16384);
	always @(posedge clk or posedge rst)
		if (rst) begin
			ini_cmd	<= COMMAND_RES;
			ini_cs	<= 2'b11;		
			ini_ba	<= 2'b00;
			ini_adr	<= 13'd0;
			ini_sta	<= S0;
			ini_sub <= S0;
		end
		else if (!gnt_execute[0]) begin
			ini_cmd	<= COMMAND_DES;
			ini_cs	<= 2'b00;
			ini_ba	<= 2'b00;
			ini_adr	<= 13'd0;
			ini_sta	<= S0;
			ini_sub <= S0;
		end
		else case (ini_sta[3:0])
			S0: begin							
				ini_cmd	<= COMMAND_DES;
				ini_cs	<= 2'b11; 
				ini_ba	<= 2'b00;
				ini_adr	<= 13'd0;
				ini_sta	<= ini_sta + 4'd1;
			end
			S1: begin
				ini_cmd	<= COMMAND_DES;
				if (timer_expire) ini_sta <= ini_sta + 4'd1;		
			end
			S2: begin							
				ini_cmd	<= COMMAND_PAL;
				ini_adr[10] <= 1'b1;
				ini_sta	<= ini_sta + 4'd1;
			end
			S3: begin
				ini_cmd	<= COMMAND_DES;
				ini_sta	<= ini_sta + 4'd1;
			end
			S4: begin
				ini_cmd	<= COMMAND_REF;
				ini_sta	<= ini_sta + 4'd1;
			end
			S5: begin
				ini_cmd	<= COMMAND_DES;
				ini_sta	<= ini_sta + 4'd1;
			end
			S6,S7,S8: begin
				ini_cmd	<= COMMAND_DES;
				ini_sta	<= ini_sta + 4'd1;
			end
			S9: begin
				ini_cmd	<= COMMAND_DES;
				if (ini_sub==S7) begin
					ini_sub <= S0;
					ini_sta	<= ini_sta + 4'd1;
				end
				else begin
					ini_sub <= ini_sub + 3'd1;
					ini_sta	<= S4;
				end
			end
			S10: begin
				ini_cmd	<= COMMAND_MRS;
				ini_ba	<= 2'b00;		
                                ini_adr <= {
				       5'b0_0000,		
				       1'b0,			
				       3'b011,			
				       1'b0,			
				       3'b001			
				};
				ini_sta	<= ini_sta + 4'd1;
			end
			S11: begin
				ini_cmd	<= COMMAND_DES;
				ini_sta	<= ini_sta + 4'd1;
			end
			S12,S13: begin
				ini_cmd	<= COMMAND_DES;
				ini_sta	<= ini_sta + 4'd1;
			end
			S14: begin
				ini_cmd	<= COMMAND_DES;
				if (timer_expire) ini_sta <= ini_sta + 4'd1;		
			end
			S15: begin
				ini_cmd	<= COMMAND_DES;
				ini_sta <= S0;				
			end
			default: begin
				ini_cmd	<= COMMAND_DES;
				ini_cs	<= 2'b00;
				ini_ba	<= 2'b00;
				ini_adr	<= 13'd0;
				ini_sta	<= S0;
			end
		endcase
	always @(posedge clk or posedge rst)
		if (rst) begin
			ref_cmd	<= COMMAND_RES;
			ref_cs	<= 2'b11; 
			ref_ba	<= 2'b00;
			ref_adr	<= 13'd0;
			ref_sta	<= S0;
		end
		else if (!gnt_execute[1]) begin
			ref_cmd	<= COMMAND_DES;
			ref_cs	<= 2'b00;
			ref_ba	<= 2'b00;
			ref_adr	<= 13'd0;
			ref_sta	<= S0;
		end
		else case (ref_sta[3:0])
			S0: begin
				ref_cmd	<= COMMAND_PAL;
				ref_cs	<= 2'b11;				
				ref_adr	<= {2'b00,1'b1,10'b00_0000_0000};	
				ref_sta	<= ref_sta + 4'd1;
			end
			S1: begin
				ref_cmd	<= COMMAND_DES; 
				ref_sta	<= ref_sta + 4'd1;
			end
			S2: begin
				ref_cmd	<= COMMAND_REF;
				ref_sta	<= ref_sta + 4'd1;
			end
			S3,S4,S5: begin 
				ref_cmd	<= COMMAND_DES;
				ref_sta	<= ref_sta + 4'd1;
			end
			S6: begin
				ref_cmd	<= COMMAND_DES;
				ref_sta <= S0;				
			end
			default: begin
				ref_cmd	<= COMMAND_DES;
				ref_cs	<= 2'b00;
				ref_ba	<= 2'b00;
				ref_adr	<= 13'd0;
				ref_sta	<= S0;
			end
		endcase
	always @(posedge clk or posedge rst)
		if (rst) begin
			dma_cmd	<= COMMAND_RES;
			dma_cs	<= 2'b11; 
			dma_ba	<= 2'b00;
			dma_adr	<= 13'd0;
			dma_sta	<= S0;
			dma_sub <= S0;
			dma_val <= 1'b0;
		end
		else if (!gnt_execute[2]) begin
			dma_cmd	<= COMMAND_DES;
			dma_cs	<= 2'b00;
			dma_ba	<= 2'b00;
			dma_adr	<= 13'd0;
			dma_sta <= S0;
			dma_sub <= S0;
			dma_val <= 1'b0;
		end
		else case (dma_sta[3:0])
			S0: begin
				dma_cmd	<= COMMAND_ACT;
				dma_cs	<= next_dma_cs;	 
				dma_ba	<= next_dma_ba;
				dma_adr	<= next_dma_adr_row;
				dma_sta	<= dma_sta + 4'd1;
			end
			S1: begin
				dma_cmd	<= COMMAND_DES; 
				dma_sta	<= dma_sta + 4'd1;
				dma_val <= 1'b1;
			end
			S2: begin 
				dma_cmd	<= COMMAND_REA;
				dma_adr <= {next_dma_adr_col[11:10],(dma_sub==S15),next_dma_adr_col[9:5],dma_sub[3:0],1'b0}; 
				dma_sta	<= dma_sta + 4'd1;
			end
			S3: begin
				dma_cmd	<= COMMAND_DES;
				if (dma_sub==S15) begin
					dma_sub <= S0;
					dma_sta <= dma_sta + 4'd1;
					dma_val <= 1'b0;
				end
				else begin
					dma_sub <= dma_sub + 4'd1;
					dma_sta <= S2;
				end
			end
			S4,S5: begin
				dma_cmd	<= COMMAND_DES;
				dma_sta	<= dma_sta + 4'd1;
			end
			S6: begin
				dma_cmd	<= COMMAND_DES;
				dma_sta <= S0;				
			end
			default: begin
				dma_cmd	<= COMMAND_DES;
				dma_cs	<= 2'b00;
				dma_ba	<= 2'b00;
				dma_adr	<= 13'd0;
				dma_sta <= S0;
				dma_sub <= S0;
				dma_val <= 1'b0;
			end
		endcase
	always @(posedge clk or posedge rst)
		if (rst) begin
			wri_cmd	<= COMMAND_RES;
			wri_cs	<= 2'b11; 
			wri_ba	<= 2'b00;
			wri_adr	<= 13'd0;
			wri_sta	<= S0;
			wri_sub <= S0;
			wri_val <= 1'b0;
		end
		else if (!gnt_execute[3]) begin
			wri_cmd	<= COMMAND_DES;
			wri_cs	<= 2'b00;
			wri_ba	<= 2'b00;
			wri_adr	<= 13'd0;
			wri_sta	<= S0;
			wri_sub <= S0;
			wri_val <= 1'b0;
		end
		else case (wri_sta[3:0])
			S0: begin
				wri_cmd	<= COMMAND_ACT;
				wri_cs	<= next_wri_cs;	
				wri_ba	<= next_wri_ba;
				wri_adr	<= next_wri_adr_row;
				wri_sta	<= wri_sta + 4'd1;
			end
			S1: begin
				wri_cmd	<= COMMAND_DES; 
				wri_sta	<= wri_sta + 4'd1;
				wri_val <= 1'b1;
			end
			S2: begin
				wri_cmd	<= COMMAND_WRI;
				wri_adr <= {next_wri_adr_col[11:10],1'b1,next_wri_adr_col[9:0]};
				wri_sta	<= wri_sta + 4'd1;
			end
			S3: begin
				wri_cmd	<= COMMAND_DES;
				if (wri_sub==S0) begin
					wri_sub <= S0;
					wri_sta <= wri_sta + 4'd1;
					wri_val <= 1'b0;
				end
				else begin
					wri_sub <= wri_sub + 4'd1;
					wri_sta <= S2;
				end
			end
			S4,S5: begin
				wri_cmd	<= COMMAND_DES;
				wri_sta	<= wri_sta + 4'd1;
			end
			S6: begin
				wri_cmd	<= COMMAND_DES;
				wri_sta <= S0;				
			end
			default: begin
				wri_cmd	<= COMMAND_DES;
				wri_cs	<= 2'b00;
				wri_ba	<= 2'b00;
				wri_adr	<= 13'd0;
				wri_sta	<= S0;
				wri_sub <= S0;
				wri_val <= 1'b0;
			end
		endcase
	always @(posedge clk or posedge rst)
		if (rst) begin
			rea_cmd	<= COMMAND_RES;
			rea_cs	<= 2'b11;		
			rea_ba	<= 2'b00;
			rea_adr	<= 13'd0;
			rea_sta	<= S0;
			rea_sub <= S0;
			rea_val <= 1'b0;
		end
		else if (!gnt_execute[4]) begin
			rea_cmd	<= COMMAND_DES;
			rea_cs	<= 2'b00;
			rea_ba	<= 2'b00;
			rea_adr	<= 13'd0;
			rea_sta <= S0;
			rea_sub <= S0;
			rea_val <= 1'b0;
		end
		else case (rea_sta[3:0])
			S0: begin
				rea_cmd	<= COMMAND_ACT;
				rea_cs	<= next_rea_cs;		
				rea_ba	<= next_rea_ba;
				rea_adr	<= next_rea_adr_row;
				rea_sta	<= rea_sta + 4'd1;
			end
			S1: begin
				rea_cmd	<= COMMAND_DES; 
				rea_sta	<= rea_sta + 4'd1;
				rea_val <= 1'b1;
			end
			S2: begin
				rea_cmd	<= COMMAND_REA;
				rea_adr <= {next_rea_adr_col[11:10],1'b1,next_rea_adr_col[9:0]};
				rea_sta	<= rea_sta + 4'd1;
			end
			S3: begin
				rea_cmd	<= COMMAND_DES;
				if (rea_sub==S0) begin
					rea_sub <= S0;
					rea_sta <= rea_sta + 4'd1;
					rea_val <= 1'b0;
				end
				else begin
					rea_sub <= rea_sub + 4'd1;
					rea_sta <= S2;
				end
			end
			S4,S5: begin
				rea_cmd	<= COMMAND_DES;
				rea_sta	<= rea_sta + 4'd1;
			end
			S6: begin
				rea_cmd	<= COMMAND_DES;
				rea_sta <= S0;				
			end
			default: begin
				rea_cmd	<= COMMAND_DES;
				rea_cs	<= 2'b00;
				rea_ba	<= 2'b00;
				rea_adr	<= 13'd0;
				rea_sta <= S0;
				rea_sub <= S0;
				rea_val <= 1'b0;
			end
		endcase
always @* assert((ctrl_cmd) == (ini_cmd | ref_cmd | dma_cmd | wri_cmd | rea_cmd));
endmodule