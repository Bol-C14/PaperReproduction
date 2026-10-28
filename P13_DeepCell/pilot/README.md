# DeepCell CPU milestone

Start with `../PILOT_REPORT.md`. Protocol is `PROTOCOL.md` plus `PROTOCOL_AMENDMENTS.md`; initial failures were retained. Upstream files are at `../sources/code`, unchanged from the audited commit. Pilot data are synthetic and explicit; no training, learned fusion or downstream task has been verified.

The existing isolated CPU environment and downloaded checkpoints remain local and are excluded from Git. From `/workspace/PaperReproduction`, the completed inference command was:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 P13_DeepCell/pilot/.venv/bin/python P13_DeepCell/pilot/run_pilot.py
```

This writes result JSONs and does not train. `run_pilot.py` verifies the original source hashes, constructs and exhaustively checks six PM/AIG pairs, strictly loads the named inference contracts and evaluates them on CPU. It explicitly removes only the untrained AIG connectivity head; it cannot be used to claim that head is available. It does not use upstream partial loaders.

`requirements-cpu-lock.txt` lists packages newly installed in the venv, which uses the cloud runtime's system-site packages; it is not a full clean-room environment lock. The result JSON records Python/PyTorch/PyG/NumPy versions. Package installation logs/reports and `installed_local_packages.json` are in `logs/`.

`logs/downloads.json` gives the exact immutable checkpoint URLs, byte counts and SHA256. Files are `downloads/aig_dg2.pth` and `downloads/pm_dg2.pth`. Do not fetch the denied optional graph-extension source: the completed path needs no torch-scatter install. No network is used by `run_pilot.py` itself.

Commands and errors: `COMMANDS.md`. Budget and measured resource use: `costs.json`. Detailed evidence: `results/full_model_compatibility.json`, `results/compatibility.json`, `results/integrity_results.json`, `results/paired_circuits.json`, `results/pilot_results.json`. Every result is retained, including high errors on some synthetic PM variants. No inference result establishes equivalence; exhaustive oracle evaluation provides that separate check.

Stopped at the documented bounded milestone. Future training/fusion/downstream work requires a new explicit protocol and relevant assets.
