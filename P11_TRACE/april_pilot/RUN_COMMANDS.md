# Executed command record

`APRIL_ROOT` denotes the user-designated isolated APRIL workspace. Machine-specific
absolute prefixes are replaced by this variable in public logs. Mac edits were
transferred to `checkouts/trace/P11_TRACE/april_pilot/`; branch base was2f33a6b.

```sh
git clone --depth 1 --single-branch --branch reproduction/trace-dac2026 https://github.com/Bol-C14/PaperReproduction.git "$APRIL_ROOT/checkouts/trace"
python3 -m venv "$APRIL_ROOT/envs/trace"
"$APRIL_ROOT/envs/trace/bin/python" -m pip install --cache-dir "$APRIL_ROOT/cache/trace/pip" torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
"$APRIL_ROOT/envs/trace/bin/python" -m pip install --cache-dir "$APRIL_ROOT/cache/trace/pip" numpy==2.0.2
```

Official URLs and SHA256s are in asset_receipt.json and DATASET_METADATA.json.
CPU commands below ran from the Mac through the existing SSH alias `april1`:

```sh
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 "$APRIL_ROOT/envs/trace/bin/python" "$APRIL_ROOT/checkouts/trace/P11_TRACE/april_pilot/run_real_pm.py" "$APRIL_ROOT/assets/trace/iccad_dc_pm.npz" "$APRIL_ROOT/assets/trace/official_pm_probability.pth" "$APRIL_ROOT/results/trace/real_pm_v1"
"$APRIL_ROOT/envs/trace/bin/python" "$APRIL_ROOT/checkouts/trace/P11_TRACE/april_pilot/verify_outputs.py" "$APRIL_ROOT/results/trace/real_pm_v1"
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 "$APRIL_ROOT/envs/trace/bin/python" "$APRIL_ROOT/checkouts/trace/P11_TRACE/april_pilot/run_operand_role.py" "$APRIL_ROOT/assets/trace/iccad_dc_pm.npz" "$APRIL_ROOT/assets/trace/official_pm_probability.pth" "$APRIL_ROOT/results/trace/real_pm_v1"
```

Mac independently ran verify_outputs.py with Python3 and NumPy2.4.1 after retrieval,
and recomputed role-lesion saved-array MAE and operand reversal differences.
INDEPENDENT_VERIFICATION.json is APRIL verification; MAC_VERIFICATION.json and
ROLE_VERIFICATION.json record the separate saved-array checks. No benchmark
optimizer or API budget batch was invoked.
