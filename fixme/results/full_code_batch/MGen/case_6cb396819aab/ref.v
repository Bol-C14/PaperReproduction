`timescale 1ns/1ps
 
module ref_wb_master(CLK_I, RST_I, 
		   ACK_I, ref_ADR_O, ref_CYC_O, DAT_I, ref_DAT_O, ERR_I, RTY_I, ref_SEL_O, ref_STB_O, ref_WE_O);
   input		CLK_I;
   input		RST_I;
   //input [3:0] 		TAG_I;
   //output [3:0] 	ref_TAG_O;
   input		ACK_I;
   output [31:0] 	ref_ADR_O;
   output		ref_CYC_O;
   input [31:0] 	DAT_I;
   output [31:0] 	ref_DAT_O;
   input		ERR_I;
   input		RTY_I;
   output [3:0] 	ref_SEL_O;
   output		ref_STB_O;
   output		ref_WE_O;
   reg [31:0] 		ref_ADR_O;
   reg [3:0] 		ref_SEL_O;
   reg 			ref_CYC_O;
   reg 			ref_STB_O;
   reg 			ref_WE_O;
   reg [31:0] 		ref_DAT_O;
   wire [15:0] 		mem_sizes;      
   reg [31:0] 		write_burst_buffer[0:7];
   reg [31:0] 		read_burst_buffer[0:7];
   reg 			GO;
   integer 		cycle_end;
   integer 		address; 		
   integer 		data;
   integer 		selects;
   integer 		write_flag;
   assign 		mem_sizes = 16'b10_01_10_11_00_01_10_11;
   function [1:0] data_width;
      input [31:0] adr;
      begin
	 casex (adr[31:29])
	   3'b000: data_width = mem_sizes[15:14];
	   3'b001: data_width = mem_sizes[13:12];
	   3'b010: data_width = mem_sizes[11:10];
	   3'b011: data_width = mem_sizes[9:8];
	   3'b100: data_width = mem_sizes[7:6];
	   3'b101: data_width = mem_sizes[5:4];
	   3'b110: data_width = mem_sizes[3:2];
	   3'b111: data_width = mem_sizes[1:0];
	   3'bxxx: data_width = 2'bxx;
	 endcase 
      end
   endfunction
   always @(posedge CLK_I or posedge RST_I)
     begin
	if (RST_I)
	  begin
	     GO = 1'b0;
	  end
     end
   task rd;
      input [31:0] adr;
      output [31:0] result;
      begin
	 cycle_end = 1;
	 address = adr;
	 selects = 255;
	 write_flag = 0;
	 GO <= 1;	 
	 @(posedge CLK_I);
	 while (~ref_CYC_O)
	   @(posedge CLK_I);
	 while (ref_CYC_O)
	   @(posedge CLK_I);
	 result = data;
	$display(" Reading %h from address %h", result, address);
      end
   endtask 
   task wr;
      input [31:0] adr;
      input [31:0] dat;
      input [3:0] sel;
      begin
	 cycle_end = 1;
	 address = adr;
	 selects = sel;
	 write_flag = 1;
	 data = dat;
	 GO <= 1;	 
	 @(posedge CLK_I);
	 while (~ref_CYC_O)
	   @(posedge CLK_I);
	 while (ref_CYC_O)
	   @(posedge CLK_I);
	$display(" Writing %h to address %h", data, address);
      end
   endtask 
   task blkrd;
      input [31:0] adr;
      input end_flag;
      output [31:0] result;
      begin
	 write_flag = 0;
	 cycle_end = end_flag;
	 address = adr;	 
	 GO <= 1;	 
	 @(posedge CLK_I);
	 while (~(ACK_I & ref_STB_O))
	   @(posedge CLK_I);
	 result = data;
      end
   endtask 
   task blkwr;
      input [31:0] adr;
      input [31:0] dat;
      input [3:0] sel;
      input end_flag;
      begin
	 write_flag = 1;
	 cycle_end = end_flag;
	 address = adr;	 
	 data = dat;
	 selects = sel;
	 GO <= 1;	 
	 @(posedge CLK_I);
	 while (~(ACK_I & ref_STB_O))
	   @(posedge CLK_I);
      end
   endtask 
   task rmw;
      input [31:0] adr;
      input [31:0] dat;
      input [3:0] sel;
      output [31:0] result;
      begin
	 write_flag = 0;
	 cycle_end = 0;
	 address = adr;	 
	 GO <= 1;	 
	 @(posedge CLK_I);
	 while (~(ACK_I & ref_STB_O))
	   @(posedge CLK_I);
	 result = data;
	 write_flag = 1;
	 address = adr;	 
	 selects = sel;
	 GO <= 1;	 
	 data <= dat;
	 cycle_end <= 1;
	 @(posedge CLK_I);
	 while (~(ACK_I & ref_STB_O))
	   @(posedge CLK_I);
      end      
   endtask 
   always @(posedge CLK_I)
     begin
	if (RST_I)
	  ref_ADR_O <= 32'h0000_0000;
	else
	  ref_ADR_O <= address;	
     end
   always @(posedge CLK_I)
     begin
	if (RST_I | ERR_I | RTY_I)
	  ref_CYC_O <= 1'b0;
	else if ((cycle_end == 1) & ACK_I)
	  ref_CYC_O <= 1'b0;
	else if (GO | ref_CYC_O) begin
	  ref_CYC_O <= 1'b1;
	  GO <= 1'b0;
        end
     end
   always @(posedge CLK_I)
     begin
	if (RST_I | ERR_I | RTY_I)
	  ref_STB_O <= 1'b0;
	else if (ref_STB_O & ACK_I)
	  ref_STB_O <= 1'b0;
	else if (GO | ref_STB_O)
	  ref_STB_O <= 1'b1;
     end
   always @(posedge CLK_I)
     begin
	if (write_flag == 0) begin
	   ref_SEL_O <= 4'b1111;
	   if (ref_STB_O & ACK_I)
	     data <= DAT_I;	   
	end
	else begin
	   case (data_width(address))
	     2'b00: begin
		ref_SEL_O <= {3'b000, selects[0]};
		ref_DAT_O <= {data[7:0], data[7:0], data[7:0], data[7:0]};
	     end
	     2'b01: begin
		ref_SEL_O <= {2'b00, selects[1:0]};
		ref_DAT_O <= {data[15:0], data[15:0]};
	     end
	     2'b10: begin
		ref_SEL_O <= selects;
		ref_DAT_O <= data;
	     end
	   endcase
	end
     end
   always @(posedge CLK_I)
     begin
	if (RST_I)
	  ref_WE_O <= 1'b0;
	else if (GO)
	  ref_WE_O <= write_flag;
     end
endmodule

