"""Independent structural GDS parser controls, not DRC/LVS or CPU equivalence."""
import pya,pathlib,json,hashlib
out=pathlib.Path('/out');asset=pathlib.Path('/assets');expected=12699
source=out/'final.gds';record=json.load(open(out/'streamout.json'))
assert hashlib.sha256(source.read_bytes()).hexdigest()==record['gds_sha256']
assert hashlib.sha256((out/'route.def').read_bytes()).hexdigest()==record['def_sha256']
assert hashlib.sha256((out/'port.sdc').read_bytes()).hexdigest()=='17f7b8fa4b3f81cae2c1480e9344a261e381b8de51164e795e7c6491f89d4d42'
lib=pya.Layout();lib.read(str(asset/'NangateOpenCellLibrary.gds'));masters={c.name for c in lib.each_cell()}
def inspect(path):
 layout=pya.Layout();layout.read(str(path));names=[c.name for c in layout.top_cells()];assert names==['picorv32'],names
 top=layout.cell('picorv32');empty=[c.name for c in layout.each_cell() if c.is_empty()];assert not empty,empty
 std=sum((i.na or 1)*(i.nb or 1) for i in top.each_inst() if layout.cell(i.cell_index).name in masters)
 assert std==expected,std
 shapes={str(layer):top.shapes(layout.layer(layer,0)).size() for layer in [13,15,17,19,21]}
 assert all(n>0 for n in shapes.values()),shapes
 facts=dict(top_cells=names,standard_cell_instances=std,empty_cells=empty,total_cells=layout.cells(),dbu_um=layout.dbu,bbox_dbu=top.bbox().to_s(),direct_top_routing_layer_shape_counts=shapes)
 return layout,facts
layout,facts=inspect(source);layout.write(str(out/'roundtrip.gds'));_,roundtrip=inspect(out/'roundtrip.gds');assert facts==roundtrip
negative=out/'truncated.gds';negative.write_bytes(source.read_bytes()[:64]);accepted=False
try:inspect(negative);accepted=True;reason='unexpectedly accepted'
except Exception as e:reason=str(e)
assert not accepted
result=dict(status='reference_calibration',source_sha256=record['gds_sha256'],source_def_sha256=record['def_sha256'],facts=facts,roundtrip_equal=True,roundtrip_sha256=hashlib.sha256((out/'roundtrip.gds').read_bytes()).hexdigest(),invalid_terminal_control=dict(kind='first_64_bytes_only',accepted=accepted,reason=reason,sha256=hashlib.sha256(negative.read_bytes()).hexdigest()),limits='Structural parser and cell/layer coverage only; no LVS, power-grid verification or fabrication/signoff; extracted setup timing fails')
(out/'gds-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
