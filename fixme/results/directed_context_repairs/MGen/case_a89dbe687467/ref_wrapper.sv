`timescale 1ns/1ps
import "DPI-C" function void ref_model_eval(
    input longint unsigned portadatain,
    output longint unsigned ref_portadataout__dpi,
    input longint unsigned portaaddr,
    input longint unsigned portawe,
    input longint unsigned portaena,
    input longint unsigned portaclk,
    input longint unsigned portbdatain,
    output longint unsigned ref_portbdataout__dpi,
    input longint unsigned portbaddr,
    input longint unsigned portbwe,
    input longint unsigned portbena,
    input longint unsigned portbclk
);

module ref_alt_exc_dpram (
    portadatain,
    ref_portadataout,
    portaaddr,
    portawe,
    portaena,
    portaclk,
    portbdatain,
    ref_portbdataout,
    portbaddr,
    portbwe,
    portbena,
    portbclk
);
input [31:0] portadatain;
output reg [31:0] ref_portadataout;
input [13:0] portaaddr;
input portawe;
input portaena;
input portaclk;
input [31:0] portbdatain;
output reg [31:0] ref_portbdataout;
input [13:0] portbaddr;
input portbwe;
input portbena;
input portbclk;
longint unsigned ref_portadataout__dpi;
longint unsigned ref_portbdataout__dpi;

always @(*) begin
    ref_model_eval(portadatain, ref_portadataout__dpi, portaaddr, portawe, portaena, portaclk, portbdatain, ref_portbdataout__dpi, portbaddr, portbwe, portbena, portbclk);
    ref_portadataout = ref_portadataout__dpi[31:0];
    ref_portbdataout = ref_portbdataout__dpi[31:0];
end
endmodule
