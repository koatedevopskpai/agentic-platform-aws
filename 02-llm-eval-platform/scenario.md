# Scenario 02 — LLM Eval Platform & Observability

## Business Context

AgenticOps ships prompt and model changes weekly. Without rigorous evaluation, every deploy risks regressions in response quality, increased latency, or higher costs. The team needs:

1. **A golden dataset** of curated queries and expected outputs to measure against
2. **Automated eval** that runs on every PR and blocks regressions
3. **Observability** to trace issues back to specific prompts, models, and invocations
4. **Cost visibility** to prevent bill shock from LLM API usage

## User Stories

| ID | User Story | Acceptance Criteria |
|----|-----------|-------------------|
| US-001 | As an AI engineer, I want to add a new eval test without writing code | YAML-based test definitions; no Python changes |
| US-002 | As a PM, I want to see if a prompt change improved quality before deploy | A/B test report with win/loss analysis |
| US-003 | As a security engineer, I want PII filtered from all LLM calls | Guardrail blocks PII with >99% precision |
| US-004 | As an engineering manager, I want cost forecasts per model | Dashboard shows projected monthly cost |
| US-005 | As a CTO, I want to trace a bad response back to the exact prompt version | Every response tagged with prompt_hash, model, timestamp |

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Eval coverage | >90% of prompt templates have tests | Test count vs prompt count |
| Regression detection | >95% of quality regressions caught | Manual review of 50 changes |
| PII detection precision | >99% | Confusion matrix on test set |
| Prompt injection detection | >95% | Test suite of known attacks |
| Eval run time | <10min for full suite | CloudWatch timing |
| Dashboard latency | <5s refresh | Manual measurement |
