#!/usr/bin/env python3
"""Telemetry and tracing for the CVDP prompt optimizer.

Provides:
  - OpenTelemetry spans for LLM calls (mutation, crossover, analyzer)
  - Per-generation metrics exported to Phoenix (or any OTLP backend)
  - Live dashboard JSON that updates after each generation
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource

_tracer: Optional[trace.Tracer] = None
_provider: Optional[TracerProvider] = None


def init_telemetry(
    service_name: str = "cvdp-prompt-optimizer",
    phoenix_endpoint: Optional[str] = None,
) -> trace.Tracer:
    """Initialize OpenTelemetry with optional Phoenix export.

    Uses SimpleSpanProcessor so spans appear in Phoenix immediately
    when they close, not batched with delay.
    """
    global _tracer, _provider

    resource = Resource.create({"service.name": service_name})
    _provider = TracerProvider(resource=resource)

    if phoenix_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
            _provider.add_span_processor(SimpleSpanProcessor(exporter))
            print(f"  [telemetry] Phoenix exporter → {phoenix_endpoint} (immediate)")
        except Exception as e:
            print(f"  [telemetry] Phoenix export unavailable: {e}")

    trace.set_tracer_provider(_provider)

    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument(tracer_provider=_provider)
        print(f"  [telemetry] OpenAI auto-instrumentation enabled")
    except Exception as e:
        print(f"  [telemetry] OpenAI instrumentation unavailable: {e}")

    _tracer = trace.get_tracer(service_name)
    return _tracer


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        _tracer = init_telemetry()
    return _tracer


def shutdown_telemetry():
    global _provider
    if _provider:
        _provider.shutdown()


def trace_llm_call(operation: str):
    """Decorator to trace an LLM call with OpenTelemetry spans."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(
                f"llm.{operation}",
                attributes={
                    "llm.operation": operation,
                    "llm.model": kwargs.get("model", args[1] if len(args) > 1 else "unknown"),
                },
            ) as span:
                t0 = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("llm.output_length", len(result) if isinstance(result, str) else 0)
                    span.set_attribute("llm.duration_ms", int((time.time() - t0) * 1000))
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator


def trace_fitness_eval(trial_id: str, generation: int, individual_idx: int):
    """Context manager to trace a full fitness evaluation."""
    tracer = get_tracer()
    return tracer.start_as_current_span(
        "fitness.evaluate",
        attributes={
            "ga.trial_id": trial_id,
            "ga.generation": generation,
            "ga.individual_idx": individual_idx,
        },
    )


def trace_generation(generation: int, pop_size: int):
    """Context manager to trace a full generation."""
    tracer = get_tracer()
    return tracer.start_as_current_span(
        "ga.generation",
        attributes={
            "ga.generation": generation,
            "ga.population_size": pop_size,
        },
    )


def record_generation_metrics(
    span,
    generation: int,
    best_fitness: float,
    worst_fitness: float,
    mean_fitness: float,
    best_ever: float,
    population_details: list[dict],
):
    """Record generation-level metrics on a span."""
    span.set_attribute("ga.best_fitness", best_fitness)
    span.set_attribute("ga.worst_fitness", worst_fitness)
    span.set_attribute("ga.mean_fitness", mean_fitness)
    span.set_attribute("ga.best_ever", best_ever)
    span.set_attribute("ga.num_individuals", len(population_details))


class LiveDashboard:
    """Writes a live JSON file that updates after each generation.

    The file can be polled by any frontend (Phoenix, custom HTML, etc.)
    to show real-time optimization progress.
    """

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.data = {
            "status": "initializing",
            "start_time": time.time(),
            "config": {},
            "generations": [],
            "best_ever": {"fitness": 0.0, "generation": 0, "prompt_preview": ""},
        }
        self._write()

    def set_config(self, config: dict):
        self.data["config"] = {
            "population_size": config.get("ga", {}).get("population_size"),
            "generations": config.get("ga", {}).get("generations"),
            "crossover_rate": config.get("ga", {}).get("crossover_rate"),
            "mutation_rate": config.get("ga", {}).get("mutation_rate"),
            "seed_skill": config.get("seed_skill"),
            "dry_run": config.get("fitness", {}).get("dry_run", False),
            "rollout_model": config.get("rollout_model", {}).get("model"),
            "rollout_temperature": config.get("rollout_model", {}).get("temperature", 0.4),
            "mutation_model": config.get("mutation_llm", {}).get("model"),
            "mutation_temperature": config.get("mutation_llm", {}).get("temperature", 0.7),
        }
        self.data["status"] = "running"
        self._write()

    def record_generation(
        self,
        generation: int,
        individuals: list[dict],
        best_fitness: float,
        worst_fitness: float,
        mean_fitness: float,
        best_ever_fitness: float,
        best_ever_generation: int,
        best_prompt_preview: str = "",
        elapsed_secs: float = 0,
    ):
        gen_record = {
            "generation": generation,
            "timestamp": time.time(),
            "elapsed_secs": round(elapsed_secs, 1),
            "best_fitness": round(best_fitness, 4),
            "worst_fitness": round(worst_fitness, 4),
            "mean_fitness": round(mean_fitness, 4),
            "best_ever": round(best_ever_fitness, 4),
            "individuals": [
                {
                    "parent_info": ind.get("parent_info", ""),
                    "fitness": round(ind.get("fitness", 0), 4),
                    "prompt_length": ind.get("prompt_length", 0),
                    "num_rollouts": ind.get("num_rollouts", 0),
                    "has_analyzer_report": ind.get("has_analyzer_report", False),
                }
                for ind in individuals
            ],
        }
        self.data["generations"].append(gen_record)
        self.data["best_ever"] = {
            "fitness": round(best_ever_fitness, 4),
            "generation": best_ever_generation,
            "prompt_preview": best_prompt_preview[:300],
        }
        self.data["status"] = "running"
        self._write()

    def finalize(self, best_fitness: float, best_generation: int):
        self.data["status"] = "complete"
        self.data["end_time"] = time.time()
        self.data["total_elapsed"] = round(
            self.data["end_time"] - self.data["start_time"], 1
        )
        self.data["best_ever"]["fitness"] = round(best_fitness, 4)
        self.data["best_ever"]["generation"] = best_generation
        self._write()

    def _write(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
