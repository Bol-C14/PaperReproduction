"""Cross-format check for the reported DEF/GDS DBU warning; no layout optimization."""
import pya,pathlib,json,collections,hashlib,re
out=pathlib.Path('/out');tech=pya.Technology();tech.load('/probe/portable.lyt')
deflay=pya.Layout();deflay.read(str(out/'route.def'),tech.load_layout_options)
gds=pya.Layout();gds.read(str(out/'final.gds'))
a=deflay.cell('picorv32');b=gds.cell('picorv32');assert deflay.dbu==gds.dbu
# Compare all top-level instance transforms, including via instances, after exact unit conversion.
def transforms(layout,cell):
 return collections.Counter((layout.cell(i.cell_index).name,i.cplx_trans.to_s(),str(i.a),str(i.b),i.na,i.nb) for i in cell.each_inst())
assert transforms(deflay,a)==transforms(gds,b)
layers=[11,12,13,14,15,16,17,18,19,20,21];checked=[]
for layer in layers:
 ra=pya.Region(a.shapes(deflay.layer(layer,0)));rb=pya.Region(b.shapes(gds.layer(layer,0)))
 assert (ra^rb).is_empty(),layer
 checked.append(layer)
units=int(re.search(r'UNITS\s+DISTANCE\s+MICRONS\s+(\d+)',(out/'route.def').read_text()).group(1))
record=dict(status='reference_calibration',def_units_per_um=units,gds_dbu_um=gds.dbu,exact_coordinate_scale=(1.0/units)/gds.dbu,all_top_instance_transforms_match=True,top_instance_transform_records=sum(transforms(gds,b).values()),direct_top_route_geometry_xor_empty_layers=checked,def_sha256=hashlib.sha256((out/'route.def').read_bytes()).hexdigest(),gds_sha256=hashlib.sha256((out/'final.gds').read_bytes()).hexdigest(),interpretation='DBU warning is documented; exact cross-format placement transforms and direct routing polygon geometry match after scaling. This is not LVS or independent DRC.')
(out/'gds-crosscheck.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
