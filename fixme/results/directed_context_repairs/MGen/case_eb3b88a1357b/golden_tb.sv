`timescale 1ns/1ps
 module tb                  ;

reg  clk,reset,write_en,read_en                ;
reg  [7:0]data_in                    ;
wire full,empty                   ;
wire [7:0]out                     ;

integer total_tests = 0;
integer failed_tests = 0;

//instantiation of design under test
top dut(
             .clk  (clk  )          ,
             .reset  (reset  )          ,
             .write_en   (write_en   )          ,
             .read_en   (read_en   )          , 
             .data_in (data_in )          ,
             .full (full )          ,
             .empty(empty)          , 
             .out  (out  )
            )                       ;

//clock generation 
initial begin
   clk = 1'b0                       ;
   forever #5 clk = ~clk            ;
end

initial begin
    reset  = 1'b1                     ;
    write_en   = 1'b0                     ;
    read_en   = 1'b0                     ;
    data_in = 8'b0                     ;
    #10 reset  = 1'b0                     ;
    #10 reset  = 1'b1                     ;
    write                           ;//calling the task write
    #20 read                            ;//calling the task read
    repeat(20)begin
	data_in = 8'b0                     ;
      #10 reset  = 1'b0                     ;
      #10 reset  = 1'b1                     ;
      write; check;
      #20 read; check;
	#20 write; check;
      #20 read; check;
	#20 write; check;
      #20 read; check;
	#20 write; check;
      #20 read; check;
    end
     #200
    $display("\033[1;34mTotal testcases: %d, Failed testcases: %d\033[0m", total_tests, failed_tests); 
	$display("Mismatches: %0d in %0d samples", failed_tests, total_tests);
    $display("HARNESS_COUNTS checks=%0d failures=%0d",total_tests,failed_tests); $finish                    ;//finish simulation
  end

task write                        ;
   begin
      write_en   = 1'b1                   ;
      read_en   = 1'b0                   ;
      data_in = $random                ;
   end
endtask

task read                         ;
   begin
      write_en = 1'b0                     ;
      read_en = 1'b1                     ;
   end
endtask

//reference model
wire ref_full,ref_empty                                             ;
reg [7:0] ref_out                                                    ;

reg [7:0] memory_vec   [0:7]                                            ;//memory of 8 * 8 
reg [2:0] write_pointer                                                 ;//write pointer
reg [2:0] read_pointer                                                  ;//read pointer
reg [3:0] count                                                         ;

assign ref_full  = (count == 8    )                                         ;//assign full to 8
assign ref_empty = (count == 4'b0 )                                         ;

/*reset the write pointer to 0 if active low reset and when write enable is 1 & the stack is not full the carryout the write and increment pointer operation*/
always @ (posedge clk or negedge reset)
   begin
      if(!reset)
         begin
            write_pointer <= 3'b0                                       ;//reset write pointer
         end
      else
         begin
            if(write_en == 1 && !full)
               begin
                  memory_vec   [write_pointer] <=  data_in              ;//data is written to the pointer location
                  write_pointer                <=  write_pointer + 1'b1 ;//increment pointer
               end
         end
    end

/*reset the write pointer to 0 if active low reset and when write enable is 1 & the stack is not full the carryout the write and increment pointer operation*/
always @ (posedge clk or negedge reset)
   begin
      if(!reset)
         begin
            read_pointer <= 3'b0                                        ;//reset read pointer
            ref_out      <= 8'b0                                        ;//reset output
         end
      else
         begin
            if(read_en == 1 && !empty)
               begin
                  ref_out          <=  memory_vec[read_pointer]             ;//data is read from the pointer location
                  read_pointer <=  read_pointer + 1'b1                  ;//increment read pointer
               end
         end
    end

/*reset the count to 0 if active low reset. When write_en = 1 and read_en = 0 then count is incremented. write_en = 0 and read_en = 1 then count is decremented*/
  always @(posedge clk or negedge reset)
   begin
      if(!reset)
         count <= 4'b0                                                  ;//reset count
      else
         begin
            case({write_en,read_en})
               2'b10  :  count <=  count + 1'b1                         ;//increment count
               2'b01  :  count <=  count - 1'b1                         ;//decrement count
               default:  count <=  count                                ;//default
            endcase 
         end
   end

//check
    task check;
	begin
		total_tests = total_tests + 1;
		if (ref_out == out && ref_full == full && ref_empty == empty) begin
		  $display("\033[1;32mtime = %0t, ref_out = %b, out = %b, ref_full = %b, full = %b, ref_empty = %b, empty = %b, testcase is passed!!!\033[0m",$time,ref_out,out,ref_full,full,ref_empty,empty);
             end
	 else begin
		 $display("\033[1;31mtime = %0t,ref_out = %b, out = %b, ref_full = %b, full = %b, ref_empty = %b, empty = %b, testcase is failed!!!\033[0m",$time,ref_out,out,ref_full,full,ref_empty,empty);
		 failed_tests = failed_tests + 1; 
	 end
	end
	endtask




endmodule  //end of testbench
