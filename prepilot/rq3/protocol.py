"""Evaluator-side receipt guard. This validates records, not engineering quality."""
import hashlib
import json
from pathlib import Path

QUERIES = {"critical_paths", "complexity", "congestion"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(receipt, state, budget_seconds):
    """Fail closed; callers must construct state from freshly hashed inputs.

    schema: state_id, query, started_s, ended_s, report_path, report_sha256,
    status, cache_hit. started_s/ended_s are monotonic elapsed seconds from
    episode origin, so the latest end includes queue/open/report latency.
    state: state_id, current_state_id, allowed_queries.
    """
    if state["state_id"] != state["current_state_id"]:
        raise ValueError("checkpoint changed; refresh state")
    if receipt["state_id"] != state["state_id"]:
        raise ValueError("stale report")
    if receipt["query"] not in QUERIES & set(state["allowed_queries"]):
        raise ValueError("query not permitted at this stage")
    start, end = receipt["started_s"], receipt["ended_s"]
    if not 0 <= start <= end <= budget_seconds:
        raise ValueError("invalid timing or exhausted episode budget")
    if not isinstance(receipt["cache_hit"], bool):
        raise ValueError("cache status required")
    if receipt["status"] != "ok":
        raise ValueError("failed query: elapsed cost counts, no report delivered")
    if digest(receipt["report_path"]) != receipt["report_sha256"]:
        raise ValueError("report bytes changed")
    return {"deliver": True, "query_wall_s": end - start,
            "remaining_episode_s": budget_seconds - end}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt")
    parser.add_argument("state")
    parser.add_argument("--budget-seconds", required=True, type=float)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(Path(args.receipt).read_text()),
                              json.loads(Path(args.state).read_text()),
                              args.budget_seconds), sort_keys=True))
