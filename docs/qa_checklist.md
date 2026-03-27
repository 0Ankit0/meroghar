# QA Checklist

Use this checklist during feature QA and release sign-off. Reference requirement IDs from `docs/requirements.md` in ticket descriptions, PRs, and test updates.

## 1. IAM (IAM-*)

### Acceptance criteria
- [ ] IAM-01: User can only access data for their active organization.
- [ ] IAM-02: Login/profile flows return correct active organization context.
- [ ] IAM-03: Group/role assignment enforces permissions in UI and API.
- [ ] IAM-04: Invitation workflows are validated end-to-end (when implemented).

### Edge-case checks (from `docs/edge_cases.md`)
- [ ] Cross-organization URL tampering is denied with `403` and no data exposure.
- [ ] Organization switching across multiple tabs does not create data in the wrong org context.

## 2. Housing & Leasing (HOU-*, TEN-*)

### Acceptance criteria
- [ ] HOU-01/HOU-02: Property and unit CRUD support required metadata.
- [ ] HOU-03: Unit occupancy/maintenance status changes are reflected in list/detail screens.
- [ ] HOU-04/HOU-05: Inspections and inventory support move-in/out workflows (when implemented).
- [ ] TEN-01 through TEN-04: Tenant profile, lease creation/status, and lease document storage work end-to-end.
- [ ] TEN-05/TEN-06: Renewal and screening scenarios are test-planned (or implemented).

### Edge-case checks (from `docs/edge_cases.md`)
- [ ] Lease overlap attempts are rejected with a clear validation error.
- [ ] Holdover tenant scenario does not auto-vacate units without manual confirmation.
- [ ] Unit swap/transfer flow preserves billing and lease history integrity.

## 3. Finance (FIN-*)

### Acceptance criteria
- [ ] FIN-01: Invoice creation computes due totals and status transitions correctly.
- [ ] FIN-02/FIN-03: Payment capture supports all configured methods and status updates.
- [ ] FIN-04: Tax amounts are applied consistently to generated invoices.
- [ ] FIN-05 through FIN-07: Expense, late-fee, and financial report coverage exists in tests/PR plan.

### Edge-case checks (from `docs/edge_cases.md`)
- [ ] Duplicate payment callbacks do not create double charges (idempotency check).
- [ ] Prorated rent handles month-length differences including leap-year dates.
- [ ] Payment reversal/chargeback re-opens invoice and corrects balance.

## 4. Operations (OPS-*)

### Acceptance criteria
- [ ] OPS-01/OPS-02: Work order creation and lifecycle transitions behave correctly.
- [ ] OPS-03: Notification messages fire for key state transitions.
- [ ] OPS-04/OPS-05: Assignment/vendor features have requirement + test traceability (or implementation plan).

### Edge-case checks (from `docs/edge_cases.md`)
- [ ] Concurrent work-order edits detect version conflicts and prevent silent overwrite.

## 5. CRM, Scheduling, Reporting (CRM-*, SCH-*, RPT-*)

### Acceptance criteria
- [ ] CRM-01 through CRM-04: Lead, showing, and application flows are traced to tests.
- [ ] SCH-01/SCH-02: Calendar/reminder behavior has documented acceptance tests.
- [ ] RPT-01 through RPT-03: Reporting outputs are validated against known fixture data.

## 6. Release gating checks
- [ ] Every domain feature change includes requirement ID references in PR description.
- [ ] Every touched requirement has corresponding test name/comment coverage updates.
- [ ] CI requirement-traceability job passes.
