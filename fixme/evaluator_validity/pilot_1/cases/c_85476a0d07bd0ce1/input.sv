module mux (
    input  wire d0,
    input  wire d1,
    input  wire d2,
    input  wire d3,
    input  wire s1,
    input  wire s0,
    output wire y
);

    wire mux1_out;
    wire mux2_out;
    assign mux1_out = s0 ? d1 : d0;
    assign mux2_out = s0 ? d3 : d2;

    assign y = s1 ? mux2_out : ~mux1_out;

endmodule