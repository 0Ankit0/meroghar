# Implementation Execution Checklist

Use this checklist to execute the project in strict dependency order.
Each phase is **one task**. Do not start the next task until the current task exit criteria are met.

Reference plan: [docs/implementation/dependency-ordered-execution-plan.md](docs/implementation/dependency-ordered-execution-plan.md)

---

## Task 1 — Phase 1: Project Baseline & Template Finalization

### Scope
- Finalize project identity (`PROJECT_NAME`, `APP_INSTANCE_NAME`, branded copy).
- Decide `FEATURE_*` module scope.
- Boot a clean baseline and capture capability/provider snapshots.

### Required Evidence
- Command logs for setup/infra/migration/health/CI (recommended: `make phase1-baseline`).
- Baseline JSON responses for `/system/capabilities/` and `/system/providers/`.
- Approved module matrix and naming decisions.

### Exit Criteria
- [ ] New contributor can bootstrap locally without tribal knowledge.
- [ ] Identity and module scope are approved.

---

## Task 2 — Phase 2: Requirements Lock

### Scope
- Convert requirements/user stories into prioritized MVP backlog.
- Define measurable acceptance criteria and v1 out-of-scope list.

### Required Evidence
- Story list with priorities and acceptance criteria (starter bundle: `make phase2-requirements-lock`).
- Mapping table: story → backend module → frontend route → mobile surface.
- Out-of-scope v1 list with rationale and target milestone.

### Exit Criteria
- [ ] Product/engineering/QA sign off on scope baseline.

---

## Task 3 — Phase 3: Analysis and Edge-Case Resolution

### Scope
- Resolve business-rule ambiguity and close edge-case behavior decisions.

### Required Evidence
- Decision log for auth, payments, multitenancy, websocket, notifications, operations.
- Test scenarios and observability signals mapped from each decision.

### Exit Criteria
- [ ] No high-severity unresolved workflow/edge-case questions.

---

## Task 4 — Phase 4: Architecture and Contract Freeze

### Scope
- Freeze API/data/RBAC/multitenancy contracts across backend/web/mobile.

### Required Evidence
- Signed contract baseline and changelog policy.
- RBAC validation notes against Casbin model and policy enforcement paths.

### Exit Criteria
- [ ] Contract changes require explicit change-control review.

---

## Task 5 — Phase 5: Backend Core Platform Build

### Scope
- Complete core backend platform modules and runtime configuration model.

### Required Evidence
- Migration replay in clean DB.
- Health/ready/capabilities/providers verification logs.
- Security default review (cookies, trust chain, rate limits).

### Exit Criteria
- [ ] Backend platform stable for downstream client features.

---

## Task 6 — Phase 6: Feature Modules and Client Parity

### Scope
- Deliver in-scope finance/notification/websocket/analytics features end-to-end.

### Required Evidence
- Story-level smoke test results for API + web + mobile.
- Capability-driven toggle behavior checks for clients.

### Exit Criteria
- [ ] Every in-scope story has verified end-to-end behavior.

---

## Task 7 — Phase 7: Hosting Readiness (Staging/Production)

### Scope
- Prepare deployable, secure, observable environments and CI/CD gates.

### Required Evidence
- Environment profile manifests (`local`, `staging`, `production`).
- CI/CD run history covering backend/frontend/mobile/docs checks.
- Completed production-hardening checklist and rollback drill results.

### Exit Criteria
- [ ] Repeatable staging deployment and tested rollback path.
- [ ] Production hardening checklist completed.

---

## Task 8 — Phase 8: Release and Go-Live Stabilization

### Scope
- Execute release checklist, cutover plan, and stabilization operations.

### Required Evidence
- Completed release checklist with links to test/deploy artifacts.
- Critical-path smoke tests in target environment.
- On-call ownership, alert thresholds, and incident response runbook.

### Exit Criteria
- [ ] Launch approval with operational ownership and monitored health.
