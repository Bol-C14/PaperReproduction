# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Agent for CVDP agentic heavy tasks.
# Implements a multi-turn tool-use loop: the model generates tool calls (ls, cat,
# echo, edit, iverilog, vvp, pwd), the resource server executes them in a sandbox, and
# the results are fed back until the model produces a final response or hits the
# step limit.

import asyncio
import base64
import json
import traceback
from typing import List, Optional

from fastapi import Request, Response
from pydantic import ConfigDict, ValidationError

from nemo_gym.base_resources_server import (
    BaseRunRequest,
    BaseVerifyRequest,
    BaseVerifyResponse,
)
from nemo_gym.base_responses_api_agent import (
    BaseResponsesAPIAgentConfig,
    Body,
    SimpleResponsesAPIAgent,
)
from nemo_gym.config_types import ModelServerRef, ResourcesServerRef
from nemo_gym.openai_utils import (
    NeMoGymEasyInputMessage,
    NeMoGymFunctionCallOutput,
    NeMoGymResponse,
    NeMoGymResponseCreateParamsNonStreaming,
    NeMoGymResponseFunctionToolCall,
    NeMoGymResponseOutputMessage,
)
from nemo_gym.server_utils import get_response_json, raise_for_status

import time

try:
    from responses_api_agents.cvdp_agentic_heavy_agent.skill_monitor import (
        MONITOR_METADATA_KEY,
        SkillContractMonitor,
        strip_monitor_metadata,
    )
except ImportError:  # pragma: no cover - app.py is also executed from its own directory
    from skill_monitor import MONITOR_METADATA_KEY, SkillContractMonitor, strip_monitor_metadata


# Fields allowed in each output item type when passed back as input.
# Any extra fields (e.g. Sonnet's "caller", "index") are stripped to
# prevent Pydantic validation failures on the model server.
_ALLOWED_FIELDS = {
    "function_call": {"type", "name", "arguments", "call_id", "id", "status"},
    "function_call_output": {"type", "call_id", "output", "id", "status"},
    "message": {"type", "role", "content", "id", "status"},
    "reasoning": {"type", "id", "summary"},
}

# The /run endpoint seeds a resource-server session, then calls this same agent
# through /v1/responses. In long parallel runs we have seen that relying only on
# nested HTTP cookie propagation can occasionally lose the resource session
# cookie, causing every subsequent tool call to fail with "No session found".
# Carrying the resource cookies through a private internal header keeps the
# sandbox session attached to the rollout without exposing it to the model.
_RESOURCE_COOKIE_HEADER = "x-cvdp-resource-cookies-b64"


def _sanitize_output_items(items: list) -> list:
    """Strip unknown fields from model output items for cross-model compatibility.

    Different LLM providers return different extra fields in Responses API output:
      - Sonnet 4.6 adds: caller, index, status on function_call items
      - GPT-5 may add: annotations, metadata
      - Haiku 4.5 returns only base fields (no stripping needed)

    By keeping only the fields each item type is known to need, we ensure the
    items can be fed back as input to any model server without validation errors.
    """
    sanitized = []
    for item in items:
        if hasattr(item, "model_dump"):
            d = item.model_dump(exclude_unset=True)
        elif isinstance(item, dict):
            d = dict(item)
        else:
            sanitized.append(item)
            continue

        item_type = d.get("type", "")
        allowed = _ALLOWED_FIELDS.get(item_type)
        if allowed:
            cleaned = {k: v for k, v in d.items() if k in allowed}
            # Recursively clean nested content (messages have content lists)
            if "content" in cleaned and isinstance(cleaned["content"], list):
                cleaned_content = []
                for c in cleaned["content"]:
                    if isinstance(c, dict):
                        # Keep only known content fields, strip annotations if empty
                        cc = {k: v for k, v in c.items()
                              if k in {"type", "text", "annotations", "refusal"}}
                        cleaned_content.append(cc)
                    else:
                        cleaned_content.append(c)
                cleaned["content"] = cleaned_content
            sanitized.append(cleaned)
        else:
            sanitized.append(d)

    return sanitized


def _merge_cookies(target: dict, source) -> None:
    """Merge cookies from an aiohttp response into a plain {str: str} dict.

    aiohttp's response.cookies is a SimpleCookie whose values are Morsel
    objects.  Storing Morsels in the dict corrupts downstream cookie
    headers — only the plain string value should be kept.
    """
    if not source:
        return
    from http.cookies import Morsel
    for key, val in source.items():
        target[key] = val.value if isinstance(val, Morsel) else str(val)


def _encode_resource_cookies(cookies: dict) -> str:
    payload = json.dumps(cookies, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _decode_resource_cookies(request: Request) -> dict[str, str]:
    raw = request.headers.get(_RESOURCE_COOKIE_HEADER)
    if not raw:
        return {}
    try:
        payload = base64.urlsafe_b64decode(raw.encode("ascii"))
        decoded = json.loads(payload.decode("utf-8"))
    except Exception as e:
        print(f"[responses] failed to decode resource cookie header: {e}")
        return {}
    if not isinstance(decoded, dict):
        return {}
    return {str(k): str(v) for k, v in decoded.items()}


def _is_missing_resource_session(text: str) -> bool:
    lowered = text.lower()
    return "no session found" in lowered and "seed_session" in lowered


def _output_item_type(item) -> str | None:
    return getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)


def _output_item_name(item) -> str | None:
    return getattr(item, "name", None) or (item.get("name") if isinstance(item, dict) else None)


def _function_call_names(items: list) -> list[str]:
    return [
        name for item in items
        if _output_item_type(item) == "function_call"
        for name in [_output_item_name(item)]
        if name
    ]


def _make_error_response(error_id: str) -> NeMoGymResponse:
    """Construct a minimal valid NeMoGymResponse for error paths."""
    return NeMoGymResponse(
        id=error_id,
        created_at=time.time(),
        model="error",
        object="response",
        output=[],
        parallel_tool_calls=False,
        tool_choice="auto",
        tools=[],
    )


class CVDPAgenticHeavyAgentConfig(BaseResponsesAPIAgentConfig):
    resources_server: ResourcesServerRef
    model_server: ModelServerRef
    max_steps: int = 20
    context_limit_tokens: int = 120000
    max_tool_output_chars: int = 30_000
    model_call_timeout: int = 300
    tool_call_timeout: int = 180


def _attach_skill_monitor_summary(response: NeMoGymResponse, monitor: SkillContractMonitor) -> NeMoGymResponse:
    if not monitor.enabled:
        return response
    metadata = {}
    existing = getattr(response, "metadata", None)
    if existing:
        try:
            metadata = dict(existing)
        except (TypeError, ValueError):
            metadata = {}
    metadata[MONITOR_METADATA_KEY] = json.dumps(monitor.summary(), ensure_ascii=False)
    return response.model_copy(update={"metadata": metadata})


def _attach_runtime_verifier_feedback_summary(response: NeMoGymResponse) -> NeMoGymResponse:
    """Summarize runtime verifier feedback tool calls in response metadata.

    The raw hidden-verifier logs stay server-side. The rollout artifact already
    contains sanitized tool outputs; this metadata makes downstream metrics easy
    to compute without reparsing the whole conversation every time.
    """
    call_names: dict[str, str] = {}
    calls = 0
    policy_violations = 0
    partial_scores: list[float] = []
    pass_before_final = False
    for item in getattr(response, "output", []) or []:
        item_type = _output_item_type(item)
        if item_type == "function_call":
            call_id = getattr(item, "call_id", None) or (item.get("call_id") if isinstance(item, dict) else None)
            name = _output_item_name(item)
            if call_id and name:
                call_names[str(call_id)] = str(name)
            continue
        if item_type != "function_call_output":
            continue
        call_id = getattr(item, "call_id", None) or (item.get("call_id") if isinstance(item, dict) else None)
        if call_names.get(str(call_id)) != "verify_feedback":
            continue
        output_text = getattr(item, "output", "") or (item.get("output", "") if isinstance(item, dict) else "")
        try:
            payload = json.loads(output_text)
        except Exception:
            payload = {}
        if isinstance(payload, dict) and "output" in payload and isinstance(payload["output"], str):
            try:
                payload = json.loads(payload["output"])
            except Exception:
                payload = {}
        if not isinstance(payload, dict):
            continue
        if "error" in payload:
            policy_violations += 1
            continue
        feedback = payload.get("verifier_feedback")
        if not isinstance(feedback, dict):
            continue
        calls += 1
        try:
            partial_scores.append(float(feedback.get("partial_score", 0.0) or 0.0))
        except (TypeError, ValueError):
            pass
        pass_before_final = pass_before_final or bool(feedback.get("pass"))

    if calls == 0 and policy_violations == 0:
        return response

    metadata = {}
    existing = getattr(response, "metadata", None)
    if existing:
        try:
            metadata = dict(existing)
        except (TypeError, ValueError):
            metadata = {}
    metadata["runtime_verifier_feedback"] = json.dumps({
        "calls": calls,
        "policy_violations": policy_violations,
        "partial_scores": [round(v, 4) for v in partial_scores],
        "mean_partial_score": round(sum(partial_scores) / len(partial_scores), 4) if partial_scores else 0.0,
        "pass_before_final": pass_before_final,
    }, ensure_ascii=False)
    return response.model_copy(update={"metadata": metadata})


class AgenticHeavyRunRequest(BaseRunRequest):
    model_config = ConfigDict(extra="allow")


class AgenticHeavyVerifyRequest(BaseVerifyRequest):
    model_config = ConfigDict(extra="allow")


class AgenticHeavyVerifyResponse(BaseVerifyResponse):
    model_config = ConfigDict(extra="allow")


def _estimate_tokens(items) -> int:
    """Rough token estimate: ~4 chars per token."""
    total = 0
    for item in items:
        try:
            if hasattr(item, "model_dump"):
                total += len(json.dumps(item.model_dump(exclude_unset=True)))
            elif isinstance(item, dict):
                total += len(json.dumps(item))
            else:
                total += len(str(item))
        except (TypeError, ValueError):
            total += 100
    return total // 4


def _compress_outputs(outputs: list, keep_recent: int = 6, aggressive: bool = False) -> list:
    """Compress older tool outputs to save context, keeping recent turns intact.

    When aggressive=True (context still over limit after normal compression),
    drops all old function_call_output items entirely and keeps only the
    function_call name/arguments as a one-line summary.
    """
    if len(outputs) <= keep_recent:
        return outputs

    recent = outputs[-keep_recent:]
    older = outputs[:-keep_recent]
    compressed = []

    for item in older:
        item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)

        if item_type == "function_call_output":
            if aggressive:
                short = "[output dropped to save context]"
            else:
                output_text = getattr(item, "output", None) or (item.get("output", "") if isinstance(item, dict) else "")
                if len(output_text) > 500:
                    short = output_text[:200] + f"\n... [compressed: {len(output_text)} chars total]"
                else:
                    short = output_text
            if hasattr(item, "model_copy"):
                item = item.model_copy(update={"output": short})
            elif isinstance(item, dict):
                item = {**item, "output": short}
            compressed.append(item)
        elif item_type == "reasoning":
            continue
        else:
            compressed.append(item)

    return compressed + recent


def _truncate_tool_output(text: str, max_chars: int) -> str:
    """Truncate tool output to prevent a single large response from blowing up context."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n\n... [truncated: {len(text)} chars total, showing first and last {half} chars] ...\n\n" + text[-half:]


class CVDPAgenticHeavyAgent(SimpleResponsesAPIAgent):
    config: CVDPAgenticHeavyAgentConfig

    async def responses(
        self,
        request: Request,
        response: Response,
        body: NeMoGymResponseCreateParamsNonStreaming = Body(),
    ) -> NeMoGymResponse:
        """Multi-turn tool-use loop."""
        body = body.model_copy(deep=True)

        if isinstance(body.input, str):
            body.input = [NeMoGymEasyInputMessage(role="user", content=body.input)]

        new_outputs: list = []
        usage = None
        model_server_cookies: dict = {}
        resources_server_cookies = dict(request.cookies)
        resources_server_cookies.update(_decode_resource_cookies(request))
        last_valid_response: Optional[NeMoGymResponse] = None
        skill_monitor = SkillContractMonitor.from_response_body(body)
        session_lost = False

        for step in range(1, self.config.max_steps + 1):
            context_for_model = new_outputs
            estimated = _estimate_tokens(body.input) + _estimate_tokens(context_for_model)
            threshold = int(self.config.context_limit_tokens * 0.8)
            hard_limit = self.config.context_limit_tokens

            if estimated > threshold:
                context_for_model = _compress_outputs(new_outputs, keep_recent=6)
                compressed_est = _estimate_tokens(body.input) + _estimate_tokens(context_for_model)
                print(f"[step {step}] Context compressed: {estimated} -> {compressed_est} tokens (threshold={threshold})")

                if compressed_est > hard_limit:
                    context_for_model = _compress_outputs(new_outputs, keep_recent=4, aggressive=True)
                    aggressive_est = _estimate_tokens(body.input) + _estimate_tokens(context_for_model)
                    print(f"[step {step}] Aggressive compression: {compressed_est} -> {aggressive_est} tokens (hard_limit={hard_limit})")

                    if aggressive_est > hard_limit:
                        print(f"[step {step}] Context still exceeds hard limit after aggressive compression. Stopping loop.")
                        break

            new_body = body.model_copy(update={"input": body.input + context_for_model})
            if skill_monitor.enabled:
                new_body = new_body.model_copy(
                    update={"metadata": strip_monitor_metadata(getattr(new_body, "metadata", None))}
                )

            try:
                model_response_raw = await asyncio.wait_for(
                    self.server_client.post(
                        server_name=self.config.model_server.name,
                        url_path="/v1/responses",
                        json=new_body,
                        cookies=model_server_cookies,
                    ),
                    timeout=self.config.model_call_timeout,
                )
            except asyncio.TimeoutError:
                print(f"[step {step}] Model call timed out after {self.config.model_call_timeout}s")
                break
            except Exception as e:
                print(f"[step {step}] Model server connection error: {e}")
                break

            if model_response_raw.status >= 400:
                error_body = (await model_response_raw.content.read()).decode(errors="replace")[:1000]
                print(f"[step {step}] Model server returned HTTP {model_response_raw.status}: {error_body}")
                if model_response_raw.status == 400 and "context" in error_body.lower():
                    print(f"[step {step}] Context length exceeded — stopping loop.")
                break

            model_response_json = await get_response_json(model_response_raw)
            _merge_cookies(model_server_cookies, model_response_raw.cookies)

            try:
                model_response = NeMoGymResponse.model_validate(model_response_json)
            except ValidationError as e:
                print(f"[step {step}] Invalid model response: {e}")
                break

            last_valid_response = model_response
            output = model_response.output
            new_outputs.extend(_sanitize_output_items(output))

            if not usage:
                usage = model_response.usage
            elif model_response.usage:
                usage.input_tokens += model_response.usage.input_tokens
                usage.output_tokens += model_response.usage.output_tokens
                usage.total_tokens += model_response.usage.total_tokens

            if model_response.incomplete_details and model_response.incomplete_details.reason == "max_output_tokens":
                break

            all_fn_calls: List[NeMoGymResponseFunctionToolCall] = [
                o for o in output if o.type == "function_call"
            ]
            all_output_messages: List[NeMoGymResponseOutputMessage] = [
                o for o in output if o.type == "message" and o.role == "assistant"
            ]

            if not all_fn_calls and all_output_messages:
                tool_names_so_far = _function_call_names(new_outputs)
                has_written = "echo" in tool_names_so_far or "edit" in tool_names_so_far
                has_compiled = "iverilog" in tool_names_so_far
                has_run_sim = "vvp" in tool_names_so_far
                completed_cycle = has_written and has_compiled and has_run_sim
                near_end = step >= self.config.max_steps * 3 // 4
                if completed_cycle or near_end:
                    break

            for fn_call in all_fn_calls:
                try:
                    tool_args = json.loads(fn_call.arguments)
                except (json.JSONDecodeError, TypeError) as e:
                    output_text = f"Error: malformed tool arguments: {e}"
                    new_outputs.append(NeMoGymFunctionCallOutput(
                        type="function_call_output",
                        call_id=fn_call.call_id,
                        output=output_text,
                    ))
                    continue

                pre_decision = skill_monitor.before_tool(step, fn_call.name, tool_args)
                if pre_decision.should_block:
                    new_outputs.append(NeMoGymFunctionCallOutput(
                        type="function_call_output",
                        call_id=fn_call.call_id,
                        output=pre_decision.feedback_text(),
                    ))
                    continue

                try:
                    api_response = await asyncio.wait_for(
                        self.server_client.post(
                            server_name=self.config.resources_server.name,
                            url_path=f"/{fn_call.name}",
                            json=tool_args,
                            cookies=resources_server_cookies,
                        ),
                        timeout=self.config.tool_call_timeout,
                    )
                    _merge_cookies(resources_server_cookies, api_response.cookies)

                    if api_response.status >= 400:
                        error_body = (await api_response.content.read()).decode(errors="replace")
                        output_text = f"Error: tool '{fn_call.name}' returned HTTP {api_response.status}: {error_body[:500]}"
                        if _is_missing_resource_session(error_body):
                            session_lost = True
                            print(
                                f"[step {step}] Resource session disappeared during tool '{fn_call.name}'. "
                                "Stopping rollout early instead of looping on invalid tool calls."
                            )
                    else:
                        raw_output = (await api_response.content.read()).decode(errors="replace")
                        output_text = _truncate_tool_output(raw_output, self.config.max_tool_output_chars)
                except asyncio.TimeoutError:
                    output_text = f"Error: tool '{fn_call.name}' timed out after {self.config.tool_call_timeout}s"
                except Exception as e:
                    output_text = f"Error: tool '{fn_call.name}' failed: {e}"

                post_decision = skill_monitor.after_tool(step, fn_call.name, tool_args, output_text)
                monitor_feedback = "\n\n".join(
                    text for text in (
                        skill_monitor.feedback_for(pre_decision),
                        skill_monitor.feedback_for(post_decision),
                    )
                    if text
                )
                if monitor_feedback:
                    output_text = f"{monitor_feedback}\n\n{output_text}"

                tool_response = NeMoGymFunctionCallOutput(
                    type="function_call_output",
                    call_id=fn_call.call_id,
                    output=output_text,
                )
                new_outputs.append(tool_response)

                if session_lost:
                    break

            if session_lost:
                break

        if last_valid_response is None:
            last_valid_response = _make_error_response("error-no-valid-response")
            last_valid_response.output = new_outputs
            last_valid_response.usage = usage

        all_cookies = list(resources_server_cookies.items())
        if model_server_cookies:
            all_cookies.extend(model_server_cookies.items())
        for k, v in all_cookies:
            response.set_cookie(k, v)

        last_valid_response.output = new_outputs
        last_valid_response.usage = usage
        last_valid_response = _attach_skill_monitor_summary(last_valid_response, skill_monitor)
        last_valid_response = _attach_runtime_verifier_feedback_summary(last_valid_response)
        return last_valid_response

    async def run(self, request: Request, body: AgenticHeavyRunRequest) -> AgenticHeavyVerifyResponse:
        """Full episode: seed session → multi-turn tool loop → verify.

        Any failure in the tool loop is caught and treated as reward=0.0
        so a single bad rollout doesn't crash the entire evaluation run.
        """
        cookies = dict(request.cookies)

        try:
            seed_response = await self.server_client.post(
                server_name=self.config.resources_server.name,
                url_path="/seed_session",
                json=body.model_dump(),
                cookies=cookies,
            )
            await raise_for_status(seed_response)
            _merge_cookies(cookies, seed_response.cookies)
        except Exception as e:
            print(f"[run] seed_session failed: {e}\n{traceback.format_exc()}")
            return AgenticHeavyVerifyResponse(
                **body.model_dump(),
                response=_make_error_response("error-seed-session"),
                reward=0.0,
            )

        try:
            response = await self.server_client.post(
                server_name=self.config.name,
                url_path="/v1/responses",
                json=body.responses_create_params,
                cookies=cookies,
                headers={_RESOURCE_COOKIE_HEADER: _encode_resource_cookies(cookies)},
            )
            await raise_for_status(response)
            _merge_cookies(cookies, response.cookies)
        except Exception as e:
            print(f"[run] responses (tool loop) failed: {e}\n{traceback.format_exc()}")
            try:
                error_response = _make_error_response("error-tool-loop-verify")
                verify_request = AgenticHeavyVerifyRequest.model_validate(
                    body.model_dump() | {"response": error_response.model_dump()}
                )
                verify_response = await self.server_client.post(
                    server_name=self.config.resources_server.name,
                    url_path="/verify",
                    json=verify_request.model_dump(),
                    cookies=cookies,
                )
                return AgenticHeavyVerifyResponse.model_validate(await get_response_json(verify_response))
            except Exception:
                pass
            return AgenticHeavyVerifyResponse(
                **body.model_dump(),
                response=_make_error_response("error-tool-loop"),
                reward=0.0,
            )

        try:
            verify_request = AgenticHeavyVerifyRequest.model_validate(
                body.model_dump() | {"response": await get_response_json(response)}
            )
            verify_response = await self.server_client.post(
                server_name=self.config.resources_server.name,
                url_path="/verify",
                json=verify_request.model_dump(),
                cookies=cookies,
            )
            await raise_for_status(verify_response)
            return AgenticHeavyVerifyResponse.model_validate(await get_response_json(verify_response))
        except Exception as e:
            print(f"[run] verify failed: {e}\n{traceback.format_exc()}")
            return AgenticHeavyVerifyResponse(
                **body.model_dump(),
                response=_make_error_response("error-verify"),
                reward=0.0,
            )


if __name__ == "__main__":
    CVDPAgenticHeavyAgent.run_webserver()
