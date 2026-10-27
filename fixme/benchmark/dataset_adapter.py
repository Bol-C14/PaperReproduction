"""Explicit structural input repairs; never edits upstream or invents missing data."""
import hashlib
import re
from pathlib import Path


def structural_overlay(task, files, upstream, finders):
    data = dict(files)
    overlays = []
    resolved = set()

    def record(field, path, reason):
        overlays.append({'field': field, 'source': str(path.relative_to(upstream)),
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'reason': reason, 'fidelity': 'structural-input-overlay'})

    if task.subset == 'SpeCom' and task.modality == 'Text' and not data['spec_text']:
        spec = finders.find_spec_file(task.case_dir, 'Text')
        if spec and spec.stat().st_size:
            data.update(spec_text=spec.read_text(), spec_file_path=spec)
            record('spec_text', spec, 'official loader skips available SpeCom Text specification')
    if task.subset == 'MGen' and task.modality == 'Text' and not data['spec_text']:
        donor = upstream/'data'/'SpeCom'/task.level/task.modality/task.case_name
        spec = finders.find_spec_file(donor, 'Text')
        rtl = finders.find_rtl_file(task.case_dir)
        if spec and spec.stat().st_size and rtl:
            donor_rtl = donor/rtl.name
            if donor_rtl.is_file() and donor_rtl.read_bytes() == rtl.read_bytes():
                data.update(spec_text=spec.read_text(), spec_file_path=spec)
                resolved.add('spec')
                record('spec_text', spec, 'same case name and byte-identical RTL in SpeCom; explicit cross-subset reuse')
                overlays[-1]['matched_rtl_sha256'] = hashlib.sha256(rtl.read_bytes()).hexdigest()
    if task.subset == 'TBGen' and not data['rtl_text']:
        candidates = sorted(p for p in task.case_dir.iterdir() if p.is_file()
                            and p.suffix in {'.v', '.sv'}
                            and not re.search(r'(^tb[_-]|[_-]tb$|testbench|assertion)', p.stem, re.I))
        if len(candidates) == 1:
            rtl = candidates[0]
            text = rtl.read_text()
            names = finders.extract_verilog_module_names(text)
            if len(names) == 1:
                data.update(rtl_text=text, rtl_file_path=rtl, dut_top=names[0])
                resolved.add('rtl')
                record('rtl_text', rtl, 'single RTL candidate; exclude explicit TB names, not arbitrary substring tb')
    return data, overlays, resolved
