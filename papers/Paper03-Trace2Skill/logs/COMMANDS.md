# Executed commands and scope

Working root: `/workspace/PaperReproduction`; paper directory: `papers/Paper03-Trace2Skill`.
Exact upstream directory suffix: `5702b3fe739ce33013296759162ad771ee11bd36`.

Acquisition/read-only environment commands:

```bash
git -C /workspace/PaperReproduction status --short --branch
git -C /workspace/PaperReproduction remote -v
git -C /workspace/PaperReproduction fetch origin
# Failed: couldn't find remote ref HEAD. Then checked current remote state:
git -C /workspace/PaperReproduction ls-remote origin
git -C /workspace/PaperReproduction ls-remote origin 'refs/heads/*'
# Both successful, zero refs returned.
git -C /workspace/PaperReproduction switch --orphan reproduction/trace2skill-mlcad2026
curl -fL --max-time 60 https://zenodo.org/records/21513682/files/trace2skill-v1.0.0.tar.gz -o papers/Paper03-Trace2Skill/sources/trace2skill-v1.0.0.tar.gz
# HTTP403, no retry; subsequent checksum download in && chain did not execute.
curl -fL --max-time 60 https://codeload.github.com/ldu-nvidia/Trace2Skill-Verifier-Guided-Skill-Evolution-for-Long-Context-EDA-Agents/tar.gz/5702b3fe739ce33013296759162ad771ee11bd36 -o papers/Paper03-Trace2Skill/sources/github-5702b3f.tar.gz
git ls-remote https://github.com/ldu-nvidia/Trace2Skill-Verifier-Guided-Skill-Evolution-for-Long-Context-EDA-Agents.git refs/tags/v1.0.0 'refs/tags/v1.0.0^{}'
curl -fL --max-time 60 https://arxiv.org/pdf/2605.21810 -o /tmp/trace2skill.pdf
# HTTP403; pdftotext did not execute. Original HTML was read with web tool.
docker version --format '{{.Server.Version}}'
docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}'
```

The codeload tar listing was inspected, then a stdlib extraction rejected absolute paths, parent traversal, symlinks/hardlinks and used tarfile's data filter. No archive entry was executed during extraction. The first tar listing piped to head ended with expected stdout closed diagnostic after listing; full extraction succeeded separately.

Offline validation (from upstream directory; no installs):

```bash
python3 scripts/validate_paper_results.py --json-out ../../metrics/official_validation.json > ../../logs/official_validation.txt
```

Independent analysis (from Paper03 directory):

```bash
python3 analysis/recompute.py > logs/independent_audit.txt
python3 analysis/replay.py > logs/replay.txt
MPLCONFIGDIR=/tmp/t2s-mpl python3 analysis/plot.py
```

`recompute.py` ran first with count/selector/statistics checks and again after adding independent AUC/task-hour audits. `replay.py` first stopped with a coordinate-key error, corrected to retain original coordinate, then passed all19 checks. `plot.py` first used matplotlib fallback /tmp cache and produced valid images; the reproducible command explicitly sets writable cache. Official validation and final release checks also rerun the cached validator; these are offline passes, never new live attempts.

Selected static review: validator imports/call sites and whole routine logic; release checker; exporter check path; original helper/test modules; setup and downloader instructions without execution; standard EA carry/mutate/defer branches; verifier private-copy path, feedback summarizer and gate order; configs, model budgets, runtime retry policy, licenses and provenance. Relevant source is retained in unmodified upstream with hashes. No arbitrary upstream install scripts, endpoint calls or container launches ran.
