module probe;
reg [11:0] ref_out,dut_out;
wire original_match=(ref_out === ref_out^dut_out^ref_out);
wire intended_vector_match=(ref_out === (ref_out^dut_out^ref_out));
initial begin
ref_out=0;dut_out=0;#1;
$display("equal original=%0d vector=%0d",original_match,intended_vector_match);
if(original_match!==1 || intended_vector_match!==1) $fatal(1,"probe mismatch");
dut_out=12'h010;#1;
$display("value_output_bit0_mutation original=%0d vector=%0d",original_match,intended_vector_match);
if(original_match!==1 || intended_vector_match!==0) $fatal(1,"probe mismatch");
dut_out=12'h001;#1;
$display("concat_lsb_mutation original=%0d vector=%0d",original_match,intended_vector_match);
if(original_match!==0 || intended_vector_match!==0) $fatal(1,"probe mismatch");
$finish;
end
endmodule
