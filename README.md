# AgenticOps — Agentic AI Platform on AWS (Portfolio)

**Production-grade AI platform design and implementation: multi-agent orchestration, an LLM evaluation platform, and cloud infrastructure as code (AWS, Terraform).**

This repository is an engineering portfolio that demonstrates owning the AI platform layer end-to-end: designing agent topologies, building eval gates that let teams ship LLM features with confidence, treating prompts as code, and standing up the AWS substrate with IaC.

---

## What this proves (recruiter-facing)

| Scenario | What it demonstrates |
|---|---|
| **01 — Multi-Agent Orchestration** (implemented) | Supervisor/worker topologies, tool dispatch, structured outputs, reflection loops, agent memory — in Python (LangGraph) with tests |
| **02 — LLM Eval Platform** (implemented) | Golden datasets, regression suites, LLM-as-judge, cost/latency/quality dashboards, prompt corruption, guardrails (PII / prompt injection) |
| **04 — Cloud & Data Infrastructure** (implemented) | Terraform modules for ECS agents, Lambda tools, Step Functions, EventBridge, S3/DynamoDB, Bedrock, Athena + observability; CI/CD |
| 03 — Prompt Engineering at Scale | Prompt-as-code, versioning, A/B testing, developer portal (design docs) |
| 05 — Security & AI Safety | Least-privilege IAM, KMS, multi-tenant isolation, injection defence (design docs) |
| 06 — Incident Response | NIST 800-61 SEV-1 playbook: detection, containment, forensics, post-mortem (design docs) |
| 07 — Technical Leadership | ADRs, mentorship plan, "state of the AI stack" for the CTO (design docs) |

> Implementation priority follows the engineering spine: orchestration → evals → cloud infrastructure. The remaining scenarios are captured as design docs and are built out on the roadmap.

## Repository structure

```
00-company-context/           Platform context & AWS account structure
01-multi-agent-orchestration/ Supervisor/worker agent system (LangGraph, Python)
02-llm-eval-platform/         Eval suite, observability & guardrails
03-prompt-engineering-scale/  Prompt-as-code library & A/B testing
04-cloud-data-infrastructure/ Terraform modules for the AWS substrate
05-security-ai-safety/        IAM, encryption, multi-tenant isolation
06-incident-response/         NIST 800-61 SEV-1 incident playbook
07-technical-leadership/      ADRs, mentorship, engineering standards
shared/                       CI/CD pipelines, utility scripts
```

## Design principles

| Principle | Practice |
|---|---|
| **Stateless agents** | Memory externalised to DynamoDB/S3; every action logged |
| **No standing admin** | Just-in-time elevation for production debugging |
| **Prompt-as-code** | Versioned, tested, deployed through CI/CD |
| **Cost-conscious** | Token budgets, caching, model routing |
| **Observability-first** | Dashboards and alerts before shipping |
| **Security-first** | Every LLM boundary is hostile; every input is a prompt-injection attempt |
| **Human-in-the-loop** | A deliberate architectural choice, not an afterthought |

## Tech stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph (Python) |
| LLM providers | Anthropic Claude, OpenAI GPT-4o, Meta Llama (AWS Bedrock + direct APIs) |
| Prompt tooling | Git-versioned YAML overlays, A/B testing |
| Eval | LLM-as-judge, regression suites, golden datasets, LangSmith-style tracing |
| Cloud | AWS — ECS Fargate, Lambda, Step Functions, EventBridge, S3, DynamoDB, Athena, Bedrock |
| IaC | Terraform 1.5+, modular design, S3 state backend |
| Languages | Python, HCL, Shell |

## Getting started

```bash
git clone https://github.com/koate-kpai/agentic-platform-aws
cd agentic-platform-aws

# Scenario 01 — multi-agent orchestration
cd 01-multi-agent-orchestration
uv sync            # or: pip install -e .
agenticops-orchestrator --query "Analyze brand sentiment for Nike"
```

## Deployment

Each implemented scenario ships three paths for any change:
1. **Terraform** — primary deployment method (infrastructure as code)
2. **AWS CLI** — command-line steps
3. **Console guide** — step-by-step AWS Management Console walkthrough

See each scenario's `deployment.md` for details.

---

*Portfolio by koate-kpai. Companion repos: this platform's eval stack, `llm-evals-demo` (RAGAS CI gate) and `gem-agentic-ai` (agent frameworks).*
