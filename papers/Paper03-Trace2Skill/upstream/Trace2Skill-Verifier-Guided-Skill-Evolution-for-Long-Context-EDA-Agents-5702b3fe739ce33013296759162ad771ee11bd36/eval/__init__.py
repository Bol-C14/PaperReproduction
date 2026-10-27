"""BLADE-style evaluation pipeline: rollout conversion, LLM analyzer, LLM-as-judge.

The analyzer produces structured behavioral failure reports (pipeline funnel,
B1-B7 patterns, KG/UK/BI/EI root cause classification). The judge scores these
reports against a rubric for quality assurance.
"""
