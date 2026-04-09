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
- `onboarding/` — helps teams bootstrap a fresh project from the template.
- `onboarding/project-orientation.md` — explains how the whole project fits together before you start changing it.
- `implementation/working-principles.md` — explains the design rules the platform follows.
- `onboarding/configuration-management.md` — explains how configuration moves through backend, web, and mobile.
- `onboarding/modifying-the-template.md` — safe process for future modifications.
- `onboarding/template-finalization-checklist.md` — handoff checklist for turning the starter into a production platform.
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
- Move-in/move-out property inspection workflows with photo evidence.
- Security deposit tracking and automated refund workflows.
- Maintenance request management with status tracking.
- Shared backend, web, and mobile runtime capability discovery, including public general settings.
- CI, environment, and release documentation for production deployment.

## Getting Started

1. Read [requirements/requirements.md](requirements/requirements.md).
2. Read [onboarding/project-orientation.md](onboarding/project-orientation.md).
3. Follow [onboarding/local-setup.md](onboarding/local-setup.md).
4. Understand config flow with [onboarding/configuration-management.md](onboarding/configuration-management.md).
5. Follow [onboarding/template-finalization-checklist.md](onboarding/template-finalization-checklist.md) before you start deleting or renaming features.
6. Configure providers using [onboarding/provider-configuration.md](onboarding/provider-configuration.md).
7. Choose enabled modules and environment profile from [infrastructure/environment-configuration.md](infrastructure/environment-configuration.md).
8. Understand authorization flow with [implementation/casbin-rbac.md](implementation/casbin-rbac.md).
9. Validate docs with `python3 scripts/validate_documentation.py`.

## Documentation Status

- Phase coverage: requirements, analysis, design, infrastructure, edge cases, implementation, onboarding.
- Diagram coverage: Mermaid-based system, process, architecture, and deployment views (all house-rental specific).
- Validation coverage: enforced by `scripts/validate_documentation.py`.
- Current status: MeroGhar platform documentation — fully converted from generic rental template to house/property rental domain.
