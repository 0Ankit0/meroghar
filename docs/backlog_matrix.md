# Requirements Backlog Matrix

This matrix is derived from `docs/requirements.md` and maps each requirement to its implementation status and owning app.

| Requirement | Current code status | Gap type | Owner app |
|---|---|---|---|
| IAM multi-tenancy (organization isolation) | Implemented via active organization scoping in middleware/viewsets | partial | `apps/iam`, shared across apps |
| User management (register/login/profile) | Implemented (auth login/profile APIs and user CRUD) | partial | `apps/iam` |
| Group management | Implemented | partial | `apps/iam` |
| Invitation system | Added in this phase (invitation model + API + UI flow) | partial | `apps/iam` |
| Property inventory (properties/units/status) | Implemented | partial | `apps/housing` |
| Unit inspections + inventory | Implemented models/API/UI (inspection + inventory item) | partial | `apps/housing` |
| Tenant profiles + lease lifecycle + docs | Implemented | partial | `apps/housing` |
| Lease renewals workflow | Added in this phase (renewal request/approve/reject) | partial | `apps/housing` |
| Invoicing, payments, payment status, taxation | Implemented | partial | `apps/finance` |
| Expense tracking | Implemented and enhanced with auto-expense from work-order completion | partial | `apps/finance`, `apps/operations` |
| Late fees automation | Added in this phase (invoice late-fee application) | partial | `apps/finance` |
| Work orders and lifecycle | Implemented | partial | `apps/operations` |
| Assignment auto-routing to vendors/staff | Added in this phase (vendor auto-assignment) | partial | `apps/operations` |
| Vendor management | Implemented and linked to auto-assignment | partial | `apps/operations` |
| CRM lead tracking, applications, showings | Existing models/API; expanded pipeline and completion semantics | partial | `apps/crm` |
| CRM follow-ups | Added in this phase | partial | `apps/crm` |
| Scheduling/calendar reminders | Not implemented in this phase | missing | `apps/core` (future: dedicated scheduling) |
| Analytics (occupancy, receivables, maintenance KPI) | Added reporting KPI API endpoint | partial | `apps/reporting` |

## Phase Deliverables (defined before implementation)

## Phase A — Core operations (`apps/operations`, `apps/finance`)
- **API**
  - Work-order create/update should auto-assign a vendor when `assigned_vendor` is empty.
  - Invoice listing should apply late fees to overdue unpaid invoices.
  - Expense API should support linking expenses to work orders and guard org integrity.
- **Web UI**
  - Work-order forms expose service type + labor hours needed for vendor routing and expense derivation.
  - Invoice detail/list surfaces late fee amount.
- **Migration**
  - Add fields for work-order routing and completion (`preferred_service_type`, `actual_hours`, `vendor_auto_assigned_at`).
  - Add invoice late-fee fields (`late_fee_amount`, `late_fee_applied_at`).
- **Tests**
  - Auto-assignment test.
  - Late-fee application test.
  - Auto-expense-on-resolution test.

## Phase B — Tenant lifecycle (`apps/iam`, `apps/housing`)
- **API**
  - Invitation create/list/accept endpoints.
  - Lease renewal CRUD with manager approval/rejection and renewal lease generation.
- **Web UI**
  - Invitation list/send page.
  - Lease renewal list/create/update pages.
- **Migration**
  - `OrganizationInvitation` in IAM.
  - `LeaseRenewal` in Housing.
- **Tests**
  - Invitation acceptance flow.
  - Lease renewal approval creates next lease.

## Phase C — Leasing funnel (`apps/crm`)
- **API**
  - Rental application pipeline statuses with transitions.
  - Follow-up model endpoints.
  - Showing completion endpoint behavior (`completed_at` timestamp when marked complete).
- **Web UI**
  - Follow-up list/form pages.
  - Showing completion action from showing list.
- **Migration**
  - Add follow-up model + showing completion timestamp.
- **Tests**
  - Follow-up creation/list scope by org.
  - Showing completion timestamp behavior.

## Phase D — Analytics (`apps/reporting`)
- **API**
  - KPI endpoint for occupancy, receivables aging summary, maintenance open/close throughput.
- **Web UI**
  - Reporting index links to KPI summary and cards.
- **Migration**
  - No schema migration required.
- **Tests**
  - KPI endpoint returns occupancy + receivables + maintenance aggregates in org scope.
