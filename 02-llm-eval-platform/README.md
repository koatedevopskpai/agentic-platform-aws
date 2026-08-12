# Scenario 02 — LLM Eval Platform & Observability

## Overview

A production evaluation platform that gives the AgenticOps team confidence to ship LLM changes. This system covers:

- **Golden dataset generation** — synthetic + curated real-world cases
- **LLM-as-judge** — automated scoring with custom rubrics
- **Regression suite** — PR-gated eval runs with baseline comparison
- **Tracing & observability** — LangSmith integration across models
- **Dashboards** — cost, latency, and quality per prompt/model
- **Prompt versioning** — YAML-based config overlays
- **Guardrails** — PII detection, prompt injection, safety filters

## Quick Start

```bash
cd 02-llm-eval-platform
uv sync

# Run the eval suite
AGENTICOPS-eval --dataset golden_v1 --model claude-sonnet-4

# Run guardrails on a sample
AGENTICOPS-guard --text "Customer email with sensitive data"

# View dashboard
AGENTICOPS-dashboard
```

## Architecture

```
Golden Dataset → Eval Runner → LLM-as-Judge → Results Store
      ↑              ↑              ↑
Curated Data    Prompt Registry   LangSmith Trace
      ↑              ↑
Synthetic Gen   Config Overlays
```

## Key Files

| File | Description |
|------|-------------|
| `src/eval_runner.py` | LLM-as-judge eval engine |
| `src/dataset_generator.py` | Synthetic + curated dataset creation |
| `src/regression_suite.py` | PR-gated regression tests |
| `src/tracer.py` | LangSmith tracing integration |
| `src/dashboard.py` | CLI cost/latency/quality dashboards |
| `src/prompt_registry.py` | Prompt versioning & overlay system |
| `src/guardrails.py` | PII, injection, safety guardrails |
| `src/main.py` | CLI entry point |
| `src/tests/test_evals.py` | Eval tests |
| `src/tests/test_guardrails.py` | Guardrail tests |
| `prompts/` | Example prompt templates |

## Deployment

See [deployment.md](deployment.md) for Terraform, AWS CLI, and Console instructions.
