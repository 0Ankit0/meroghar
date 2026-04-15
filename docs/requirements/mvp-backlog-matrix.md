# MVP Backlog and Requirements Traceability Matrix

## 1) Purpose and source-of-truth status

This document converts `docs/requirements/requirements.md` and `docs/requirements/user-stories.md` into a prioritized MVP backlog with explicit actor scope, journey mapping, measurable acceptance criteria, and implementation traceability.

**Decision:** this matrix is the source of truth for engineering implementation, QA test design, and product acceptance for v1.

---

## 2) MVP prioritization model

- **P0 (Must-have for v1 launch):** required for core renting flow and operational safety.
- **P1 (Should-have soon after v1):** important but not launch-blocking.
- **P2 (Could-have / deferred):** intentionally excluded from v1 to prevent architecture drift.

---

## 3) Actor scope and core journeys

### 3.1 Actor scope

| Actor | In-scope for MVP | Primary responsibilities |
|---|---|---|
| Landlord | Yes (P0) | Create listings, approve applications (or instant booking), countersign leases, manage charges and maintenance intake |
| Tenant | Yes (P0) | Discover listings, apply, sign lease, pay invoices, receive and act on notifications |
| Property Manager | Yes (limited P0) | Execute inspections, update maintenance tasks, maintain task evidence |
| Admin | Yes (limited P0) | Operate RBAC/security controls, verify landlord documents, manage disputes escalations, audit actions |

### 3.2 Core journey coverage matrix

| Journey | Landlord | Tenant | Property Manager | Admin |
|---|---|---|---|---|
| Listing | Owns create/publish/configure | Browse/search/view | N/A | Manages property taxonomy templates |
| Application | Approve/decline or enable instant booking | Submit/track/cancel | N/A | Oversight for abuse/disputes |
| Lease | Generate/countersign/amend | Review/sign | N/A | Template governance |
| Maintenance | Create/triage requests | Create requests/track | Execute and update tasks | Escalation visibility |
| Payments | Invoice/charges/payout view | Pay/dispute/view history | N/A | Exceptional overrides/audits |
| Notifications | Receive workflow events | Receive workflow events | Receive task events | Configure templates and monitor delivery |

---

## 4) Prioritized MVP backlog with measurable acceptance criteria and implementation touchpoints

> Notes:
> - IDs are normalized to backlog items (`MVP-*`) and mapped to original FR and user stories.
> - “Implementation touchpoints” include existing modules/routes/folders and explicit planned additions where no module exists yet.

| Priority | Backlog ID | Feature | Actors | Core Journey | Source Requirements | Acceptance criteria (measurable) | Implementation touchpoints |
|---|---|---|---|---|---|---|---|
| P0 | MVP-001 | Auth, registration, OTP, session security | Landlord, Tenant, Admin | Notifications (auth events) | FR-UM-001/002/004/005; LND-001; TNT-001 | **API:** signup/login/refresh/logout endpoints return 2xx for valid payloads and 4xx for invalid/expired OTP; concurrent session cap enforced. **UI:** web/mobile auth forms support signup, login, OTP verification, password reset. **Tenant isolation:** authenticated user only reads own profile/session metadata. **Security:** JWT+refresh flow, account lockout after configured failed attempts, admin 2FA required. | Backend: `backend/src/apps/iam/api/v1/auth/*`, `backend/src/apps/iam/models/*`, `backend/src/apps/iam/services/*`. Frontend: `frontend/src/app/(auth)/*`, `frontend/src/components/auth/*`, `frontend/src/hooks/use-auth.ts`. Mobile: `mobile/lib/features/auth/**`. |
| P0 | MVP-002 | Property listing creation + publication | Landlord, Admin | Listing | FR-AL-001/002/005; LND-003/004/007; ADM-006 | **API:** landlord can create draft listing, update, publish/unpublish; validation errors for missing required fields. **UI:** listing wizard captures type, amenities, media, and status badge (draft/published). **Tenant isolation:** listing CRUD scoped to landlord’s tenant/org. **Security:** ownership checks + RBAC permission required for publish actions. | Backend: **Implemented** in `backend/src/apps/listings/{api,models,schemas,services}` plus owner-scoped landlord routes under `/assets` and `/properties/*`. Frontend: **Implemented** in `frontend/src/app/(user-dashboard)/listings/*`, `frontend/src/components/listings/*`, `frontend/src/hooks/use-properties.ts`. Mobile: **Implemented** in `mobile/lib/features/listings/**` with landlord access gating. |
| P0 | MVP-003 | Availability and pricing rules | Landlord, Tenant | Listing | FR-AL-003/004; LND-005/006; TNT-004/005 | **API:** supports monthly and daily/weekly rates, min/max duration, blocked dates; price quote endpoint returns deterministic total for same inputs. **UI:** calendar shows unavailable dates and pricing breakdown pre-application. **Tenant isolation:** quote and availability responses restricted to target listing visibility rules. **Security:** server-side validation for date overlap and negative pricing prevention. | Backend: **Implemented** in `backend/src/apps/pricing/**` and `backend/src/apps/availability/**`. Frontend: **Implemented** in the public property detail flow plus landlord listing editors. Mobile: **Implemented** in `mobile/lib/features/listings/` pricing and availability models/pages. |
| P0 | MVP-004 | Property search and discovery | Tenant | Listing | FR-BR-001; TNT-004/005 | **API:** search endpoint supports type, location, date range, price filters; p95 response ≤ 800ms on MVP test dataset. **UI:** filterable search results and listing detail page with gallery and amenities. **Tenant isolation:** unpublished/private listings never appear to unauthorized users. **Security:** input sanitization and rate limiting on search endpoints. | Backend: **Implemented** in `backend/src/apps/search/**` plus public property detail/read APIs. Frontend: **Implemented** in `/properties`, `/properties/[id]`, and supporting listing hooks/components. Mobile: **Implemented** in `mobile/lib/features/listings/presentation/pages/listing_search_page.dart` and `listing_detail_page.dart`. |
| P0 | MVP-005 | Rental application submission and decisioning | Landlord, Tenant | Application | FR-BR-002/003/005; LND-008/009/011; TNT-006/007/009 | **API:** tenant creates application, system places timed hold, landlord approves/declines or instant-booking auto-confirms, cancellation policy computes refund amount deterministically. **UI:** application status timeline with pending/confirmed/declined/cancelled states. **Tenant isolation:** tenant can view only own applications; landlord sees only org-scoped applications. **Security:** anti-double-booking transaction lock and idempotency key for submission. | Backend: **Implemented** in `backend/src/apps/bookings/{api,models,schemas,services}` with the bookings migration `backend/alembic/versions/4f2c8d7a9b1e_add_bookings_and_agreements.py`. Frontend: **Implemented** in `frontend/src/app/(user-dashboard)/bookings/*`, `frontend/src/components/bookings/*`, `frontend/src/hooks/use-bookings.ts`, and the public property booking request form. Mobile: **Implemented** in `mobile/lib/features/applications/**` plus tenant booking entry from `mobile/lib/features/listings/presentation/pages/listing_detail_page.dart`. |
| P0 | MVP-006 | Lease generation and digital signing | Landlord, Tenant, Admin | Lease | FR-RA-001/002; LND-012/013; TNT-010; ADM-007 | **API:** generate lease from template after confirmation, record e-sign timestamp/IP, store immutable signed artifact. **UI:** lease preview + sign + countersign status. **Tenant isolation:** only lease parties and authorized admin can access lease file. **Security:** immutable audit trail and tamper-evident document hash storage. | Backend: **Implemented** in `backend/src/apps/bookings/{api,models,schemas,services}` with local artifact storage via `backend/src/apps/core/storage.py`. Frontend: **Implemented** in the bookings workflow pages and agreement components under `frontend/src/app/(user-dashboard)/bookings/*` and `frontend/src/components/bookings/*`. Mobile: **Implemented** in `mobile/lib/features/lease/**` and tenant application detail routes under `mobile/lib/features/applications/**`. |
| P0 | MVP-007 | Invoicing, monthly rent collection, receipts | Landlord, Tenant | Payments | FR-PI-001/001A/002/005/008; LND-016; TNT-011/012 | **API:** monthly invoice generated by recurring scheduler + due date policy; payment intent/callback update status; reminder cadence (T-7/T-3/T-1) and overdue fee policy job operate deterministically. **UI:** invoice list, rent ledger timeline, checkout, and receipt display. **Tenant isolation:** payment records scoped to payer/payee tenant. **Security:** gateway callbacks signature-verified and replay-protected; reminder suppression after settlement. | Backend: existing finance: `backend/src/apps/finance/api/v1/payment.py`, `backend/src/apps/finance/models/payment.py`, `backend/src/apps/finance/services/*`; extend with invoice/billing scheduler domain (**Planned** `backend/src/apps/invoicing/**`). Frontend: `frontend/src/app/(user-dashboard)/finances/page.tsx`, `frontend/src/components/finances/*`, `frontend/src/hooks/use-finances.ts`. Mobile: `mobile/lib/features/payments/**`. |
| P0 | MVP-008 | Deposit handling and post-tenancy charges/disputes | Landlord, Tenant, Admin | Payments | FR-PI-003/004; LND-014/015/017; TNT-013; ADM-008/009 | **API:** supports deposit hold/charge, deduction with evidence, refund window SLA, and dispute state machine. **UI:** itemized deduction and dispute submission/resolution timeline. **Tenant isolation:** only involved parties + admin mediator can access charge evidence. **Security:** immutable financial audit log for manual overrides. | Backend: finance + notifications existing modules; **Planned** dispute domain `backend/src/apps/disputes/**`. Frontend: **Planned** disputes pages; existing notifications components for alerts. Mobile: **Planned** disputes under payments feature. |
| P0 | MVP-009 | Maintenance request intake, assignment, and preventive task tracking | Landlord, Tenant, Property Manager | Maintenance | FR-MS-001/002/003/005; LND-021; STF-001/004/005 | **API:** create maintenance request with unique ID, category/severity, evidence attachments, assignment, and status transitions (open→in-progress→completed). Preventive task endpoints create recurring operational tasks with due date + SLA. **UI:** request list + task board with preventive queue and escalation badges. **Tenant isolation:** requests visible only within property's tenant/org boundary. **Security:** role checks for assignment/completion approvals and immutable timeline entries. | Backend: **Planned** `backend/src/apps/maintenance/**`, `backend/src/apps/operations/**`; notification integration via existing `backend/src/apps/notification/*`. Frontend: **Planned** maintenance/operations routes and components. Mobile: **Planned** `mobile/lib/features/maintenance/**`. |
| P0 | MVP-010 | Notification delivery for rent, bills, and maintenance workflows | All actors | Notifications | FR-BR-003, FR-PI-005/007/008, FR-MS-001/005; LND/TNT/STF/ADM notification needs | **API:** event-driven notifications generated for application decision, lease signed, rent reminder, payment success/failure, utility bill split publication, overdue escalation, and maintenance assignment/update; delivery status persisted. **UI:** in-app notification center with read/unread controls and deep links to payable/request detail pages. **Tenant isolation:** no cross-tenant notification leakage. **Security:** template rendering escapes unsafe content and honors user notification preferences. | Backend existing: `backend/src/apps/notification/api/v1/*`, `backend/src/apps/notification/models/*`, `backend/src/apps/notification/services/*`, `backend/src/apps/communications/*`. Frontend existing: `frontend/src/app/(user-dashboard)/notifications/page.tsx`, `frontend/src/components/notifications/*`, `frontend/src/hooks/use-notifications.ts`. Mobile existing: `mobile/lib/features/notifications/**`. |
| P0 | MVP-017 | Utility bill upload, split assignment, and tenant collection | Landlord, Property Manager, Tenant | Payments | FR-PI-007/008; LND-016; TNT-011/012 | **API:** owner/manager uploads utility bill image + metadata, configures split (single/equal/percentage/fixed), validates totals, publishes tenant payable entries, and tracks settlement/dispute. **UI:** bill workspace with attachment preview, split editor, and tenant payable history. **Tenant isolation:** tenant only sees own bill-share entries while owner/manager sees property-scoped data. **Security:** attachment access control, immutable bill split audit trail, and dispute timeline retention. | Backend: **Planned** `backend/src/apps/utility_billing/**`, `backend/src/apps/invoicing/**`. Frontend: **Planned** utility billing workspace under finance dashboard. Mobile: **Planned** bill-share list and payment screens under payments. |
| P0 | MVP-011 | Multi-tenancy guardrails and RBAC enforcement | All actors | Cross-cutting | FR-UM-004/005 + platform constraints | **API:** every protected endpoint enforces tenant context and role permission; forbidden access returns 403 with no data leakage. **UI:** menu/routes hidden or disabled when permission is absent. **Tenant isolation:** automated tests prove cross-tenant reads/writes are blocked. **Security:** audit logs for privileged actions and admin 2FA enforced. | Backend existing: `backend/src/apps/multitenancy/*`, `backend/src/apps/iam/api/v1/rbac.py`, `backend/src/apps/iam/utils/rbac.py`, `backend/src/apps/iam/models/casbin_rule.py`, `backend/src/apps/observability/*`. Frontend existing: `frontend/src/hooks/use-tenants.ts`, `frontend/src/hooks/use-rbac.ts`, `frontend/src/components/tenants/*`, `frontend/src/app/(admin-dashboard)/admin/rbac/*`. Mobile: core auth/provider layers + **Planned** tenant switcher parity. |
| P1 | MVP-012 | Move-in/move-out inspections with photo evidence | Landlord, Tenant, Property Manager | Maintenance, Lease | FR-CA-001/002/003; LND-019/020; TNT-014/016; STF-002/003 | **API:** inspection checklist templates, photo upload, move-in vs move-out diff summary. **UI:** guided checklist and countersign flow. **Tenant isolation:** inspection artifacts restricted to tenancy participants. **Security:** signed timestamps and immutable evidence storage policy. | Backend: **Planned** `backend/src/apps/inspections/**`. Frontend: **Planned** inspections routes/components. Mobile: **Planned** `mobile/lib/features/inspections/**`. |
| P1 | MVP-013 | Staff scheduling and work history | Property Manager, Landlord | Maintenance | FR-UM-003; STF-006/007 | **API:** staff availability and assignment calendar endpoints. **UI:** manager calendar + completed history filters. **Tenant isolation:** staff can only see assigned org tasks. **Security:** assignment changes are auditable. | Backend: **Planned** `backend/src/apps/staffing/**`. Frontend: **Planned** staff operations pages. Mobile: **Planned** staff schedule module. |
| P1 | MVP-014 | Landlord payouts and settlement exports | Landlord, Admin | Payments | FR-PI-006; LND-018; ADM-010 | **API:** net payout computation (gross - fees - commission), scheduled disbursement status, CSV export endpoint. **UI:** payout ledger with settlement drill-down. **Tenant isolation:** landlord sees only own payout records. **Security:** payout account update requires step-up authentication. | Backend: finance extension (**Planned** payout submodule under `backend/src/apps/finance`). Frontend/mobile: extend existing finance screens. |
| P2 | MVP-015 | Reviews and ratings | Tenant | Listing | TNT-017/018 | **API/UI:** review create/read after completed tenancy. **Tenant isolation:** only verified tenants can post for completed stay. **Security:** moderation and abuse controls required before launch. | Deferred; no v1 implementation. |
| P2 | MVP-016 | Advanced analytics and tax reporting | Landlord, Admin | Reporting | LND-023/024/025; ADM-001/002 | **API/UI:** portfolio KPIs, occupancy/tax exports. **Tenant isolation:** strict reporting boundary per org. **Security:** report exports access controlled + watermarking. | Partial existing analytics plumbing in `backend/src/apps/analytics/*`, `frontend/src/lib/analytics/*`, `mobile/lib/core/analytics/*`; business reporting features deferred. |

---

## 5) Explicit v1 out-of-scope list (to prevent architecture drift)

The following are **out of scope for v1** and must not drive foundational architecture changes before P0 completion:

1. Public property reviews/ratings and moderation workflows (MVP-015).
2. Full financial intelligence dashboards, occupancy analytics, and tax reporting exports (MVP-016).
3. Advanced optimization for preventive servicing recurrence (auto-priority tuning, predictive scheduling) beyond rule-based recurrence.
4. Complex tenancy amendments/version chains beyond one amendment cycle.
5. Buy-now-pay-later provider expansion beyond a single card/bank gateway path.
6. Platform-wide custom report builder and scheduled admin reports.
7. Advanced dispute mediation chat tooling (retain simple ticket timeline in v1).

---

## 6) Traceability index (original requirement → MVP backlog)

### 6.1 FR to backlog mapping

- FR-UM-001/002/004/005 → MVP-001, MVP-011
- FR-AL-001/002/003/004/005 → MVP-002, MVP-003, MVP-004
- FR-BR-001/002/003/005 → MVP-004, MVP-005, MVP-010
- FR-RA-001/002 → MVP-006
- FR-PI-001/002/003/004/005/006 → MVP-007, MVP-008, MVP-014
- FR-CA-001/002/003 → MVP-012
- FR-MS-001 → MVP-009

### 6.2 User stories to backlog mapping

- Landlord LND-001…021 primarily map to MVP-001…012; LND-022+ and reporting stories LND-023…025 map to P2 (MVP-016).
- Tenant TNT-001…016 map to MVP-001, 004, 005, 006, 007, 008, 012; TNT-017/018 map to P2 (MVP-015).
- Staff STF-001…005 map to MVP-009/012; STF-006/007 map to MVP-013.
- Admin ADM-001…012 map to MVP-001, 002, 006, 008, 011, 014, and P2 reporting slice in MVP-016.

---

## 7) Exit criteria: signed-off requirements matrix

This document is considered “signed off” when all gates below are marked complete:

- [ ] **Product sign-off:** priorities and out-of-scope boundaries accepted.
- [ ] **Engineering sign-off:** implementation touchpoints validated, new module boundaries approved.
- [ ] **QA sign-off:** every P0 backlog item has test cases for API behavior, UI behavior, tenant isolation, and security constraints.
- [ ] **Security sign-off:** auth, RBAC, tenant isolation, and audit logging controls reviewed for P0.
- [ ] **Delivery sign-off:** release plan confirms all P0 items are committed for v1.

### Sign-off record

| Function | Owner | Date | Status | Notes |
|---|---|---|---|---|
| Product | _TBD_ | _TBD_ | Pending | |
| Engineering | _TBD_ | _TBD_ | Pending | |
| QA | _TBD_ | _TBD_ | Pending | |
| Security | _TBD_ | _TBD_ | Pending | |
