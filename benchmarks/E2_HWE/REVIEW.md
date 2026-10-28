# HWE-Bench — source and evaluator review

This is PKU's **hardware bug-repair** benchmark, not the similarly named CPU-design benchmark. The paper is [arXiv:2604.14709v3](https://arxiv.org/html/2604.14709v3), dated 2026-05-05. Paper type: benchmark/dataset and empirical agent evaluation. Contribution: repository-scale hardware repair tasks, executable verification environments, and construction methodology. Venue: **arXiv preprint; accepted venue unverified**. CCF: **unknown**, because no accepted venue or dated official CCF mapping was established. An arXiv subject classification is not a venue ranking. No appendix appears in the retrieved full v3 HTML; repository documentation was reviewed as implementation material.

## Claims and mechanism

The paper reports 417 historical repair tasks from six hardware projects, with generated problem descriptions and simulation-based checking. OpenTitan accounts for 245 tasks and needs VCS; the other 172 use open tools. Its strongest reported system resolves 295/417 (70.7%). Agent runs allow six hours and 500 iterations. These are **paper claims**, not results reproduced here. Model/framework pairings and subscription/API access differ, so the table measures complete agent systems. Cross-benchmark comparisons use externally reported software scores; they are not a controlled domain experiment.

The main mechanism transfers the SWE-bench issue-to-patch-to-test structure into heterogeneous hardware repositories. VerilogEval/RTLLM cover component generation, CVDP broadens component-level tasks, and HWFixBench supplies repair-oriented comparison. These are explicit prior-work collisions acknowledged by the paper, so the defensible contribution is domain-specific task/environment construction and evidence, rather than invention of execution-based repository repair. The broad “first” claim was not independently established by an exhaustive literature search.

## Frozen current release, separate from the paper protocol

[Official source](https://github.com/pku-liang/hwe-bench/tree/10c78a87e1f92695d78d15b1464a6107dcac8837): `10c78a87e1f92695d78d15b1464a6107dcac8837` (2026-08-01 UTC). [Dataset](https://huggingface.co/datasets/henryen/hwe-bench/tree/82a42e0a05719366a326e09ddc668ea0d46c91f6): `82a42e0a05719366a326e09ddc668ea0d46c91f6` (2026-04-23). These dates do not make the current harness equivalent to the May paper environment.

The release's July update changes the vendored Harbor snapshot to upstream `00c19fe2` (package version still 0.20.0), adds explicit no-external-access instructions, and adds/re-evaluates leaderboard systems. Task templates nevertheless request public agent networking; the verifier template requests no network. This is a documented policy/mechanism distinction. Harbor reward is deliberately always zero; benchmark scoring occurs in the offline evaluator. Neither reward zero nor a Harbor process exit constitutes task correctness.

Code, vendored Harbor, and dataset metadata declare Apache-2.0; the paper HTML links CC BY 4.0. Selected Ibex images contain Apache-2.0 LICENSE files. Selected CVA6 images contain Solderpad Hardware License 0.51 plus Berkeley BSD-3-Clause and SiFive Apache notices; per-image file hashes and excerpts are in `raw/image_licenses.json`. Container dependencies retain their own licenses. No blanket Apache assertion is made for image contents. No images, datasets, reference fixes, or hidden test scripts are vendored in this report package.

## Direct evaluator evidence

See `raw/controls-local/evaluator_controls.json`, `raw/controls-local/history_finalize.log`, and the reproducible `scripts/evaluator_controls.py`. These are **source-level fixtures**, not benchmark tasks, hardware verification, or live-agent outcomes. Unchanged parser/report/finalizer AST nodes are executed; only unused serialization decorators/metadata are replaced with no-ops.

* The parser/report rejects a bare PASS, a failing no-op, a previously passing baseline, a partial fix leaving another test failing, and disappearance of a previously reported test.
* It accepts a declared FAIL→PASS transition. It also accepts NONE→PASS and SKIP→PASS as valid, although those do not by themselves establish genuine fail-to-pass behavior. A missing compiler/tool can therefore be confused with a broken baseline unless the raw simulator evidence is inspected.
* A PASS followed by a timeout or crash message is accepted by the report logic. The Docker runner records a timeout string but returns log text to the scorer, without including process status in the report's success predicate. Result brackets can also exclude outer failure markers. These controls demonstrate sensitivity limits of the log/report boundary; they do not prove an observed benchmark exploit.
* The finalizer removes remotes, extra refs, reflogs and unreachable future objects, but retains ancestry reachable from the baseline. An exact-script fixture retained two reachable commits and pruned its unreferenced future commit. This is insufficient evidence for a literal “truncated to one commit” guarantee. Ancestor retention alone does **not** prove that a particular hidden fix exists in a published image. Actual image-level history checks must be distinguished from this fixture.
* Ibex runtime `fix-run.sh` uses `git apply ... || true`, so patch application failure must be checked independently. The offline Docker utility does not explicitly set network isolation; the Harbor verifier template does. Our replay must enforce isolation itself and label the Podman orchestration change.

## Selection, sensitivity, and inference limits

`selection.json` freezes four tasks before simulation: the first two numeric PRs in each pinned Ibex/CVA6 file. This is reproducible convenience sampling, biased toward earlier tasks and unsuitable for estimating all-417 resolved rate. Every selected task stays in the outcome table, including setup failures and timeouts. Other projects were excluded before selection: OpenTitan requires unavailable licensed VCS; the three remaining open-tool projects were outside this four-task/two-repository pilot.

All four selected dataset records have one declared fail-to-pass test and **zero declared pass-to-pass tests**. Published reference outcomes are metadata, not fresh replay evidence. The selected CVA6 PR 1482 checks a Spike/CVXIF software component rather than a whole RTL core simulation; per-task native flows matter more than the repository-level simulator label.

Reference replay calibrates the evaluator only. A reference patch passing a narrow simulation does not establish ISA-wide, cycle-wide, four-state, formal, timing, or system correctness. A useful next sensitivity experiment compares partial, overfitted, and semantically equivalent implementation changes against independent checks while retaining the official score unchanged. General agent claims remain untested until calibration and a separately budgeted live pilot complete.

## Relevant upstream discussion

[Issue #9](https://github.com/pku-liang/hwe-bench/issues/9), opened 2026-10-12, proposes a separate reproducer-writing track and reports acceptance of incorrect patches on other Ibex tasks. This is an external contributor's report, not our validation or a maintainer-confirmed fix. It is prior evidence motivating independent sensitivity controls; similar findings here must not be presented as a novel benchmark critique. Its tasks differ from our frozen sample. Our parser fixtures alone establish no native false acceptance.

In [issue #3](https://github.com/pku-liang/hwe-bench/issues/3), a project contributor explicitly explains that curated behavioral reproducers may instantiate individual modules or subsystems and that a passing score does not certify an upstream-ready integration patch. Full integration compilation is outside the current default score. This clarification is consistent with the Ibex module-level flows inspected here and narrows how the paper's repository-level framing should be interpreted. A smaller patch or a difference from the reference alone is therefore not sufficient evidence of incorrectness.


## Fresh native findings

Four preselected base/reference pairs now satisfy native behavioral fail-to-pass, with patch applicability independently checked and no timeouts. `raw/final/native_results.json` records outcomes and costs. This is reference calibration under the declared Podman orchestration port; it is not a model score or replication of the paper's agent table.

On the calibrated **Ibex PR 48 compressed-decoder task only**, both a partial family repair and an overfitted implementation pass the unchanged official native test and upstream report logic. Independently compiled checks reject them on 15/31 and 30/31 inputs in the task-described HINT family, respectively. Full fixed-domain comparison finds 480 and 45,000 differences from the reference across 65,536 inputs. An alternative expression passes and matches the reference on those 65,536 two-state inputs, with upper 16 bits zero; this is not universal ISA, four-state or full-chip equivalence. These are observed native coverage limits, independently checked against the described family, rather than only synthetic scorer anomalies. The official score was not changed. This small, deliberately adversarial sample gives no estimate of the benchmark-wide false-acceptance rate.

All reference patches apply cleanly. Image history retains ancestors, but none of 15 candidate fixing/merge objects checked across the four images exists. No actual solution-history leak was demonstrated. CVA6's prepared runtime baseline can differ from the upstream base and is pinned separately. The fresh findings reinforce a narrow interpretation of scores: curated behavioral repair, with explicit regression-coverage limitations. No live-agent experiment was run.
