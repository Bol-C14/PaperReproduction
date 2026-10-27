# CVDP Agentic Heavy Benchmark

Multi-turn agentic evaluation for complex hardware design tasks. Models interact
with a sandbox environment via visible-context tool calls (`ls`, `cat`, `rg`,
`find_files`, `read_file`, `show_changes`, `module_index`, `echo`, `edit`,
`restore_file`, `iverilog`, `vvp`, `pwd`) to debug and fix RTL code across
real-world designs. Verification is done by running per-task cocotb test
harnesses inside Docker after the rollout ends.

## Verification Flow

1. `seed_session()` — write context files to a per-session sandbox directory
2. Multi-turn tool loop — model issues tool calls, resource server executes them
   in the sandbox and returns results
3. `verify()` — run the Docker harness (cocotb + pytest) against the agent's
   modified sandbox. Exit code 0 across all services → reward 1.0; any failure → reward 0.0

The hidden verifier harness is stored under `verifier_metadata.harness_files`
and is mounted only by `verify()`. It is not exposed through `context_files` or
as a rollout tool.

## Dataset Creation

### Step 1 — Convert agentic heavy compiled data to NeMo-Gym format

This resolves context URLs (repo + commit) into inlined file contents and
restructures fields into the gym schema.

```bash
python resources_servers/cvdp_agentic_heavy/scripts/convert_to_gym.py \
    --input  /path/to/20250801_agentic_heavy_compiled_all_categories.json \
    --output resources_servers/cvdp_agentic_heavy/data/gym_cvdp_agentic_heavy.jsonl \
    --repos-cache /tmp/cvdp_repos_cache
```

Requires git access to the `turing-genai-hw` GitHub org repos.

Use `--skip-resolve` to test schema conversion without cloning repos.

### Gym JSONL Schema

```json
{
  "responses_create_params": {
    "input": [
      {"role": "developer", "content": "<agent system prompt with tool descriptions>"},
      {"role": "user", "content": "<task description>"}
    ],
    "tools": [
      {"type": "function", "name": "ls", ...},
      {"type": "function", "name": "cat", ...},
      {"type": "function", "name": "rg", ...},
      {"type": "function", "name": "find_files", ...},
      {"type": "function", "name": "read_file", ...},
      {"type": "function", "name": "show_changes", ...},
      {"type": "function", "name": "module_index", ...},
      {"type": "function", "name": "echo", ...},
      {"type": "function", "name": "edit", ...},
      {"type": "function", "name": "restore_file", ...},
      {"type": "function", "name": "iverilog", ...},
      {"type": "function", "name": "vvp", ...},
      {"type": "function", "name": "pwd", ...}
    ]
  },
  "verifier_metadata": {
    "task_id": "cvdp_agentic_heavy_Edf_Switch_0001",
    "categories": ["cid016", "hard"],
    "difficulty": "hard",
    "context_files": {"path/to/file.v": "...actual content..."},
    "harness_files": {"docker-compose.yml": "...", "src/.env": "...", ...},
    "patch": {"path/to/file.v": "@@ unified diff ..."},
    "origin": {"repo": "...", "commit": "..."}
  }
}
```

## Configuration

| Field | Default | Description |
|---|---|---|
| `oss_sim_image` | `ghcr.io/hdl/sim/osvb` | Docker image for open-source simulation |
| `eda_sim_image` | `""` | Commercial EDA image (Cadence Xcelium) |
| `docker_timeout` | `600` | Seconds before a Docker run is killed |
| `num_processes` | `4` | Max concurrent Docker jobs |

## Tool Boundary

The diagnostic tools are intentionally low-risk:

- `rg`, `find_files`, `read_file`, and `module_index` only read files already
  mounted into the visible `/code` sandbox.
- `show_changes` compares the current sandbox against the original visible
  context captured at `seed_session()`.
- None of these tools can call the final verifier or read hidden harness files.
