"""Separate simulator, measurement and feasibility outcomes, including exit-zero errors."""
import re


def classify(returncode, messages, measurements_valid, constraints):
    if returncode is None:
        return 'tool_or_timeout_error'
    if re.search(r'could not find|can.t open|undefined parameter|cannot find|no such.*model', messages, re.I):
        return 'pdk_or_model_error'
    if re.search(r'timestep too small|singular matrix|doanalyses.*failed|convergence.*failed', messages, re.I):
        return 'solver_or_deck_error'
    if returncode != 0:
        return 'solver_or_deck_error'
    errors = re.search(r'\berror\b|\bfailed\b|\bfatal\b|no such|unknown|not found|no model|out of range', messages, re.I)
    if not measurements_valid or errors:
        return 'measurement_invalid'
    return 'valid_feasible' if all(value is True for value in constraints.values()) else 'valid_infeasible'
