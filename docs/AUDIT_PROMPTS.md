# Audit Prompts Configuration
*Project-specific audit rules loaded by the audit pipeline.*
*Edit this file to add rules specific to your project's domain.*

---

## Global rules (all agents)

These rules apply to all three audit agents in addition to their standard rubrics.

```
GLOBAL_RULES:
- This project uses [language(s)]. Apply language-specific best practices.
- Privacy model: [public OSS / private / commercial SaaS].
- [Add any domain-specific rules, e.g. "healthcare data must not be logged"]
- [Add any must-avoid libraries or patterns]
```

---

## Agent 1 — Security & Architecture: additional rules

*Add project-specific security concerns Agent 1 should check for.*

```
AGENT_1_ADDITIONAL:
- Check that [specific sensitive data type] is never logged
- Verify [specific auth pattern] is used consistently
- Confirm [specific API integration] validates webhooks/signatures
- [Other custom security rules]
```

**Score adjustments for this project:**

| Category | Default max | Adjusted max | Reason |
|----------|------------|--------------|--------|
| S2 Auth | 15 | 15 | standard |
| [category] | [N] | [N] | [reason for adjustment] |

---

## Agent 2 — Parity: additional rules

*Add project-specific parity concerns.*

```
AGENT_2_ADDITIONAL:
- The following endpoints MUST have frontend consumers: [list]
- The following frontend flows MUST have backend backing: [list]
- i18n is [required / not required] for this project
- [Other custom parity rules]
```

---

## Agent 3 — Quality & Licensing: additional rules

*Add project-specific quality standards and license constraints.*

```
AGENT_3_ADDITIONAL:
- Maximum acceptable file length: [300] lines
- Maximum acceptable function length: [40] lines
- GPL dependencies are [forbidden / allowed — project is also GPL]
- AGPL dependencies are [forbidden / allowed]
- Required license headers: [yes / no]
- Minimum test coverage target: [60]%
- [Other custom quality rules]
```

---

## Pass threshold overrides

*Change these values if your project requires stricter or looser standards.*

```
THRESHOLDS:
  average_pass: 85        # minimum average score across all agents
  min_agent_score: 70     # each individual agent must score at least this
  max_iterations: 3       # re-audit up to N times before giving up
```

To apply custom thresholds:
```bash
python scripts/audit_pipeline.py --threshold 90 --max-iter 2
```

---

## Domain-specific checks

### If this project handles payments (Stripe / PayPal / etc.)
Agent 1 should additionally verify:
- Stripe keys use `sk_test_` in development, `sk_live_` only in production env
- Webhook signatures are validated before processing
- Payment amounts are calculated server-side, never trusted from client
- PCI scope is minimized (no raw card data touches your servers)

### If this project uses ML/AI (Anthropic / OpenAI / etc.)
Agent 1 should additionally verify:
- API keys loaded from env (never hardcoded or committed)
- Prompts stored as files, not inline strings
- Token budget enforced before API call (prevent runaway costs)
- Retry/backoff on all API calls
- User input is sanitized before injection into prompts

### If this project stores personal data (GDPR / CCPA scope)
Agent 1 should additionally verify:
- PII fields identified and documented
- Deletion mechanism exists (`DELETE /api/users/{id}` removes all PII)
- Data retention policy documented
- No PII in log statements

### If this project is multi-tenant
Agent 2 should additionally verify:
- Every DB query filters by tenant/org ID
- No cross-tenant data leakage in API responses
- Auth tokens carry tenant context

---

## Version-specific audit notes

*Add notes about what to check (or ignore) for each specific version.*

| Version | Notes for auditors |
|---------|-------------------|
| v0.0 | Skeleton only — skip test coverage check |
| v0.1 | No frontend yet — skip parity check (Agent 2 score N/A) |
| v0.2+ | All checks apply |
| beta | Raise threshold to 90; check README completeness |
