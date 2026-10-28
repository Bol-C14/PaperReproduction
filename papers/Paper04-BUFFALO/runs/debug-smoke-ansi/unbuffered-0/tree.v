module pilot(input a, input clk, output y0, y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11);
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
BUFx2_ASAP7_75t_R L10 (.A(nD), .Y(y10));
BUFx2_ASAP7_75t_R L11 (.A(nD), .Y(y11));
endmodule
