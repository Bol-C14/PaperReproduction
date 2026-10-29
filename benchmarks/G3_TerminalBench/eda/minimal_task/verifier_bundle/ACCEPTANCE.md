# Trusted verifier acceptance contract — template

Freeze a separate tool image, functional golden model, seed, hidden stimuli/properties, libraries/corners and constraint interpretation. Never expose this bundle to the evaluated agent. The public template contains no actual hidden tests or reference answers.

1. Validate artifact path/schema/size/hash and immutable input hashes; reject stale outputs.
2. Re-elaborate candidate in a clean workspace; independently check functionality including reset and edge cases.
3. Recompute timing/area/power with trusted tool binaries and fresh reports. Check all declared corners and uncertainty/tolerances.
4. Produce machine-readable results with separate infra_error, timeout, functional_failure, and metric_failure; attach tool versions and artifact hashes. Do not reward stdout, a claimed PASS, or a successful shell exit alone.
5. Preserve enough artifacts to regrade verifier-only fixes. Kill/reap trial descendants on timeout and demonstrate a fresh reset before the next trial.
