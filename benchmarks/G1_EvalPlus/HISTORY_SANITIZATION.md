# G1 publication-history sanitation

The proposed publication commit is reconstructed directly on public baseline `809ca20e003c2f5d5a723c77ead8a6de532e4539`. Its tree preserves every baseline path and adds only the exact G1 whitelist in PUBLICATION_MANIFEST.json.

All original final G1 payload files remain byte-for-byte identical to source commit `880d8a30598d272efb19da07b33bb41167f6804b`. The only additions are this note and the publication manifest. No experiment, model/API call, download, upstream modification or push is part of this operation.

The two original experiment commits remain private in `refs/private/g1/original-880d8a3` and a verified incremental bundle requiring the public baseline. Neither is an ancestor of the proposed public branch. Do not push private refs, the original branch history or the bundle.

Four reviewed path-bearing historical blobs must not be reachable from the proposed public ref:

- `eacda189fa18b7fcfb413863b7a4226145f07fe0`
- `a166fa78c2c23f5a91c9c51c4a85761f0343658e`
- `a1a72286627f3e01b1dc693451b9f97bb1962c59`
- `a29438a74ceca21e61328fa46bcd6b7ffdae77af`

A separate receipt records the exact clean commit/tree, complete whitelist/blob inventory, raw-evidence verification, baseline preservation and forbidden-object reachability check. A private raw-evidence directory, caches and oracle helper remain excluded from the publication payload. Cache-specific licensing remains unresolved; no cached code or full witness is included.
