#!/usr/bin/env python3
"""Run the CVDP failure analyzer using a local or remote LLM.

Reads rollout data from convert_rollouts.py output and produces
failure analysis reports, guided by the analyzer_skill.md prompt.

Uses the OpenAI-compatible API directly (works with Ollama, NVIDIA API, etc.)

Usage:
    # Using shared config (recommended):
    python eval/run_analyzer.py \
        --model-summaries eval/outputs/model_summaries.jsonl \
        --config eval/configs/eval_models.yml

    # Using CLI overrides:
    python eval/run_analyzer.py \
        --model-summaries eval/outputs/model_summaries.jsonl \
        --base-url http://localhost:11434/v1 \
        --model nemotron-3-nano:30b
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import openai


def load_skill(repo_root: Path) -> str:
    """Load analyzer skill from the canonical skills/ directory.

    Falls back to the NeMo-Gym-CVDP submodule copy if skills/ is missing
    (e.g. when running inside the submodule as a standalone).
    """
    primary = repo_root / "skills" / "analysis" / "analyzer_skill.md"
    fallback = repo_root / "nemogym" / "analysis" / "analyzer_skill.md"
    for path in (primary, fallback):
        if path.exists():
            return path.read_text(encoding="utf-8")
    print(f"Error: analyzer_skill.md not found at {primary} or {fallback}", file=sys.stderr)
    sys.exit(1)


def build_user_prompt(summary: dict) -> str:
    model_name = summary["model_name"]
    metrics = json.dumps(summary["metrics"], indent=2)
    rollouts = json.dumps(summary["rollouts"], indent=2)
    return f"""Analyze the following NeMo-Gym rollouts and produce a failure analysis report.

Model: {model_name}

Metrics:
{metrics}

Rollout trajectories:
{rollouts}"""


def run_analyzer(
    client: openai.OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8192,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def main():
    parser = argparse.ArgumentParser(description="Run CVDP failure analyzer")
    parser.add_argument("--model-summaries", required=True, help="Path to model_summaries.jsonl")
    parser.add_argument("--output-dir", default="eval/outputs/reports", help="Output directory for reports")
    parser.add_argument("--config", default=None, help="Path to eval_models.yml (shared config)")
    parser.add_argument("--base-url", default=None, help="LLM API base URL (overrides config)")
    parser.add_argument("--model", default=None, help="Model name (overrides config)")
    parser.add_argument("--api-key", default=None, help="API key (overrides config)")
    parser.add_argument("--max-tokens", type=int, default=None, help="Max output tokens (overrides config)")
    args = parser.parse_args()

    # Load config: shared YAML -> CLI overrides -> env var defaults
    base_url = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    model = os.environ.get("ANALYZER_MODEL", "nemotron-3-nano:30b")
    api_key = os.environ.get("LLM_API_KEY", "ollama")
    max_tokens = 8192

    if args.config:
        from eval_config import get_analyzer_config
        cfg = get_analyzer_config(args.config)
        base_url = cfg.get("base_url", base_url)
        model = cfg.get("model", model)
        api_key = cfg.get("api_key", api_key)
        max_tokens = cfg.get("max_tokens", max_tokens)

    if args.base_url:
        base_url = args.base_url
    if args.model:
        model = args.model
    if args.api_key:
        api_key = args.api_key
    if args.max_tokens is not None:
        max_tokens = args.max_tokens

    repo_root = Path(__file__).resolve().parent.parent
    skill_text = load_skill(repo_root)
    print(f"Loaded analyzer skill ({len(skill_text)} chars)")
    print(f"Model: {model}")
    print(f"Endpoint: {base_url}")

    summaries_path = Path(args.model_summaries)
    if not summaries_path.exists():
        print(f"Error: {summaries_path} not found", file=sys.stderr)
        sys.exit(1)

    summaries = []
    with open(summaries_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                summaries.append(json.loads(line))

    print(f"Loaded {len(summaries)} model summaries")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = openai.OpenAI(base_url=base_url, api_key=api_key)

    for summary in summaries:
        model_name = summary["model_name"]
        print(f"\n{'='*60}")
        print(f"  Analyzing: {model_name}")
        print(f"{'='*60}")

        user_prompt = build_user_prompt(summary)
        print(f"  Prompt size: {len(skill_text) + len(user_prompt)} chars")

        t0 = time.time()
        try:
            report = run_analyzer(client, model, skill_text, user_prompt, max_tokens)
        except Exception as e:
            print(f"  Error: {e}")
            report = f"# Analysis failed for {model_name}\n\nError: {e}\n"

        elapsed = time.time() - t0
        print(f"  Generated {len(report)} chars in {elapsed:.1f}s")

        report_path = output_dir / f"report_{model_name}.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"  Saved to {report_path}")

    print(f"\nAll reports saved to {output_dir}/")


if __name__ == "__main__":
    main()
