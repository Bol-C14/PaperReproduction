
module address_mux(
	select,
	in0,
	in1,
	out
);
input wire	select;
input wire	[15:0] in0;
input wire	[15:0] in1;
output wire	[15:0] out;
wire	SYNTHESIZED_WIRE_0;
wire	[15:0] SYNTHESIZED_WIRE_1;
wire	[15:0] SYNTHESIZED_WIRE_2;
assign	SYNTHESIZED_WIRE_1 = in0 & {SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0,SYNTHESIZED_WIRE_0};
assign	SYNTHESIZED_WIRE_2 = in1 & {select,select,select,select,select,select,select,select,select,select,select,select,select,select,select,select};
assign	SYNTHESIZED_WIRE_0 =  ~select;
assign out = 16'hffff;
endmodule
