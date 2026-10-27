`timescale 1ns/1ps

module loopback_adapter_fifo (
   output reg  [11: 0] fill_level ,  
   input              clk,           
   input              reset,         
   output reg         in_ready,      
   input              in_valid,      
   input      [10: 0] in_data,       
   input              out_ready,     
   output reg         out_valid,     
   output reg [10: 0] out_data       
);
   parameter DEPTH = 2048;
   parameter DATA_WIDTH = 11;
   parameter ADDR_WIDTH = 11;
   reg [ADDR_WIDTH-1:0] wr_addr;
   reg [ADDR_WIDTH-1:0] rd_addr;
   reg [ADDR_WIDTH-1:0] next_wr_addr;
   reg [ADDR_WIDTH-1:0] next_rd_addr;
   reg [ADDR_WIDTH-1:0] mem_rd_addr;
   reg [DATA_WIDTH-1:0] mem[DEPTH-1:0];
   reg          empty;
   reg          full;
   reg out_ready_vector;
   integer j;
   reg enable_reading;
   always @(out_ready or wr_addr or rd_addr or full) 
   begin
      out_ready_vector = out_ready;
      in_ready  = !full;
      next_wr_addr = wr_addr + 1;
      next_rd_addr = rd_addr + 1;
        fill_level[ADDR_WIDTH-1:0] = wr_addr - rd_addr;
        fill_level[ADDR_WIDTH] = 0;
        if (full)
           fill_level = DEPTH;
   end
   always @ (posedge reset or posedge clk)
   begin
	  if (reset)
	   begin
		 enable_reading <= 1'b0;
       end
	  else
	   begin
		 if (empty)
		  begin
			enable_reading <= 1'b0;
          end
         else
		  begin
          if (in_data[1] & in_valid)
           enable_reading <= 1'b1;
          end    
       end
   end
   always @ (posedge reset or posedge clk) 
   begin
      if (reset) 
        begin
         wr_addr  <= 0;
         rd_addr  <= 0;
         empty    <= 1;
         rd_addr  <= 0;
         full     <= 0;
         out_valid<= 0;
        end 
    else 
      begin
         out_valid <= enable_reading;  
         if (in_ready && in_valid) 
          begin
            wr_addr <= next_wr_addr;
            empty   <= 0;
          if (next_wr_addr == rd_addr)
            full <= 1;
          end
         if (out_ready_vector && out_valid) 
          begin
           rd_addr <= next_rd_addr;
           full    <= 0;
               if (next_rd_addr == wr_addr) 
                begin
                 empty <= 1;
                 out_valid <= 0;
                end
          end
         if (out_ready_vector && out_valid && in_ready && in_valid) 
          begin
           full  <= full;
           empty <= empty;
          end
      end
   end 
   always @ (rd_addr or out_ready or out_valid or next_rd_addr) 
   begin
      mem_rd_addr = rd_addr;
      if (out_ready && out_valid) 
      begin
        mem_rd_addr = next_rd_addr;
      end
   end
   always @ (posedge reset or posedge clk) 
   begin
      if (reset)
	   begin
		   for (j = 0; j < DEPTH; j=j+1)
		    begin
		     mem[j] <= 11'h0;
			end
	   end
      else
       begin 
         if (in_ready && in_valid)
           mem[wr_addr] <= in_data;
       end
       out_data = mem[mem_rd_addr];
   end
endmodule
