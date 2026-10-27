# Exact failures and outcomes

- `curl -L --fail https://jpan.me/files/ISPD26_AstroTune.pdf`: HTTP 403, denied by remote/network route; no PDF file downloaded. Official PDF readable through web extraction, all 9 pages including references read. No attempt to bypass restriction.
- `apt-get update && apt-get install -y yosys iverilog openroad`: update failed on read-only `/var/lib/apt/lists/partial`; install did not execute.
- `docker manifest inspect openroad/flow-ubuntu22.04:latest` and `openroad/flow-scripts:latest`: registry denied/unauthorized; no manifest, no credential setup attempted. Official current image is `openroad/orfs:latest`.
- `docker pull openroad/orfs:latest`: `failed to register layer: no space left on device`; image not registered. `efabless/openlane:2023.09.07` subsequently downloaded, but `docker run ... --name astrotune-eda ...` failed `no space left on device`; `docker ps -a` confirmed no container. Docker storage used substantially more space than reported image size (consistent with layer duplication, not independently proven).
- `docker image prune -f`: completed, reclaimed 0B.
- `docker system prune -f`: **denied by automatic approval review; did not execute**. Reason: broad irreversible deletion could remove unrelated stopped containers/data. Never retried and not bypassed. No approval is needed to finish the reproduction because a narrower alternative succeeded.
- `docker image rm efabless/openlane:2023.09.07`: approved/succeeded, removed exactly this task's newly downloaded, unused image. Filesystem recovered from 100% full to 27 GiB free. Unrelated Docker objects untouched.
- Alternative: anonymously retrieve immutable public image manifest and only hash-verified tool/dependency layers, extract under workspace, run native tools. This is a different install method, no Docker deletion or access-control bypass. `bootstrap_tools.py` reproduces it.
- `pip install llama-cpp-python==0.3.16 --only-binary=:all: --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`: backend index proxy tunnel HTTP 403; no package installed.
- `curl -L --fail https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf`: HTTP 403; no weights downloaded. No restricted retry. TF-IDF remains explicitly a non-LLM control.
