# Scenario 02 — Architecture Decision Records

## ADR-001: LLM-as-Judge vs Automated Metrics

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Choosing evaluation methodology for prompt and model quality |
| **Options** | LLM-as-Judge, BLEU/ROUGE, BERTScore, Human evaluation |

**LLM-as-Judge** selected because:
- Brand analysis quality is subjective and context-dependent
- BLEU/ROUGE unsuitable for creative/analytical outputs
- LLM judges can evaluate nuanced criteria (tone, completeness, reasoning)
- Claude Opus as judge provides consistent, calibrated scoring
- Cost is acceptable at ~$0.015/eval for production confidence

## ADR-002: LangSmith vs Self-Hosted Tracing

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Observability platform for LLM invocations |
| **Options** | LangSmith, MLflow, Weights & Biases, Custom (CloudWatch + S3) |

**LangSmith** selected because:
- Native LangGraph/LangChain integration — zero-instrumentation traces
- Built-in comparison views for A/B testing
- Dataset management features align with golden dataset workflow
- Automated feedback collection via annotation queues
- Cost justified for <$500/mo at AgenticOps's scale

## ADR-003: Synthetic + Curated Dataset Strategy

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Generating and maintaining the golden evaluation dataset |
| **Decision** | 60% synthetic (LLM-generated variations), 30% curated from production, 10% edge cases |
| **Rationale** | Synthetic provides breadth; curated provides real-world relevance; edge cases catch regressions production data would miss |
| **Refresh cadence** | Synthetic: weekly; Curated: monthly; Edge cases: continuous |

## ADR-004: Prompt-as-Code Approach

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | How to manage, version, and deploy prompt templates |
| **Decision** | YAML-based prompt registry in Git, versioned alongside code, deployed via CI/CD |
| **Rationale** | Prompts are code — they need version control, code review, testing, and rollback. YAML provides readability for PMs and non-engineering stakeholders. Overlay system allows per-environment configuration without branch switching |

## ADR-005: Guardrail Architecture

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Defending LLM pipeline against PII leakage, prompt injection, and unsafe content |
| **Decision** | Three-layer guard: Input guard (pre-generation), Output guard (post-generation), Monitoring (async analysis) |
| **Rationale** | Defense-in-depth. Input guard prevents bad data reaching the model; output guard catches model errors; monitoring provides audit trail for post-hoc analysis |
