# Version Plan — v[X.Y]: [Short title]
*Created by: project-architect skill*
*Status: planned / in-progress / complete*

---

## Goal

[One paragraph describing what this version achieves and why it matters.
What can the user do after this version that they couldn't do before?]

---

## Acceptance criterion

> [Copy this verbatim from the roadmap. This is the single test for "done".]

**How to verify:**
```bash
[Exact commands or steps to verify the acceptance criterion]
```

---

## Out of scope

The following are explicitly NOT part of this version:
- [Feature or concern deferred to vX.Y+1]
- [Feature or concern deferred to vX.Y+1]

---

## Files to create

| File | Purpose | Spec owner | Status |
|------|---------|-----------|--------|
| `path/to/file.ext` | [one-line purpose] | Claude Code | planned |

---

## Files to modify

| File | What changes | Status |
|------|-------------|--------|
| `path/to/file.ext` | [description] | planned |

---

## Files to delete

| File | Reason for deletion |
|------|-------------------|
| `backup_file.py` | Stale backup — replaced by refactored module |

---

## Dependency order

Generate files in this exact order (bottom-up):

1. `[config/env file]`
2. `[model/schema file]`
3. `[service/business logic file]`
4. `[router/controller file]`
5. `[entry point]`
6. `[frontend types]`
7. `[frontend service]`
8. `[frontend component]`
9. `[frontend page]`
10. `[tests]`

---

## API changes

*List every new or modified endpoint.*

| Method | Path | New / Modified / Removed | Notes |
|--------|------|--------------------------|-------|
| | | | |

---

## Data model changes

*List every schema/model change.*

| Model | Change | Migration needed? |
|-------|--------|------------------|
| | | |

---

## Security checklist for this version

- [ ] No new secrets added to source
- [ ] All new endpoints have auth guards (if required)
- [ ] All new inputs validated at the HTTP boundary
- [ ] CORS not widened
- [ ] New dependencies reviewed for license and CVEs

---

## Review checklist

Before marking this version complete:

- [ ] Acceptance criterion verified manually
- [ ] All new files APPROVED by build orchestrator review
- [ ] PROJECT_MANIFEST.md updated with new files
- [ ] SESSION_HANDOFF.md updated
- [ ] `python scripts/audit_pipeline.py` run and score ≥ 85
- [ ] AUDIT_REPORT.md written to docs/

---

## Notes and decisions

*Record any design decisions made during this version's implementation.*

| Decision | Alternatives | Reason |
|----------|-------------|--------|
| | | |
