# MeroGhar Documentation

**MeroGhar** ("My House" in Nepali) is a house, flat, and apartment rental platform connecting landlords with tenants.

## Documentation Structure

- `requirements/` — scope, personas, and success criteria for the MeroGhar platform.
- `analysis/` — domain rules, workflows, actors (Landlord, Tenant, Property Manager, Admin), and events.
- `high-level-design/` — architecture and major runtime flows (property listings, rental applications, lease agreements).
- `detailed-design/` — API contracts, components, data models, and database schema.
- `infrastructure/` — environments, networking, deployment, and CI/CD.
- `edge-cases/` — failure modes and operational concerns specific to property rental.
- `implementation/` — build, rollout, and testing playbooks.
- `implementation/dependency-ordered-execution-plan.md` — phase-gated plan from bootstrap through production launch.
- `implementation/working-principles.md` — explains the design rules the platform follows.
- `requirements/mvp-backlog-matrix.md` — prioritized engineering scope and traceability for the documented features.
- `implementation/implementation-playbook.md` — operator checklist for bring-up and verification.
- `infrastructure/production-hardening-checklist.md` — deployment reviews that belong to each downstream project.

## Platform Overview

MeroGhar enables:
- **Landlords** to list properties (Apartment, House, Room, Studio, Villa, Commercial Space), manage availability, and handle lease agreements.
- **Tenants** to search, filter (bedrooms, bathrooms, furnishing, location), apply for rental, sign leases, and raise maintenance requests.
- **Property Managers** (staff) to oversee listings, conduct move-in/move-out inspections, and process payments.
- **Admins** to manage users, resolve disputes, and access occupancy and revenue reports.

## Key Features

- Feature-flagged modules for auth, multi-tenancy, notifications, analytics, finance, and websockets.
- Provider-driven outbound communications for email, push, SMS, analytics, and payments.
- Domain-aware Casbin RBAC with SQL-managed roles and permissions mirrored into runtime policy tuples.
- Multi-device notification registry across Web Push, FCM, and OneSignal.
- Property listing management with amenity attributes (bedrooms, bathrooms, floor area, furnishing status, parking, balcony).
- Rental application and lease agreement lifecycle management.
- Monthly rent collection workflows with configurable reminders, overdue handling, and receipts.
- Utility bill sharing with bill-image upload and tenant-level payable split assignment (single-tenant or multi-tenant).
- Move-in/move-out property inspection workflows with photo evidence.
- Security deposit tracking and automated refund workflows.
- Maintenance request and preventive operations workflows with assignment, SLA tracking, and evidence logging.
- Shared backend, web, and mobile runtime capability discovery, including public general settings.
- CI, environment, and release documentation for production deployment.

## Getting Started

1. Read [requirements/requirements.md](requirements/requirements.md).
2. Read [requirements/mvp-backlog-matrix.md](requirements/mvp-backlog-matrix.md).
3. Read [implementation/dependency-ordered-execution-plan.md](implementation/dependency-ordered-execution-plan.md).
4. Use [implementation/implementation-playbook.md](implementation/implementation-playbook.md) and [infrastructure/environment-configuration.md](infrastructure/environment-configuration.md) to shape runtime setup.
5. Understand authorization flow with [implementation/casbin-rbac.md](implementation/casbin-rbac.md).
6. Validate docs with `python3 scripts/validate_documentation.py`.

## Documentation Status

- Phase coverage: requirements, analysis, design, infrastructure, edge cases, implementation.
- Diagram coverage: Mermaid-based system, process, architecture, and deployment views (all house-rental specific).
- Validation coverage: enforced by `scripts/validate_documentation.py`.
- Current status: MeroGhar platform documentation — fully converted from generic rental template to house/property rental domain.
