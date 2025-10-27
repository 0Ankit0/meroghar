<!--
SYNC IMPACT REPORT
==================
Version Change: INITIAL → 1.0.0
Rationale: Initial constitution creation for Meroghar project

Principles Defined:
- I. Data Privacy & Security
- II. Role-Based Access Control
- III. Offline-First Architecture
- IV. Mobile-Responsive Design
- V. Financial Data Accuracy & Audit Trails
- VI. Multi-Tenant Data Isolation
- VII. Test-Driven Development
- VIII. API-First Design

Sections Added:
- Core Principles (8 principles)
- Technology Stack Requirements
- Development Workflow
- Governance

Templates Status:
- ✅ spec-template.md - Aligned with security and testing principles
- ✅ plan-template.md - Aligned with API-first and architecture principles
- ✅ tasks-template.md - Aligned with TDD and testing requirements
- ✅ checklist-template.md - Aligned with quality gates
- ✅ agent-file-template.md - No changes required

Follow-up TODOs: None - all placeholders filled

Next Steps:
- Review constitution with team
- Begin feature specifications using /speckit.specify
- Ensure all implementations adhere to these principles
-->

# Meroghar Constitution

## Core Principles

### I. Data Privacy & Security

All tenant information MUST be protected with industry-standard security measures:

- **Encryption at Rest**: All sensitive data (passwords, personal information, financial records) MUST be encrypted in the database using AES-256 or equivalent
- **Encryption in Transit**: All API communications MUST use HTTPS/TLS 1.3 or higher
- **Password Security**: User passwords MUST be hashed using bcrypt with minimum cost factor of 12
- **PII Protection**: Personally Identifiable Information (PII) MUST NOT appear in logs, error messages, or debugging output
- **Data Minimization**: Collect only necessary tenant data; justify any additional fields
- **Secure Storage**: Mobile apps MUST use platform-secure storage (flutter_secure_storage) for tokens and sensitive data
- **Audit Logging**: All access to tenant financial data and PII MUST be logged with user, timestamp, and action

**Rationale**: Meroghar handles sensitive tenant financial and personal information. Any breach would violate tenant trust and potentially legal obligations. Security must be built-in from day one, not added later.

### II. Role-Based Access Control (RBAC)

Access to data and functionality MUST be strictly controlled by user role:

- **Three Roles Only**: Owner, Intermediary, Tenant - no role hierarchy or inheritance
- **Server-Side Enforcement**: ALL permission checks MUST occur on the backend API; client-side checks are for UX only
- **Principle of Least Privilege**: Users receive minimum permissions required for their role
- **Role-Specific APIs**: API endpoints MUST validate role permissions before executing any operation
- **Data Isolation**:
  - Tenants see ONLY their own profile and payment data
  - Intermediaries see ONLY their managed tenants, not other intermediaries' data
  - Owners see ALL data across the entire property
- **Immutable Roles**: Role changes require explicit authorization and audit trail
- **Row-Level Security**: Database queries MUST filter by role automatically (PostgreSQL RLS)

**Rationale**: Mixed-role access creates security vulnerabilities and data leaks. Clear role boundaries prevent intermediaries from accessing each other's data and ensure tenants cannot view others' information.

### III. Offline-First Architecture

The mobile application MUST function fully without internet connectivity:

- **Local-First Data**: All data MUST be stored locally on the device (SQLite)
- **Sync, Don't Reload**: Synchronization updates differences, never full data replacement
- **Conflict Resolution**: Implement deterministic conflict resolution (last-write-wins with timestamp)
- **Queue Failed Operations**: Failed syncs MUST be queued and retried with exponential backoff
- **Graceful Degradation**: Features that require server (e.g., new tenant creation by owner) MUST clearly indicate online requirement
- **Sync Indicators**: Users MUST see clear status indicators (synced, pending, error, syncing)
- **Data Validation**: Validate data integrity before sync to prevent corruption
- **Background Sync**: Use platform background services (WorkManager/BackgroundFetch) for automatic sync

**Rationale**: Internet connectivity in rental properties may be unreliable. Intermediaries need to record payments and bills immediately, regardless of network status. Offline capability is not optional.

### IV. Mobile-Responsive Design

The Flutter application MUST provide excellent UX across all device sizes:

- **Responsive Layouts**: Use Flutter's responsive widgets (MediaQuery, LayoutBuilder) for all screens
- **Touch Targets**: Minimum 48x48 logical pixels for all interactive elements
- **Readable Text**: Minimum 14sp font size; support dynamic text scaling
- **Fast Performance**:
  - App startup: < 3 seconds
  - Screen transitions: < 300ms
  - List scrolling: 60 FPS minimum
- **Accessibility**: Support screen readers, high contrast, and font scaling
- **Platform Conventions**: Follow Material Design guidelines; respect platform-specific patterns
- **Offline Indicators**: Clear visual feedback for network status
- **Error Handling**: User-friendly error messages with actionable recovery steps

**Rationale**: Intermediaries and tenants access Meroghar primarily on mobile devices. Poor mobile UX leads to user frustration and reduced adoption. Desktop/web are secondary concerns.

### V. Financial Data Accuracy & Audit Trails

All financial calculations and transactions MUST be accurate and traceable:

- **Decimal Precision**: Use DECIMAL/NUMERIC types (never FLOAT) for all monetary values
- **Currency Handling**: Store amounts in smallest unit (e.g., cents) to avoid rounding errors
- **Immutable Records**: Payment and bill records MUST NOT be deleted, only marked as void/cancelled
- **Audit Trail**: Every financial transaction MUST record:
  - Amount, date, time (with timezone)
  - User who created/modified the record
  - Original and modified values (if edited)
  - Reason for void/cancellation if applicable
- **Balance Calculations**: Tenant balances MUST be calculated from transaction history, not stored as mutable values
- **Reconciliation**: Provide reports comparing calculated vs. expected balances
- **Bill Division Accuracy**: Division algorithms MUST handle remainders deterministically (e.g., assign extra cent to first tenant)
- **Receipt Generation**: All payments MUST generate timestamped, immutable receipts

**Rationale**: Financial errors destroy trust and create legal liability. Audit trails are essential for dispute resolution and accounting. "Soft deletes" and immutability prevent data loss.

### VI. Multi-Tenant Data Isolation

Tenant data MUST be logically isolated to prevent cross-tenant data leaks:

- **Scoped Queries**: ALL database queries MUST include tenant/property scope filters
- **No Global Queries**: Queries like `SELECT * FROM tenants` without filtering are FORBIDDEN
- **API Route Scoping**: API routes MUST validate that requested resources belong to authenticated user's scope
- **Test Isolation**: Integration tests MUST verify no cross-tenant data leakage
- **Cascade Rules**: Deleting intermediary MUST NOT delete their tenant data (reassignment required)
- **Property Scoping**: Data belongs to property → intermediary → tenant hierarchy
- **Shared Resources**: Bills and expenses scoped to property; payments scoped to tenant
- **Error Messages**: MUST NOT reveal existence of data outside user's scope (404 for both "not found" and "not authorized")

**Rationale**: Multi-tenant systems are prone to authorization bugs that leak data across tenant boundaries. Explicit scoping in every query prevents these vulnerabilities.

### VII. Test-Driven Development (NON-NEGOTIABLE)

All implementation MUST follow strict test-first development:

- **No Code Before Tests**: Implementation code MUST NOT be written until tests exist and fail
- **Red-Green-Refactor**: Mandatory cycle:
  1. Write failing test (Red)
  2. Write minimum code to pass (Green)
  3. Refactor for quality (Refactor)
- **Test Types Required**:
  - **Unit Tests**: Business logic, calculations, utilities
  - **Integration Tests**: API endpoints, database operations, authentication flows
  - **Contract Tests**: API request/response validation against contracts
  - **E2E Tests**: Critical user flows (login → create tenant → record payment)
- **Test Coverage**: Minimum 80% code coverage for backend; 70% for frontend
- **Real Dependencies**: Prefer real database over mocks in integration tests
- **Test Databases**: Use containerized PostgreSQL for consistent test environments
- **Continuous Testing**: Tests MUST run on every commit (CI/CD pipeline)
- **Test Documentation**: Tests serve as executable documentation of feature behavior

**Rationale**: TDD prevents bugs, improves design, and provides living documentation. Skipping tests creates technical debt that compounds over time. Financial software demands high reliability.

### VIII. API-First Design

Backend services MUST be designed as APIs before implementation:

- **Contract-First**: Define OpenAPI/JSON schemas before writing API code
- **API Contracts**: Document all endpoints with:
  - HTTP method, path, parameters
  - Request/response schemas (JSON)
  - Authentication requirements
  - Error responses
  - Example requests/responses
- **Versioning**: API paths MUST include version (`/api/v1/tenants`)
- **RESTful Design**: Follow REST principles (resources, HTTP verbs, status codes)
- **Error Standards**: Use consistent error format:
  ```json
  {
    "error": "error_code",
    "message": "Human-readable message",
    "details": {}
  }
  ```
- **Authentication**: JWT tokens in Authorization header for all protected endpoints
- **Rate Limiting**: Implement rate limits to prevent abuse
- **API Documentation**: Auto-generate docs from OpenAPI specs (Swagger UI)
- **Breaking Changes**: MAJOR version bump for incompatible changes; maintain old version during transition

**Rationale**: API-first design enables parallel frontend/backend development, creates clear contracts, and ensures consistency. Mobile apps depend entirely on stable, well-documented APIs.

## Technology Stack Requirements

The following technology choices are mandated for architectural consistency:

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (for async support and auto-generated OpenAPI docs)
- **Database**: PostgreSQL 14+ (with Row-Level Security enabled)
- **ORM**: SQLAlchemy 2.0+ with Alembic for migrations
- **Authentication**: JWT tokens (PyJWT library)
- **Testing**: pytest with pytest-asyncio
- **API Validation**: Pydantic models for request/response validation
- **Task Queue**: Celery with Redis (for background jobs like recurring bills)

### Frontend
- **Framework**: Flutter 3.10+
- **State Management**: Provider pattern (or Riverpod for complex state)
- **Local Storage**: SQLite with sqflite package
- **Secure Storage**: flutter_secure_storage for tokens
- **HTTP Client**: Dio with interceptors for auth and error handling
- **Charts**: fl_chart for financial visualizations
- **Excel Export**: excel package for generating spreadsheets
- **Testing**: flutter_test with integration_test

### Infrastructure
- **Version Control**: Git with feature branch workflow
- **CI/CD**: GitHub Actions or GitLab CI
- **Containerization**: Docker for backend services
- **API Documentation**: Swagger UI auto-generated from OpenAPI specs

## Development Workflow

All development MUST follow this structured process:

### 1. Specification Phase
- Use `/speckit.specify` to create feature specification
- Define user stories with acceptance criteria
- Identify edge cases and constraints
- Use `/speckit.clarify` to resolve ambiguities

### 2. Planning Phase
- Use `/speckit.plan` to create technical implementation plan
- Define database schema changes
- Document API contracts (request/response)
- Research library/technology choices
- Identify performance and security requirements

### 3. Task Breakdown Phase
- Use `/speckit.tasks` to generate executable task list
- Order tasks: contracts → tests → implementation
- Mark parallelizable tasks with [P]
- Define clear acceptance criteria per task

### 4. Implementation Phase
- **Test First**: Write failing tests before implementation
- **Implement**: Write minimum code to pass tests
- **Refactor**: Improve code quality while keeping tests green
- **Review**: Code review checks constitution compliance
- **Document**: Update API docs and inline comments

### 5. Quality Assurance Phase
- Run full test suite (unit, integration, e2e)
- Use `/speckit.analyze` for cross-artifact consistency checks
- Perform security review (OWASP checklist)
- Test offline/sync scenarios manually
- Validate RBAC enforcement across all endpoints

### 6. Deployment Phase
- Database migrations applied (with rollback plan)
- API versioning maintained for breaking changes
- Mobile app updates backward-compatible with API
- Monitoring and logging configured
- Backup verified before production deployment

## Governance

This constitution is the supreme governing document for Meroghar development. All code, architecture decisions, and processes MUST comply with these principles.

### Enforcement
- **Code Reviews**: All pull requests MUST be reviewed for constitution compliance
- **CI/CD Gates**: Automated checks enforce test coverage, linting, and security scans
- **Architecture Reviews**: Major changes require explicit constitution alignment justification
- **Exceptions**: Any deviation from principles MUST be documented with:
  - Rationale for exception
  - Risk assessment
  - Plan to return to compliance
  - Approval from project maintainer

### Amendment Process
Modifications to this constitution require:
1. **Proposal**: Document proposed change with rationale
2. **Impact Assessment**: Analyze effect on existing code and architecture
3. **Team Review**: Discuss and approve change with all maintainers
4. **Version Update**: Follow semantic versioning:
   - **MAJOR**: Principle removal or incompatible redefinition
   - **MINOR**: New principle added or substantial expansion
   - **PATCH**: Clarifications, wording improvements, typos
5. **Migration Plan**: Define steps to bring existing code into compliance
6. **Documentation**: Update all templates and guidance files

### Versioning Policy
- Constitution changes are tracked in git history
- Each amendment appends to Sync Impact Report
- Breaking changes require migration guide for active features

### Compliance Review
- **Monthly**: Review constitution compliance across active features
- **Quarterly**: Architecture review to identify technical debt
- **Per Feature**: Use `/speckit.checklist` to generate compliance checklist
- **Violations**: Document, prioritize, and remediate any non-compliance

**Version**: 1.0.0 | **Ratified**: 2025-10-26 | **Last Amended**: 2025-10-26
