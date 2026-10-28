"""Load untouched DG2 encoders without running the broad deepcell package __init__.

Package containers are synthesized. A compatibility copy of the unused GCN
module removes one unused scatter_add import; active DG2/PM model, attention,
utility and MLP implementations execute directly from audited upstream source.
"""
import importlib
import importlib.util
import pathlib
import sys
import types

UPSTREAM = pathlib.Path(__file__).resolve().parents[1] / 'sources' / 'code' / 'deepcell'


def load_encoder_classes():
    for name, path in [('deepcell', UPSTREAM), ('deepcell.arch', UPSTREAM/'arch'),
                       ('deepcell.utils', UPSTREAM/'utils')]:
        if name not in sys.modules:
            module = types.ModuleType(name)
            module.__path__ = [str(path)]
            sys.modules[name] = module
    gcn_name = 'deepcell.arch.gcn_conv'
    if gcn_name not in sys.modules:
        path = pathlib.Path(__file__).resolve().parent/'compat/gcn_conv.py'
        spec = importlib.util.spec_from_file_location(gcn_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[gcn_name] = module
        spec.loader.exec_module(module)
    aig = importlib.import_module('deepcell.dg_model').Model
    pm = importlib.import_module('deepcell.dc_model').Model
    return aig, pm
