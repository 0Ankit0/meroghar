# MeroGhar

A full-stack property rental platform built with FastAPI, Next.js, and Flutter, with feature flags, pluggable providers, and capability-driven clients.

The project is designed so that most customization starts with configuration and capability discovery, not code forks. The backend is the source of truth for enabled modules, active providers, public runtime settings, and operational behavior.

## What It Includes

- Config-driven modules for auth, multi-tenancy, notifications, websockets, finance, analytics, and social auth.
- Communications provider switching for email, push, and SMS.
- Runtime discovery APIs for clients and operators.
- Database-backed runtime settings overrides for safe operational config.
- Centralized operational config for cookies, hosts, rate limits, logging, observability, storage, Celery, and websocket behavior.
- Web and mobile clients that adapt to enabled modules and configured providers.
- A full `docs/` system modeled on the Project-Ideas documentation structure.

## Quick Start

1. Review [docs/README.md](docs/README.md).
2. Read [docs/requirements/requirements.md](docs/requirements/requirements.md), [docs/requirements/mvp-backlog-matrix.md](docs/requirements/mvp-backlog-matrix.md), [docs/implementation/dependency-ordered-execution-plan.md](docs/implementation/dependency-ordered-execution-plan.md), and [TEMPLATE_RELEASE_CHECKLIST.md](TEMPLATE_RELEASE_CHECKLIST.md).
3. Run `make setup`.
4. Start local dependencies with `make infra-up`.
5. Run migrations with `make backend-migrate`.
6. Start the apps with `make backend-dev`, `make frontend-dev`, and `make mobile-dev`.
7. Verify the baseline with `make health-check` and `make ci`.

## Validation

- Backend lint and tests: `make backend-lint` and `make backend-test`
- Frontend lint, typecheck, tests, and build: `make frontend-lint` and `make frontend-test`
- Mobile analyze and tests: `make mobile-lint` and `make mobile-test`
- Docs validation: `make docs`
- Full local quality bar: `make ci`
