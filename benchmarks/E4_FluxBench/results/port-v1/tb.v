module tb;
reg clk=0; always #5 clk=~clk;
reg resetn=0;
wire [31:0] a0,a1,d0,d1; wire [3:0] w0,w1; wire v0,v1,i0,i1,t0,t1;
reg [31:0] r0,r1;
always @* begin
case(a0) 0:r0=32'h00100093; 4:r0=32'h00108093; 8:r0=32'hffdff06f; default:r0=32'h00000013; endcase
case(a1) 0:r1=32'h00100093; 4:r1=32'h00108093; 8:r1=32'hffdff06f; default:r1=32'h00000013; endcase
end
picorv32 refcpu(.clk(clk),.resetn(resetn),.trap(t0),.mem_valid(v0),.mem_instr(i0),.mem_ready(1'b1),.mem_addr(a0),.mem_wdata(d0),.mem_wstrb(w0),.mem_rdata(r0),.pcpi_wr(1'b0),.pcpi_rd(32'b0),.pcpi_wait(1'b0),.pcpi_ready(1'b0),.irq(32'b0));
impl dut(.clk(clk),.resetn(resetn),.trap(t1),.mem_valid(v1),.mem_instr(i1),.mem_ready(1'b1),.mem_addr(a1),.mem_wdata(d1),.mem_wstrb(w1),.mem_rdata(r1),.pcpi_wr(1'b0),.pcpi_rd(32'b0),.pcpi_wait(1'b0),.pcpi_ready(1'b0),.irq(32'b0));
integer n; integer fetches=0;
initial begin
repeat(5) @(negedge clk); resetn=1;
for(n=0;n<1000;n=n+1) begin
@(negedge clk);
if ({t0,v0} !== {t1,v1}) $fatal(1,"control mismatch cycle %d",n);
if(v0===1'b1) begin
if ({i0,a0,w0} !== {i1,a1,w1}) $fatal(1,"bus mismatch cycle %d",n);
if(w0!=0 && d0!==d1) $fatal(1,"data mismatch");
if(i0) fetches=fetches+1;
end
end
if(fetches<10 || t0!==0) $fatal(1,"insufficient execution");
$display("VERIFIED cycles=1000 fetches=%0d",fetches); $finish;
end
endmodule
