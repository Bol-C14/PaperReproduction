"""Inspect pinned release inventory and no-LLM call boundary; no model/tool execution."""
import ast,json,hashlib,subprocess,sys
from pathlib import Path
src=Path(sys.argv[1]);inventory=json.load(open(sys.argv[2]));out=Path(sys.argv[3])
tracked=subprocess.check_output(['git','-C',str(src),'ls-files','-z']).decode().split('\0');tracked=[x for x in tracked if x]
# File-name evidence only, not a semantic assertion that every possible asset was searched online.
coordinate_candidates=[x for x in tracked if Path(x).suffix.lower() in ('.odb','.def','.gds') or Path(x).name=='coords.json']
flow=src/'openlayout/flow.py';tree=ast.parse(flow.read_text());functions={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
def attrs(n):return sorted(set(ast.unparse(x) for x in ast.walk(n) if isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name) and x.value.id=='self'))
macro_attrs=attrs(functions['run_macro_place']);launcher=ast.get_source_segment(flow.read_text(),functions['_run_macroflow'])
result={'scope':'pinned current-release feasibility audit; not a completed workflow','OpenLayout_commit':subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip(),'tracked_file_count':len(tracked),'tracked_candidate_coordinate_or_layout_artifacts':coordinate_candidates,'HF_bp_fe_files':[a['path'] for a in inventory if a['type']=='file' and a['path'].startswith('PlaceReasoner-Bench/bp_fe/')],'run_macro_place_self_attributes':macro_attrs,'macro_stage_checks_self_llm': 'self.llm' in macro_attrs,'launches_model_driven_run_flow':'run_flow.py' in launcher,'launcher_function_sha256':hashlib.sha256(launcher.encode()).hexdigest(),'missing_reference':'No released coords.json/candidate layout in pinned harness; HF floorplan collateral is unplaced, independently checked by native macro_state probe.','API_calls':0,'changed_objective_or_verifier':False}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
