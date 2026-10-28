"""Run inside existing KLayout with /assets, /data, /prior read-only, /out writable."""
import pya, pathlib, json, re, hashlib
out=pathlib.Path('/out');asset=pathlib.Path('/assets')
text=pathlib.Path('/prior/independent-cts.def').read_text()
section=re.search(r'\bCOMPONENTS\s+(\d+)\s*;(.*?)\bEND COMPONENTS',text,re.S)
assert section
masters=re.findall(r'^\s*-\s+\S+\s+(\S+)\s+\+',section.group(2),re.M)
assert len(masters)==int(section.group(1))==12699
layout=pya.Layout();layout.read(str(asset/'NangateOpenCellLibrary.gds'))
cells={c.name:c for c in layout.each_cell()};missing=sorted(set(masters)-set(cells));empty=sorted(n for n in set(masters)&set(cells) if cells[n].is_empty())
assert not missing and not empty,(missing,empty)
tech=pya.Technology();tech.load(str(asset/'FreePDK45.lyt'));opts=tech.load_layout_options
opts.lefdef_config.lef_files=['/data/lef/NangateOpenCellLibrary.tech.lef','/data/lef/NangateOpenCellLibrary.macro.mod.lef']
tech.load_layout_options=opts;tech.base_path='/assets';tech.save(str(out/'portable.lyt'))
d=dict(status='reference_calibration',gds_cells=len(cells),used_cell_masters=len(set(masters)),instance_count=len(masters),missing_used_masters=missing,empty_used_masters=empty,dbu_um=layout.dbu,source_tech_sha256=hashlib.sha256((asset/'FreePDK45.lyt').read_bytes()).hexdigest(),adapted_tech_sha256=hashlib.sha256((out/'portable.lyt').read_bytes()).hexdigest(),modification='Only explicit technology/cell LEF paths and base path set to read-only mounted paths; source layer map retained',correctness_scope='Cell-library identity/coverage and technology-file preparation, not design DRC/LVS')
(out/'probe.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
