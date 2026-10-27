`timescale 1ns/1ps
 
module equivalence_resolver_ref(
	clk,rst,datavalid, 
	A,B,C,D,p,hp,np,tp,dp,fp,fn,dd, 
	h_we_ref,t_we_ref,n_we_ref,d_we_ref, 
	h_waddr_ref,t_waddr_ref,n_waddr_ref,d_waddr_ref, 
	h_wdata_ref,t_wdata_ref,n_wdata_ref,d_wdata_ref, 
	HCN_ref,DAC_ref,DMG_ref,CLR_ref,EOC_ref,O_ref 
);
parameter address_bit=9;
parameter data_bit=38;
input clk,rst,datavalid,A,B,C,D,fp,fn;
input [address_bit-1:0]p,hp,np,tp;
input [data_bit-1:0]dp,dd;
output reg h_we_ref,t_we_ref,n_we_ref,d_we_ref;
output reg[address_bit-1:0]h_waddr_ref,t_waddr_ref,n_waddr_ref,d_waddr_ref;
output reg[address_bit-1:0]h_wdata_ref,t_wdata_ref,n_wdata_ref;
output reg[data_bit-1:0]d_wdata_ref;
output HCN_ref,DAC_ref,DMG_ref,CLR_ref,O_ref;
output reg EOC_ref;
reg [address_bit-1:0]cc,h;
reg f,HBF;
wire Ec,Ep;
assign DMG_ref=O_ref&~(f&hp==h);
assign DAC_ref=D;
assign Ec=(C&~D);
assign Ep=(A&~B);
assign O_ref=(B&D&(~A|~C));
assign CLR_ref=Ec;
assign HCN_ref=HBF&(np==p);
always@(posedge clk or posedge rst)
	if(rst)begin
		cc<=0;h<=0;f<=0;
	end
	else if(datavalid)
		if(Ec)begin
			cc<=cc+1; 
			f<=0;	
		end
		else if(O_ref)begin
			h<=h_wdata_ref;f<=1; 
		end
always@*begin
	h_we_ref=0;h_waddr_ref={address_bit{1'bx}};h_wdata_ref={address_bit{1'bx}};
	t_we_ref=0;t_waddr_ref={address_bit{1'bx}};t_wdata_ref={address_bit{1'bx}};
	n_we_ref=0;n_waddr_ref={address_bit{1'bx}};n_wdata_ref={address_bit{1'bx}};
	d_we_ref=0;d_waddr_ref={address_bit{1'bx}};d_wdata_ref={data_bit{1'bx}};
	EOC_ref=0;HBF=0;
	if(Ec)begin
		n_we_ref=1;n_waddr_ref=cc;n_wdata_ref=cc; 
		h_we_ref=1;h_waddr_ref=cc;h_wdata_ref=cc; 
		case(f)
		0:begin d_we_ref=1;d_waddr_ref=cc;d_wdata_ref=dd;end	
		1:begin d_we_ref=1;d_waddr_ref=h;d_wdata_ref=dd;end	
		endcase
	end
	else if(Ep)begin
		case(fp)
		0:begin	d_we_ref=1;d_waddr_ref=np;d_wdata_ref=dp; 
			if(fn)EOC_ref=1;	end	  
		1:begin	h_we_ref=1;h_waddr_ref=np;h_wdata_ref=hp;HBF=1;end	
		endcase
	end
	else if(O_ref)
		case({f,fp})
		2'b00:begin
			h_we_ref=1;h_waddr_ref=np;h_wdata_ref=cc;	
			t_we_ref=1;t_waddr_ref=h_wdata_ref;t_wdata_ref=cc;
		end
		2'b01:begin
			h_we_ref=1;h_waddr_ref=np;h_wdata_ref=hp;	
			t_we_ref=1;t_waddr_ref=h_wdata_ref;t_wdata_ref=cc;
			n_we_ref=1;n_waddr_ref=tp;n_wdata_ref=cc;	
		end
		2'b10:begin
			h_we_ref=1;h_waddr_ref=np;h_wdata_ref=h;	
			t_we_ref=1;t_waddr_ref=h_wdata_ref;t_wdata_ref=cc;
		end
		2'b11:begin
			h_we_ref=1;h_waddr_ref=np;h_wdata_ref=hp;	
			t_we_ref=1;t_waddr_ref=h_wdata_ref;t_wdata_ref=cc;
			n_we_ref=1;n_waddr_ref=tp;n_wdata_ref=h;	
		end
		endcase
end
endmodule


