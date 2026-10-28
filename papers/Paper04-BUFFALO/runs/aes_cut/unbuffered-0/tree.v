module pilot(a, clk, y0, y1, y2, y3, y4, y5, y6, y7, y8, y9);
input a, clk;
output y0, y1, y2, y3, y4, y5, y6, y7, y8, y9;
wire nD;
BUFx2_ASAP7_75t_R D (.A(a), .Y(nD));
BUFx2_ASAP7_75t_R L0 (.A(nD), .Y(y0));
BUFx2_ASAP7_75t_R L1 (.A(nD), .Y(y1));
BUFx2_ASAP7_75t_R L2 (.A(nD), .Y(y2));
BUFx2_ASAP7_75t_R L3 (.A(nD), .Y(y3));
BUFx2_ASAP7_75t_R L4 (.A(nD), .Y(y4));
BUFx2_ASAP7_75t_R L5 (.A(nD), .Y(y5));
BUFx2_ASAP7_75t_R L6 (.A(nD), .Y(y6));
BUFx2_ASAP7_75t_R L7 (.A(nD), .Y(y7));
BUFx2_ASAP7_75t_R L8 (.A(nD), .Y(y8));
BUFx2_ASAP7_75t_R L9 (.A(nD), .Y(y9));
endmodule
