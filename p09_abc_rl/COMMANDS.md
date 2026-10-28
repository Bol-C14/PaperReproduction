# Commands and source provenance

All commands ran in `/workspace/PaperReproduction` in the selected cloud, never a Mac. No AGENTS.md existed under `/workspace` or the fetched base. The user-authorized repository was already configured as `https://github.com/Bol-C14/PaperReproduction.git` with an unborn local branch.

```bash
git ls-remote --heads origin
git fetch --depth=1 origin reproduction/aspen-mlcad2025
git switch -c reproduction/abc-rl-iclr2024 FETCH_HEAD
# Preserve all inherited files; add only p09_abc_rl/.
git commit -m 'Freeze bounded CPU ABC-RL protocol and preserve audited upstream snapshots'
python3 -m venv p09_abc_rl/.venv
p09_abc_rl/.venv/bin/pip install --no-cache-dir 'torch==2.6.0+cpu' --index-url https://download.pytorch.org/whl/cpu
p09_abc_rl/.venv/bin/pip install --no-cache-dir numpy==2.2.6 scipy==1.15.3 torch-geometric==2.6.1 transformers==4.48.3 gym==0.26.2
curl --fail -L --max-time 60 'https://raw.githubusercontent.com/NYU-MLDA/ABC-RL/db6186cb4018963b5bc15926772c3edc0c2873f1/ABC-RL_ICLR/dump/pretrained_models/pretrained_TTSPLIT_5001/nn_model.pt' -o p09_abc_rl/assets/nn_model.pt
git ls-remote https://github.com/berkeley-abc/abc.git HEAD
# This source GET failed403. Do not retry without materially new authorization/access evidence.
curl --fail -L --max-time 40 -D p09_abc_rl/logs/bert_config_headers.txt 'https://huggingface.co/google-bert/bert-base-cased/resolve/main/config.json' -o p09_abc_rl/assets/bert_config.json
python3 p09_abc_rl/port/build_repaired.py
p09_abc_rl/.venv/bin/python p09_abc_rl/tests/test_contract.py
p09_abc_rl/.venv/bin/python p09_abc_rl/tests/check_structural_loading.py
p09_abc_rl/.venv/bin/pip freeze --all > p09_abc_rl/configs/installed.lock
```

Official CPU PyTorch distribution index and published NumPy/SciPy/PyG/HuggingFace Transformers/Gym distributions were used in an isolated venv. All direct versions are pinned above; exact transitive installed versions appear in the lock. No unknown installer script, privilege escalation or system package changes were used. Tensor checkpoint source is the author-linked repository established in ASSET_AUDIT.md; it is safe-loaded with restricted tensor unpickling. BERT was requested from the canonical google-bert model repository, but its revision/content was not obtained. BerkeleyABC source identity was read-only discovered and not executed. Native Yosys/ABC sources are not substituted with an unrelated package.

The local snapshot manifest in assets.json records original file URLs and SHA256. Protocol commit and verification script make subsequent source/repair changes inspectable. These commands are a recorded setup recipe, not a claim that rerunning gated downloads will succeed.
