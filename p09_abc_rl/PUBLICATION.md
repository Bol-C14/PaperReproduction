# Public Round2 export

This branch publishes the P09 ABC-RL research source, preserved upstream text snapshots and license, separate repair patch, frozen protocol, dependency pins, actual unit/structural-load logs, metrics, failure evidence and methodology/status reports. No new research run was added for publication.

Scientific status remains: seven deterministic contract tests passed; real author-checkpoint26tensor structural CPU load passed using fail-closed external-encoder placeholders. No policy inference, circuit/ABC evaluation, equivalence evaluation or training ran. No full-paper or behavioral reproduction is claimed. Read REPRODUCTION.md and BERT_RESOURCE_BLOCKER.md before interpreting results. Inference compatibility is not established by structural state loading.

The paper branch was based on an existing public ASPEN branch. Its inherited history and files are retained unchanged; they are previous-paper context, not P09 experimental results. Only the paper branch is pushed, without merge, deletion, force push, PR, repository visibility change or alteration to other paper branches.

## Excluded assets

| Asset | Size / SHA256 | Provenance / recovery |
|---|---|---|
| External unchanged author policy `p09_abc_rl/assets/nn_model.pt` |1401370bytes; `d4747eeff16c7247acf8f1480a33f2239a1a51adaac78a0a6e915c5ba12164f5` | Author-linked NYU-MLDA/ABC-RL revision `db6186cb4018963b5bc15926772c3edc0c2873f1`, path `ABC-RL_ICLR/dump/pretrained_models/pretrained_TTSPLIT_5001/nn_model.pt`; exact pinned download URL in COMMANDS.md. Excluded from Git as an external model asset; metadata/hashes and inspection results included. External download or retained local/private backup copy required. |
| Installed `.venv` and paper-local compiled caches |1285642002bytes recorded in the migration inventory; replaceable environment, not a single upstream asset | Rebuild from configs/installed.lock and COMMANDS.md. Exact installed-distribution pins and original pip logs retained. Byte-identical installed environment is not promised across machines. Full per-file hash inventory remains with the separately retained private recovery archive, not published. |
| BERT model/config/tokenizer | Never obtained; payload size/hash/revision unavailable. Approx430–440MB is a planning estimate only. | `google-bert/bert-base-cased`; prior first public config GET returned403; no retry. Required local bundle, licensing/revision uncertainty and compatibility requirements are recorded in BERT_RESOURCE_BLOCKER.md. |
|7nm library/circuit payloads and native ABC/abc_py/torch_sparse runtime | Not downloaded/installed in this pilot; no payload hashes available | Public sources and inspected metadata are in ASSET_AUDIT.md/assets.json. Native ABC HEAD was identified read-only in logs/abc_remote.txt. These remain separate preflight requirements. |
| Generated recovery archives, Git bundles, transfer helpers/receipts | Kept outside this Git repository; not published | Existing private recovery archive is preserved; no repeat upload or deletion. |

No small user-generated experiment checkpoint exists in this phase. The excluded policy is an unchanged external author asset. Upstream source snapshot SHA256 values are in assets.json, and the downloaded checkpoint SHA256 is repeated in results/checkpoint_inspection.json.

## Public release screening

Before publication, a local pattern scan examined all branch-reachable commit contents and blobs plus all tracked working files. Patterns cover private keys, common cloud/GitHub/OpenAI-style token forms, credentials in URLs, bearer/JWT values, authentication/cookie header lines, selected internal service hostnames and environment-secret dump markers. No findings were detected. Generated archives, credential stores, Git config/hooks, environments and unrelated workspace/personal files are excluded. The scan does not prove absence of every possible secret format. Git author attribution and public upstream source author paths remain ordinary research provenance.

The independent remote-ref verification and full publication SHA are recorded in the task result outside the commit, avoiding a self-referential commit hash. No full environment dump or access settings are published.
