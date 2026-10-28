# Public branch publication review

Date: 2026-10-28. Destination authorized by the user: existing public repository `Bol-C14/PaperReproduction`, branch `reproduction/crop-iccad2025`. No repository visibility change, PR, merge, forced update, or branch deletion is part of this publication.

## Scope and scientific boundaries

The branch contains the P15 asset audit, preserved twelve-call preliminary study, and expanded CROP-inspired non-model experiment. The expanded study closes retrieval, legal configuration proposal, actual free synthesis, target-history updates, and subsequent selection with matched online controls. It does not implement semantic summarization/embedding or LLM search. Its independently authored circuits and LUT count/depth proxies do not reproduce industrial RTL Architect PPA. Structural retrieval did not outperform random-prior retrieval. Original CROP code availability remains unverified.

The [expanded report](closed_loop/README.md), [mechanism coverage](closed_loop/MECHANISM_COVERAGE.md), [actual metrics](closed_loop/measurements.csv), [trace summary](closed_loop/trace_summary.csv), and [commands/costs](closed_loop/COMMANDS.md) state these limits and preserve negative results, preliminary failures, versions, seeds, and tool substitutions. No new research run was performed for publication.

## History and secret review

The existing local snapshot `c5ce2b6f357a431fe75ecd98530efb354c1f539d` was inspected before adding this note. It is a single root commit with 2,539 tracked paths and 1,910 reachable Git objects, including 1,605 unique blob objects totaling 15,581,180 bytes. The largest blob is 343,904 bytes. Git naturally deduplicates repeated experimental artifacts.

The review scanned all reachable blob contents and commit/tag metadata, not just the working tree. Checks covered private-key blocks, recognizable provider token formats, access-key formats, authentication headers, credential assignments, URL-embedded credentials, sensitive environment assignments, internal-service identifiers, and personal home-directory paths. No pattern match was found. A broader contextual pass over sensitive terms identified four documentation/source files; manual inspection confirmed they discuss absent credentials, access boundaries, and local bootstrapping rather than containing credential values. Commit author metadata was reviewed as ordinary research Git provenance.

All tracked paths belong to `P15_CROP/` or `reproduction/crop-iccad2025/`. There are no tracked archives, installed environments, caches, bytecode, model weights, or package binaries. The final publication commit is checked again over its complete reachable history before pushing. This documents the performed pattern and contextual review; it does not claim a formal proof that arbitrary data can never contain secrets.

No sensitive-history remediation was needed. The original local `work` branch and root commit are preserved unchanged; the paper branch contains that history plus this publication note. No experimental record or metric was edited for publication. No separate recovery archive was created, deleted, or uploaded in this task.

## Included evidence and omitted runtime assets

Included: independently authored RTL and Python source, frozen manifests/options, hashes, small ABC scripts, JSON contexts and archives, tool commands and logs, mapped netlists and equivalence references, actual metrics, analysis, and reports. Keeping raw small artifacts allows checking the claims without accepting only a prose summary.

Omitted from Git, preserved locally:

| Asset | Exclusion and reproducibility evidence |
| --- | --- |
| Earlier YoWASP installed Python environment and compiled WASM cache | `.gitignore` excludes `toolchain/` and `cache/`; pinned versions and wheel SHA-256 values are in `requirements.lock` and `install-report.json`. The cache is derived from those runtime assets. |
| Native Yosys/ABC Debian packages and extracted installation | `closed_loop/.gitignore` excludes `native/*.deb` and `native/root/`; exact public package URLs, byte counts, and SHA-256 values are in `closed_loop/native/downloads.json`. `bootstrap_native.py` restores and checks the package pins locally. |
| Python bytecode caches | Excluded; reproducible from the committed source. |
| Model weights or semantic caches | None downloaded/generated. Denied access attempts are recorded in `closed_loop/model_access_check.json`; no artifact hash can be claimed for a nonexistent local download. |
| Recovery archives | None created by this paper task; none published. |

The native tools remain usable in this cloud workspace. Their large installed files are not needed in the public history because their lawful public provenance, exact package hashes, and restoration commands are retained. Publication does not rerun or alter either experiment.

## Remote handling

Read-only remote-ref inspection showed the intended CROP branch did not exist. The generic local `work` snapshot was given the dedicated paper branch name without changing or deleting `work`. Only `refs/heads/reproduction/crop-iccad2025` is pushed, using an ordinary non-forced update. Other paper branches and the repository's default branch are outside this update. An independent remote-ref read must match the full local paper-branch commit SHA before publication is reported as verified.
