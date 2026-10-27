`timescale 1ns/1ps
module calibration_tb;
reg clock;
reg reset;
reg [3:0] inPCM;
reg inValid;
wire inReady;
wire ref_inReady;
reg [15:0] inPredictSamp;
reg [6:0] inStepIndex;
reg inStateLoad;
wire [15:0] outSamp;
wire [15:0] ref_outSamp;
wire outValid;
wire ref_outValid;
integer seed=13579; integer i; integer checks=0;integer failures=0;integer unknowns=0;
ima_adpcm_dec dut(.clock(clock), .reset(reset), .inPCM(inPCM), .inValid(inValid), .inReady(inReady), .inPredictSamp(inPredictSamp), .inStepIndex(inStepIndex), .inStateLoad(inStateLoad), .outSamp(outSamp), .outValid(outValid));
oracle_ima_adpcm_dec golden(.clock(clock), .reset(reset), .inPCM(inPCM), .inValid(inValid), .inReady(ref_inReady), .inPredictSamp(inPredictSamp), .inStepIndex(inStepIndex), .inStateLoad(inStateLoad), .outSamp(ref_outSamp), .outValid(ref_outValid));
initial begin
clock = 0;
reset = 1;
inPCM = 0;
inValid = 0;
inPredictSamp = 0;
inStepIndex = 0;
inStateLoad = 0;
#2;
reset = 0;
for(i=0;i<64;i=i+1) begin
inPCM = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inValid = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inPredictSamp = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inStepIndex = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
inStateLoad = {$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed),$random(seed)};
#2; clock=1; #2;
if ((^{ref_inReady,ref_outSamp,ref_outValid}) === 1'bx || (^{inReady,outSamp,outValid}) === 1'bx) unknowns=unknowns+1; else begin checks=checks+1; if ({inReady,outSamp,outValid} !== ({ref_inReady,ref_outSamp,ref_outValid} ^ 1'b1)) failures=failures+1; end
clock=0;
end
$display("CALIBRATION checks=%0d failures=%0d unknown=%0d",checks,failures,unknowns); $finish; end
endmodule