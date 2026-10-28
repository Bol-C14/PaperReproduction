# Commands and execution boundary

Mac controls APRIL through existing strict `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes april1`. The approved root and private original logs are recorded outside this public package. Set `APRIL_ROOT` to that existing root. All commands below are per-project; no global dependencies, credentials, networks or services were changed.

Source acquisition already performed (do not redownload to replay):

```bash
git clone https://github.com/lmarena/arena-hard-auto.git "$APRIL_ROOT/checkouts/arena-hard/upstream"
git -C "$APRIL_ROOT/checkouts/arena-hard/upstream" checkout --detach 19412d70c6e05f02740c5ffdf2b0c22795d06637
python3 "$APRIL_ROOT/checkouts/arena-hard/prepare.py" "$APRIL_ROOT/assets/arena-hard"
```

The public HF tree metadata was fetched before freezing paths; only 61 frozen paths were subsequently acquired by `prepare.py`, all at `15f3746e21432264ce9b453999bde4f3c946d2e6`. The arXiv v2 PDF was fetched and its appendices read through pdftotext. Raw responses and judgments remain in private APRIL assets; public metadata includes SHA-256 hashes and exact URLs.

Environment creation already performed:

```bash
UV_CACHE_DIR="$APRIL_ROOT/cache/arena-hard/uv" uv venv --python 3.11 "$APRIL_ROOT/envs/arena-hard"
UV_CACHE_DIR="$APRIL_ROOT/cache/arena-hard/uv" uv pip install --python "$APRIL_ROOT/envs/arena-hard/bin/python" numpy==1.26.4 pandas==2.2.3 scikit-learn==1.3.2 scipy==1.13.1 tqdm==4.67.1 PyYAML==6.0.2 requests==2.32.3
uv pip freeze --python "$APRIL_ROOT/envs/arena-hard/bin/python"
```

Copy this package's analysis scripts into the existing `checkouts/arena-hard/` directory. Reproduce without new downloads or API access:

```bash
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
PY="$APRIL_ROOT/envs/arena-hard/bin/python"
"$PY" "$APRIL_ROOT/checkouts/arena-hard/diagnose.py" "$APRIL_ROOT"
"$PY" "$APRIL_ROOT/checkouts/arena-hard/replay.py" --assets "$APRIL_ROOT/assets/arena-hard" --upstream "$APRIL_ROOT/checkouts/arena-hard/upstream" --out "$APRIL_ROOT/results/arena-hard"
"$PY" "$APRIL_ROOT/checkouts/arena-hard/verify.py" "$APRIL_ROOT"
```

Generation entrypoints, API clients, the notebook and its pickle input were never executed. Historical notebook source and JSON outputs are read as public evidence. Parent scheduling pause was respected at a process-free boundary, then the same G5 task resumed after a slot became free. No extra parallel paper tasks or workers were created.
