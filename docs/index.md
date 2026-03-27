# Welcome to MeroGhar

MeroGhar is an enterprise-grade rental property management system designed for the Nepalese market.

## Key Features

- **Property Management**: Track properties, units, and amenities.
- **Tenant & Lease Management**: Full lifecycle management of tenants and lease agreements.
- **Billing & Payments**: Automated invoicing and integrated **Khalti** online payments.
- **Maintenance**: Digital work order tracking for property upkeep.
- **Multi-tenancy**: Support for multiple organizations and organization-groups.

## Getting Started

To run the project locally:

1. Clone the repository.
2. Install dependencies: `pipenv install`
3. Enter shell: `pipenv shell`
4. Run migrations: `python manage.py migrate`
5. Start server: `python manage.py runserver`

## Architecture

MeroGhar follows a **Modular Monolith** architecture using Django Web Framework.

See [Architecture](architecture.md) for details.

## Domain Ownership Map

| Requirement Area | Owning App(s) | Primary Web Namespace |
|---|---|---|
| IAM & Multi-tenancy | `apps/iam`, `apps/core` | `/iam/` |
| Property / Unit / Tenant / Lease | `apps/housing` | `/housing/` |
| Billing, Payments, Expenses | `apps/finance` | `/finance/` |
| Maintenance & Operations | `apps/operations` | `/operations/` |
| CRM & Leasing Funnel | `apps/crm` | `/crm/` |
| Analytics & Reports | `apps/reporting` | `/reporting/` |

For API route ownership, use `config/api_urls.py` as the root registry.
