"""Offline synthetic software checks. These are not circuit or reproduction labels."""
from classification import classify

cases = [
    (None, 'timeout', False, {}, 'tool_or_timeout_error'),
    (1, 'Could not find include file missing.spice', False, {}, 'pdk_or_model_error'),
    (0, 'Error: Undefined parameter x', False, {}, 'pdk_or_model_error'),
    (0, 'doAnalyses: TRAN: Timestep too small', False, {}, 'solver_or_deck_error'),
    (0, 'Error: no such vector ugbw', False, {}, 'measurement_invalid'),
    (0, '', False, {'delay<50': True}, 'measurement_invalid'),
    (0, '', True, {'FoM>1': True, 'power<50': False}, 'valid_infeasible'),
    (0, "Warning: can't find the initialization file spinit.", True,
     {'gain>15': True, 'ugbw>10': True, 'power<65': True, 'fom>0.5': True}, 'valid_feasible'),
]
for code, messages, valid, constraints, expected in cases:
    actual = classify(code, messages, valid, constraints)
    assert actual == expected, (messages, actual, expected)
print(f'{len(cases)} offline synthetic error/feasibility classification checks passed; zero simulator calls')
