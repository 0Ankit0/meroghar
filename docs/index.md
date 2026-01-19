# Welcome to MeroGhar

MeroGhar is an enterprise-grade rental property management system designed for the Nepalese market.

## Key Features

- **Property Management**: Track properties, units, and amenities.
- **Tenant & Lease Management**: Full lifecycle management of tenants and lease agreements.
- **Billing & Payments**: Automated invoicing and integrated **Khalti** online payments.
- **Maintenance**: Digital work order tracking for property upkeep.

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
