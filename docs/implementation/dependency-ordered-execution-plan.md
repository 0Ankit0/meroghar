# Dependency-Ordered Execution Plan

This roadmap turns the documentation set into an implementation sequence that can be executed from project bootstrap to production launch.

## How to Use This Plan

- Execute phases in order; do not skip a phase gate.
- Treat each phase as a single tracked work item (Epic-level task).
- Do not begin the next phase until all deliverables and exit criteria are complete.
- Link PRs, test runs, and deployment evidence directly under each phase.

---

## Phase 1 — Project Baseline & Template Finalization

### Goal
Stabilize the starter and make project identity decisions before building domain features.

### Deliverables
- Project identity updated (`PROJECT_NAME`, `APP_INSTANCE_NAME`, product-facing naming).
- Enabled/disabled `FEATURE_*` module matrix approved.
- Baseline boot evidence captured (`setup`, infra up, migrations, health check, CI).
- Capability and provider endpoint baseline captured for regression reference.

### Execution Steps
1. Read orientation docs and finalization checklist.
2. Run baseline bring-up commands and archive results (`make phase1-baseline`).
3. Rename template identity in backend/frontend/mobile/docs.
4. Decide module scope and remove dead navigation/routes/docs references.
5. Snapshot `/system/capabilities/` and `/system/providers/` outputs.

### Exit Criteria
- New contributor can bootstrap the project from scratch with no tribal knowledge.
- Team has approved module scope and naming.

---

## Phase 2 — Requirements Lock

### Goal
Freeze MVP scope and acceptance criteria before implementation expands.

### Deliverables
- Prioritized MVP backlog from requirements and user stories.
- Actor-to-feature mapping (Landlord, Tenant, Property Manager, Admin).
- Acceptance criteria matrix with API/UI/test expectations.
- Explicit out-of-scope list for v1.

### Execution Steps
1. Initialize requirements-lock artifacts (`make phase2-requirements-lock`).
2. Consolidate requirements docs into one prioritized backlog.
3. Attach measurable acceptance criteria to each story.
4. Map each story to backend module + frontend route + mobile surface.
5. Mark deferred stories and rationale.

### Exit Criteria
- Product, engineering, and QA sign off on one scope baseline.

---

## Phase 3 — Analysis and Edge-Case Resolution

### Goal
Resolve ambiguity and failure behavior before coding high-risk paths.

### Deliverables
- Confirmed business rules and workflow decisions.
- Closed edge-case decision log across auth, payments, multitenancy, websocket, notifications, operations.
- Test scenarios derived from each edge-case decision.

### Execution Steps
1. Review analysis docs and edge-case docs together.
2. Create decision records for unresolved behaviors.
3. Convert each decision into test cases and observability signals.

### Exit Criteria
- No high-severity unresolved product behavior questions.

---

## Phase 4 — Architecture and Contract Freeze

### Goal
Lock data, API, RBAC, and interaction contracts across all clients.

### Deliverables
- High-level and detailed design consistency sign-off.
- Frozen API schema contract and DTO naming.
- RBAC policy mapping validated against Casbin implementation.
- Multitenancy isolation contract documented end-to-end.

### Execution Steps
1. Reconcile high-level and detailed design docs.
2. Align backend schemas with frontend/mobile types.
3. Validate RBAC and role resolution behavior.
4. Finalize tenant boundary rules in API and data access.

### Exit Criteria
- Contract changes now require deliberate change-control review.

---

## Phase 5 — Backend Core Platform Build

### Goal
Implement backend platform primitives and cross-cutting services.

### Deliverables
- Stable IAM/token lifecycle, multitenancy, communications abstraction, observability/system APIs.
- Migration chain reproducible for fresh environments.
- Runtime configuration model enforced (env bootstrap + safe DB overrides).

### Execution Steps
1. Complete backend core, iam, multitenancy, communications, observability/system modules.
2. Apply and verify migrations in clean DB.
3. Verify health/ready/capabilities/providers endpoints.
4. Validate security-sensitive defaults (cookies, trust chain, rate limits).

### Exit Criteria
- Backend platform is stable for downstream feature modules and clients.

---

## Phase 6 — Feature Modules and Client Parity

### Goal
Deliver end-to-end user journeys across backend, web, and mobile.

### Deliverables
- Finance, notifications, websocket, analytics features completed per scope.
- Web route-level parity for all in-scope user stories.
- Mobile parity for launch-critical flows.
- Capability-driven feature toggling validated in clients.

### Execution Steps
1. Complete backend feature APIs and provider integrations.
2. Implement corresponding frontend and mobile experiences.
3. Run end-to-end smoke tests for each story.
4. Verify dynamic behavior when modules/providers are toggled.

### Exit Criteria
- Every in-scope story has a verified API + web/mobile path.

---

## Phase 7 — Hosting Readiness (Staging/Production)

### Goal
Make environments deployable, secure, observable, and repeatable.

### Deliverables
- `local`, `staging`, `production` environment profiles operational.
- CI/CD gates enforce backend/frontend/mobile/docs quality checks.
- Production hardening checklist complete (secrets, network/proxy, storage, providers/callbacks, workers, observability).
- Deployment/rollback runbooks tested in staging.

### Execution Steps
1. Configure environment-specific values and secret management.
2. Implement CI/CD pipeline and artifact publishing.
3. Validate ingress/proxy/cookie/CORS configuration per environment.
4. Validate provider callbacks/webhooks and worker behavior.
5. Execute staging deployment with rollback drill.

### Exit Criteria
- Team can perform low-risk repeatable deployments with recovery confidence.

---

## Phase 8 — Release and Go-Live Stabilization

### Goal
Ship safely and operationalize ownership.

### Deliverables
- Release checklist completed with evidence.
- Post-deploy health/readiness and critical flow smoke tests passed.
- Incident ownership, on-call path, and alert thresholds documented.
- Post-launch stabilization window and review cadence scheduled.

### Execution Steps
1. Run release checklist before each promotion.
2. Verify migration order and traffic-shift plan.
3. Execute critical-path smoke tests in target environment.
4. Confirm rollback and secret-rotation readiness.
5. Monitor stabilization metrics and close launch issues.

### Exit Criteria
- Production launch approved with monitored service health and clear ownership.
