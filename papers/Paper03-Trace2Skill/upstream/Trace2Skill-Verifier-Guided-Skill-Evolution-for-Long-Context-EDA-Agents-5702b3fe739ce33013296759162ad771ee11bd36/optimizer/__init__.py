"""Core optimizer machinery: EA loop, fitness evaluation, LLM mutation + crossover.

Benchmark- and method-agnostic. The method variants in `methods/` compose this
machinery with different oracles for feedback extraction.
"""
