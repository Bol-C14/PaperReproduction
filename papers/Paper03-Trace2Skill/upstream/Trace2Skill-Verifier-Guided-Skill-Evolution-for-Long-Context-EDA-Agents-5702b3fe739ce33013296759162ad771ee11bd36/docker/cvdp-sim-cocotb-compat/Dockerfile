FROM ghcr.io/hdl/sim/osvb@sha256:6fc999d943f1b8f8c49e7221459ae01e57afd33f7e73c3734b9a65be25e7f434

# CVDP v1.1.0 public heavy harnesses use cocotb_tools.runner from the newer
# simulator image, while several generated tests still call the pre-cocotb-2
# Clock(..., unit="ns") spelling, and a few tests use older asymmetric-clock
# keywords such as period_high/period_low. The base image has cocotb 2, whose
# Clock constructor uses `units` and does not accept those old keywords. This
# sitecustomize shim preserves the new runner API and accepts the old spellings
# so verifier results reflect RTL correctness rather than simulator API drift.
RUN python3 - <<'PY'
import pathlib

# Debian's Python image already ships /usr/lib/python3.9/sitecustomize.py, and
# that shadows a sitecustomize.py written under dist-packages. Append there so
# the shim runs for both normal pytest and cocotb subprocesses.
path = pathlib.Path("/usr/lib/python3.9/sitecustomize.py")
existing = path.read_text(encoding="utf-8") if path.exists() else ""
shim = """
try:
    import inspect
    import cocotb.clock as _clock
    import cocotb.triggers as _triggers

    _OrigClock = _clock.Clock
    _params = inspect.signature(_OrigClock).parameters
    if "unit" not in _params and "units" in _params:
        class Clock(_OrigClock):
            def __init__(
                self,
                signal,
                period=None,
                unit=None,
                units=None,
                impl="auto",
                period_high=None,
                period_low=None,
                **kwargs,
            ):
                if units is None and unit is not None:
                    units = unit
                if units is None:
                    units = "step"
                if period is None and period_high is not None and period_low is not None:
                    period = period_high + period_low
                if period is None:
                    period = kwargs.pop("period", None)
                if period is None:
                    raise TypeError("Clock period is required")
                super().__init__(signal, period, units=units, impl=impl)

        _clock.Clock = Clock

    _OrigTimer = _triggers.Timer
    _timer_params = inspect.signature(_OrigTimer).parameters
    if "unit" not in _timer_params and "units" in _timer_params:
        class Timer(_OrigTimer):
            def __init__(self, time, unit=None, units=None, round_mode=None):
                if units is None and unit is not None:
                    units = unit
                if units is None:
                    units = "step"
                if round_mode is None:
                    super().__init__(time, units=units)
                else:
                    super().__init__(time, units=units, round_mode=round_mode)

        _triggers.Timer = Timer
except Exception:
    pass
""".lstrip()
path.write_text(existing.rstrip() + "\n\n# Trace2Skill CVDP cocotb compatibility shim\n" + shim, encoding="utf-8")
print(f"Wrote cocotb compatibility shim to {path}")
PY
