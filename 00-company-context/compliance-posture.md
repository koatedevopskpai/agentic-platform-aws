# AgenticOps — Compliance Posture

## Certifications & Frameworks

| Framework | Status | Scope | Last Audit |
|-----------|--------|-------|------------|
| **SOC 2 Type II** | ✅ Certified | Security, Availability, Confidentiality | Feb 2026 |
| **ISO 27001** | ✅ Certified | Information Security Management System | Jan 2026 |
| **GDPR** | ✅ Compliant | Data processing for EU customers | Continuous |
| **CCPA** | ✅ Compliant | California resident data | Continuous |

## Control Mapping

### SOC 2 / ISO 27001 — Common Controls

| Control ID | Area | Implementation at AgenticOps |
|------------|------|------------------------------|
| **CC6.1 / A.9.1.2** | Logical Access | IAM Identity Center + Okta SSO, MFA enforced, JIT production access |
| **CC6.6 / A.12.6.1** | Encryption | KMS-managed keys for all data at rest; TLS 1.3 in transit |
| **CC7.2 / A.16.1.2** | Incident Response | NIST 800-61 aligned runbook; GuardDuty + Security Hub |
| **CC7.3 / A.12.7.1** | Monitoring | CloudWatch metrics + custom dashboards + PagerDuty escalation |
| **CC8.1 / A.14.2.1** | Change Management | CI/CD gated on eval suite pass + security scan + PR approval |
| **A.8.1.1** | Asset Management | Tagging strategy enforced by SCP; all AI resources tagged |
| **A.9.2.3** | Access Review | Quarterly access review with automated certification in Okta |
| **A.11.1.4** | Data Retention | S3 lifecycle policies (7d staging, 90d prod, 1y audit archive) |

### AI-Specific Controls

| Control | Implementation | Evidence |
|---------|---------------|----------|
| **Prompt injection defense** | Input sanitization, output filtering, deny-list guard agent | Guard logs in CloudWatch |
| **PII detection** | Automated guardrail on all LLM inputs/outputs | PII detection score in eval results |
| **Model output audit** | Every LLM invocation logged with session_id, user_id, timestamp | Audit trail in S3 + DynamoDB |
| **Human-in-the-loop** | HITL for any analysis flagged >95% confidence uncertainty | Reviewer assignment in agent workflow |
| **Model governance** | Only approved models via Bedrock + approved direct API endpoints | SCP blocks unapproved model access |
| **Training data controls** | No customer data used for model training; contractual prohibition | Signed DPA with each provider |

## Data Classification

| Class | Definition | Examples | Storage Requirements |
|-------|-----------|----------|---------------------|
| **Public** | Non-sensitive, intended for public | Marketing materials, documentation | S3 public bucket (audited) |
| **Internal** | Business operations data | Internal dashboards, org charts | S3 standard, DynamoDB standard |
| **Confidential** | Customer-facing data | Brand analyses, sentiment reports | S3 SSE-KMS, DynamoDB encryption at rest |
| **Restricted** | Highly sensitive | Customer PII, competitor data, API keys | S3 SSE-KMS with separate CMK, Secrets Manager |

## Data Flow Compliance (GDPR Article 30)

```
Customer Data → Ingestion → (PII Detection → Redaction) → S3 (EU/US Region)
                               ↓
                         Agent Pipeline → Evaluation → S3 Artifacts
                               ↓
                         API Response ← (PII Filter) ←
```

- **Data Processor**: AgenticOps (DPA in place with all customers)
- **Sub-processors**: Anthropic, OpenAI, AWS (all DPA-compliant, SCCs in place)
- **Data retention**: 90 days default, configurable per customer contract
- **Deletion**: Full purge within 30 days of customer request
- **Data export**: Self-service export API for all customer data
