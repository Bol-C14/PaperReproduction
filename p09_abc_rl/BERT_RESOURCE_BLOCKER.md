# BERT asset blocker clarification — no new request or experiment

This clarification uses only saved headers, code and checkpoint inspection. The completed result remains seven passing tests, structural-only checkpoint loading, zero policy inference and zero ABC evaluations. No denied download was retried.

## Model identity and revision

- Upstream source identifier: `bert-base-cased` in both `BertModel.from_pretrained` and slow `BertTokenizer.from_pretrained`.
- Canonical asset target used for the single attempted GET: `google-bert/bert-base-cased` on Hugging Face, URL `https://huggingface.co/google-bert/bert-base-cased/resolve/main/config.json`.
- Requested revision: **main**, a moving reference. **Resolved immutable revision: unknown.** The403 arrived before any config or `x-repo-commit` metadata was obtained. Upstream code also has no `revision=` pin. No exact model commit used for the historical policy checkpoint has been established.
- Compatibility requirement from inspected code/checkpoint: pooled recipe embedding has768 dimensions and must come from the same cased BERT encoder/tokenization semantics. The1.4MB ABC-RL checkpoint contains no BERT parameters, so it cannot supply the missing encoder.

## Smallest compatible local bundle

Supply a single local directory from one coherent canonical snapshot, with:

1. `config.json` — model architecture/configuration.
2. `model.safetensors` — complete compatible model weights, preferred safe format. An original `pytorch_model.bin` is an alternative, not an additional required copy; its provenance and safe-loading compatibility would need checking.
3. `vocab.txt` — WordPiece vocabulary for the explicitly used slow `BertTokenizer`.
4. `tokenizer_config.json` — preserve canonical settings, especially **do_lower_case=false**. Omitting this when loading from a local directory can cause default lowercasing and change the recipe embeddings.

Also include `special_tokens_map.json` **if supplied by that canonical snapshot**, to preserve its token configuration. The above are loader requirements, not a claim that we inspected the remote file listing. Fast-tokenizer `tokenizer.json`, optimizer state, training data, TensorFlow/Flax/ONNX copies and duplicate weights are unnecessary for this CPU inference route.

Include a small provenance manifest: source model ID, resolved immutable commit/revision, SHA256 of every supplied file, and applicable model license/notice. Copy its model card and license/notice files if present; their contents are not yet verified here. A local directory can be selected through the port's `ABC_RL_BERT_PATH`; no credential, account token or settings change is requested.

**Size:** no model size metadata was successfully retrieved. A complete FP32 BERT-base-cased bundle is expected to be roughly **430–440MB decimal (about410–420MiB)** plus sub-megabyte tokenizer/config files. This is an architecture-based planning estimate, not observed payload metadata or an exact download size. Quantization/alternate encoder weights would be a new port requiring compatibility validation, not the smallest known faithful replacement.

**License:** the canonical model's license and redistribution terms were **not inspected/verified**. Do not present an Apache license assumption as confirmed. The ABC-RL repository's observed GPL-3.0 does not establish the external model's license. Provide the canonical license/model-card evidence with the bundle.

## What the403 establishes

Saved response headers in `logs/bert_config_headers.txt` show:

```
HTTP/1.1 403 Forbidden
content-length: 16
content-type: text/plain
server: envoy
connection: close
```

There is no saved error body because curl used `--fail`, and no `WWW-Authenticate`, Hugging Face error header, `x-repo-commit` or other origin-identifying diagnostic. **Source authorization/access denial versus platform/egress proxy denial cannot be determined from this evidence.** `server: envoy` is consistent with an intermediary/proxy, but it does not prove which side generated the rejection. This must not be labeled a confirmed Hugging Face authentication requirement or a confirmed platform-proxy block. The exact status is an unlocalized HTTP403 on the first public asset GET; no automatic approval rejection occurred.

The requested local bundle resolves the immediate access dependency without diagnosing or changing access controls. Its availability would enable the next inference preflight, not automatically authorize experiments or establish full-paper compatibility. Native ABC/abc_py/torch_sparse setup and retrieval-bank provenance remain separate, documented preflight work.
