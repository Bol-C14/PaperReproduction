# Public release checklist

- [x] Include the Apache-2.0 root `LICENSE` and package metadata.
- [x] Preserve the upstream NeMo Gym `LICENSE`.
- [x] Include the pinned CVDP dataset `LICENSE` and `NOTICE` terms.
- [ ] Obtain final owner review for the source, prompts, evidence, dataset
  attribution, and paper metadata.
- [x] Run `./scripts/check_public_release.sh`.
- [x] Run `python3 scripts/validate_paper_results.py`.
- [x] Run the unit suite and public data-materialization smoke.
- [x] Confirm no generated `data/`, `runs/`, environment, bundle, image, or
  model-exchange files are tracked.
- [x] Tag the exact Git commit deposited to Zenodo.
- [x] Add the Zenodo DOI to `CITATION.cff`, README, and Artifact Appendix.
- [ ] Confirm the live Git repository and Zenodo snapshot are byte-consistent.
