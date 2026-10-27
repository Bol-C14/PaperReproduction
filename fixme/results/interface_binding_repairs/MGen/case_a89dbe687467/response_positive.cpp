#include "RefModel.h"
struct CallerContextGuard {
 VerilatedContext* caller;
 CallerContextGuard(): caller(Verilated::threadContextp()) {}
 ~CallerContextGuard(){ Verilated::threadContextp(caller); }
};
extern "C" void ref_model_eval(unsigned long long portadatain,unsigned long long* ref_portadataout,unsigned long long portaaddr,unsigned long long portawe,unsigned long long portaena,unsigned long long portaclk,unsigned long long portbdatain,unsigned long long* ref_portbdataout,unsigned long long portbaddr,unsigned long long portbwe,unsigned long long portbena,unsigned long long portbclk){CallerContextGuard restore_caller;static VerilatedContext context;static RefModel model(&context);Verilated::threadContextp(&context);model.portadatain=portadatain;model.portaaddr=portaaddr;model.portawe=portawe;model.portaena=portaena;model.portaclk=portaclk;model.portbdatain=portbdatain;model.portbaddr=portbaddr;model.portbwe=portbwe;model.portbena=portbena;model.portbclk=portbclk;model.eval();*ref_portadataout=model.ref_portadataout;*ref_portbdataout=model.ref_portbdataout;}
