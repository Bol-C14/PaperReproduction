# Round2 checkpoint preservation

All43 locally generated checkpoint files are now included unchanged. Individual files range from270643 to1697611 bytes; total70122411 bytes. This is a normal follow-on commit, not a force push. The full recovery archive is not published.

| Origin | Files | Public status |
|---|---:|---|
| Valid v2 main pretrain/adaptation |30 |Included |
| Invalid attempts retained for audit |11 |Included; not valid performance evidence |
| Actual v1 trained pilot |2 |Included |
| Original upstream PM pretrained asset |1 |External pinned URL/hash; unmodified |

Each file size, SHA256, role, provenance and regeneration limits are in CHECKPOINT_INVENTORY.json. Generated weights can generally be rerun from included code/seeds, but cross-version bitwise identity is not assumed. Failed unpaired-RNG snapshots especially warrant exact-byte preservation.

## Per-file inventory

| File | Bytes | Origin |
|---|---:|---|
| `P11_TRACE/closure/attempt1_invalid_direct_clamp/weights/2026_direct_comparator_adapt.pt` |1697121 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt1_invalid_direct_clamp/weights/2026_direct_pretrain.pt` |1696497 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt1_invalid_direct_clamp/weights/2026_direct_priority_selector_adapt.pt` |1697611 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt1_invalid_direct_clamp/weights/2026_direct_ripple_carry_adapt.pt` |1697261 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_direct_comparator_adapt.pt` |1697121 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_direct_pretrain.pt` |1696497 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_direct_priority_selector_adapt.pt` |1697611 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_direct_reconvergent_mux_adapt.pt` |1697541 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_direct_ripple_carry_adapt.pt` |1697261 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_fsl_pretrain.pt` |1696287 |user_generated_invalid_attempt |
| `P11_TRACE/closure/attempt2_unpaired_dropout/weights/2026_fsl_ripple_carry_adapt.pt` |1697051 |user_generated_invalid_attempt |
| `P11_TRACE/closure/official_pm_probability.pth` |4241614 |upstream_pretrained |
| `P11_TRACE/closure/weights/2026_direct_comparator_adapt.pt` |1697121 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_direct_pretrain.pt` |1696497 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_direct_priority_selector_adapt.pt` |1697611 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_direct_reconvergent_mux_adapt.pt` |1697541 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_direct_ripple_carry_adapt.pt` |1697261 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_fsl_comparator_adapt.pt` |1696911 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_fsl_pretrain.pt` |1696287 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_fsl_priority_selector_adapt.pt` |1697401 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_fsl_reconvergent_mux_adapt.pt` |1697331 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2026_fsl_ripple_carry_adapt.pt` |1697051 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_direct_comparator_adapt.pt` |1697121 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_direct_pretrain.pt` |1696497 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_direct_priority_selector_adapt.pt` |1697611 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_direct_reconvergent_mux_adapt.pt` |1697541 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_direct_ripple_carry_adapt.pt` |1697261 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_fsl_comparator_adapt.pt` |1696911 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_fsl_pretrain.pt` |1696287 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_fsl_priority_selector_adapt.pt` |1697401 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_fsl_reconvergent_mux_adapt.pt` |1697331 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2027_fsl_ripple_carry_adapt.pt` |1697051 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_direct_comparator_adapt.pt` |1697121 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_direct_pretrain.pt` |1696497 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_direct_priority_selector_adapt.pt` |1697611 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_direct_reconvergent_mux_adapt.pt` |1697541 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_direct_ripple_carry_adapt.pt` |1697261 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_fsl_comparator_adapt.pt` |1696911 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_fsl_pretrain.pt` |1696287 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_fsl_priority_selector_adapt.pt` |1697401 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_fsl_reconvergent_mux_adapt.pt` |1697331 |user_generated_v2_valid |
| `P11_TRACE/closure/weights/2028_fsl_ripple_carry_adapt.pt` |1697051 |user_generated_v2_valid |
| `P11_TRACE/pilot/direct_pilot_weights.pt` |270643 |user_generated_v1_pilot |
| `P11_TRACE/pilot/residual_pilot_weights.pt` |270873 |user_generated_v1_pilot |

## Remaining upstream asset

`P11_TRACE/closure/official_pm_probability.pth`:4241614 bytes; SHA256 `19fe1e95857072e5eb838802ee21260ffe48345df85785f9f6ddd0e784cad7c0`. This original checkpoint was loaded read-only and is not uniquely modified. It remains omitted because upstream redistribution terms are not independently verified, rather than because this file exceeds GitHub size limits.

[Pinned public upstream bytes](https://raw.githubusercontent.com/zyzheng17/TRACE_DAC26/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/checkpoints/trace_predictive_pm_probability.pth). AIG/PM contrastive checkpoints used only in the asset audit likewise remain unmodified external assets, with their sizes/hashes/URLs in the JSON inventory. No essential uniquely generated saved checkpoint requires a separate backup.

Research metrics and datasets were not changed; no optimizer step or new scientific experiment ran in this preservation follow-up.
