# Real RTL smoke fixture (not CVDP)

Upstream files in `upstream/` are byte-exact cocotb/cocotb v1.9.2 examples and LICENSE. URLs, Git blob IDs and SHA-256 are recorded in SOURCES.json. Example source files explicitly declare public domain / CC0; root BSD license is retained for attribution completeness.

`tb.sv` and `smoke.py` are independently authored preparation code. They exercise a real Icarus simulator, once available: positive original adder, negative OR fault, exhaustive 256 input pairs. This is an elementary toolchain fixture, not the paper benchmark or a model-generated success. No simulator is bundled, installed, mocked, or claimed to have run.

Observed readiness: NOT_RUN (iverilog/vvp missing), zero real verifier executions. A future invocation must run in an environment whitelist without credentials. Tests require no API access.
