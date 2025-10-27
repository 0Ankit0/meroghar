# Meroghar - House Rental Management System
## Spec-Kit Command Reference

This document defines the `/speckit.*` commands for the Meroghar house rental management system, following the [Spec-Driven Development methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md).

---

## 🚀 Quick Start - Copy & Paste Commands

Use these commands in sequence to build the complete Meroghar system:

### 1. Create Constitution
```
/speckit.constitution Create principles for Meroghar focusing on:
- Data privacy and security for tenant information
- Role-based access control (Owner/Intermediary/Tenant)
- Offline-first architecture with sync capabilities
- Mobile-responsive design principles
- Financial data accuracy and audit trails
- Multi-tenant data isolation
- Test-driven development with integration tests
- API-first design for backend services
```

### 2. Create Complete System Specification
```
/speckit.specify Build a comprehensive house rental management system with the following features:

FEATURE 1: User Management & Authentication
- Three user types exist: Owner, Intermediary, and Tenant
- Owners and Intermediaries can create Tenant accounts
- Each Tenant receives credentials to access their personal dashboard
- Role-based permissions control what each user can view and modify
- Owners can view all data across all tenants and intermediaries
- Intermediaries can view all their managed tenants but not other intermediaries
- Tenants can only view their own profile and payment information

FEATURE 2: Tenant Profile Management
- Basic information: name, mobile number, start date
- Financial summary: total paid, remaining balance, payment history
- Occupancy details: time stayed in the house (calculated from start date)
- Utility consumption: electricity units consumed with configurable pricing
- Water bill tracking with division among tenants
- Profile cards displayed in a grid/list view
- Click on card to view detailed tenant information
- Search and filter capabilities for finding tenants

FEATURE 3: Rent & Payment Tracking
- Intermediaries track rent collection from all tenants
- Intermediaries record their own rent payments if applicable
- System tracks money sent to owners and calculates remaining balance
- Payment history is maintained with dates and amounts
- Overdue payments are highlighted with visual indicators
- Generate payment receipts for tenants
- Support multiple payment methods (cash, bank transfer, digital payment)

FEATURE 4: Bill Management & Division
- Allows adding monthly bills (electricity, water, maintenance, etc.)
- Supports percentage-based division among tenants
- Supports fixed amount division methods
- Handles recurring bills with automatic monthly creation
- Tracks which tenants have paid their share
- Calculates remaining amounts per tenant
- Allows custom division rules for different bill types
- Shows bill history and trends over time

FEATURE 5: Maintenance & Emergency Expense Tracking
- Recording maintenance costs (painting, repairs, cleaning)
- Emergency fix expenses with descriptions and dates
- Categorizing expenses by type
- Uploading receipts or photos as evidence
- Tracking which party paid (Owner/Intermediary/Tenant)
- Expense approval workflow if needed
- Monthly and yearly expense reports
- Cost allocation and reimbursement tracking

FEATURE 6: Rent Increment Management
- Configure percentage-based or fixed amount increments
- Set increment schedule (every N years)
- Automatic calculation on tenant anniversary
- Manual override capability for special cases
- Notification to tenants before increment takes effect
- Historical rent rate tracking per tenant
- Preview future rent amounts

FEATURE 7: Data Synchronization
- Three sync modes: no sync, periodic automatic sync, manual sync
- Sync mobile app data with PostgreSQL server
- Conflict resolution for simultaneous edits
- Offline capability with local data storage
- Sync status indicators (synced, pending, failed)
- Retry mechanism for failed syncs
- Data validation before sync to prevent corruption
- Sync history and logs for troubleshooting

FEATURE 8: Excel Export Functionality
- Intermediaries can export all tenant data to Excel
- Export includes: tenant details, payment status, bills, outstanding amounts
- Tenants can export their individual payment history
- Customizable export templates
- Include date range filters for exports
- Generate summary sheets with totals and statistics
- Support for PDF export as alternative format

FEATURE 9: Mobile Messaging System
- Sends SMS/WhatsApp messages to tenants
- Supports message templates (rent reminders, bill notifications)
- Configurable delivery schedules (immediate, scheduled, recurring)
- Manual message sending for custom communications
- Bulk messaging to multiple tenants
- Message delivery status tracking
- Message history per tenant
- Configurable intervals in settings (daily, weekly, monthly)
- Personalized message variables (tenant name, amount due, etc.)

FEATURE 10: Settings & Configuration
- Electricity rate configuration (price per unit)
- Water bill calculation settings
- Default bill division methods
- Sync preferences (mode, frequency, auto-retry)
- Notification preferences
- Currency and date format settings
- Backup and restore options
- User profile management
- System theme (light/dark mode)

FEATURE 11: Document Storage & Management
- Upload and store lease agreements (PDF, images)
- Attach documents to tenant profiles
- Document versioning and history tracking
- Secure document access based on user role
- Document expiration reminders (lease renewal dates)
- Support for multiple document types (ID proof, agreements, NOCs)
- Document sharing with specific users
- Cloud storage integration for document backup
- Document categories and tagging
- Search documents by tenant, date, or type

FEATURE 12: Online Payment Gateway Integration
- Integrate payment gateways (Stripe, Razorpay, PayPal, etc.)
- Tenants can pay rent directly through the app
- Support for multiple payment methods (cards, UPI, wallets)
- Automatic payment receipt generation
- Payment confirmation notifications
- Recurring payment setup for monthly rent
- Payment history with transaction IDs
- Refund and chargeback handling
- Payment gateway fee tracking
- Secure PCI-DSS compliant payment processing
- Multi-currency support
- Payment links generation for sharing

FEATURE 13: Analytics Dashboard with Charts
- Interactive dashboard for Owners and Intermediaries
- Rent collection trends over time (line/bar charts)
- Payment status overview (paid/pending/overdue)
- Occupancy rates and vacancy analytics
- Bill payment patterns and averages
- Expense breakdown by category (pie charts)
- Revenue vs. expenses comparison
- Tenant payment behavior analysis
- Year-over-year comparison charts
- Property-wise performance metrics
- Customizable date ranges for reports
- Export analytics data to PDF/Excel
- Real-time data updates
- Drill-down capability for detailed insights

FEATURE 14: Mobile Push Notifications
- Real-time push notifications for important events
- Rent payment reminders before due date
- Bill allocation notifications to tenants
- Payment confirmation alerts
- Overdue payment warnings
- New message notifications
- Document upload/update alerts
- Lease expiration reminders
- Maintenance request updates
- Customizable notification preferences per user
- Quiet hours settings (no notifications during sleep time)
- Notification history and archive
- In-app notification center
- Badge counts for unread notifications

FEATURE 15: Multi-Language Support
- Support for multiple languages (English, Hindi, Spanish, etc.)
- User can select preferred language in settings
- All UI text translated based on language preference
- RTL (Right-to-Left) support for Arabic, Hebrew, etc.
- Date and number formatting based on locale
- Currency symbols based on region
- Language-specific message templates
- Fallback to English for untranslated content
- Translation management for easy updates
- Voice/text input in native language

FEATURE 16: Advanced Reporting & Tax Statements
- Generate comprehensive financial reports
- Annual rent income statements for tax filing
- Expense deduction reports for property owners
- Tenant-wise income breakdown
- GST/VAT calculation and reports
- Form generation (e.g., IRS Form 1099, local tax forms)
- Profit and loss statements
- Cash flow reports
- Comparative reports (month-over-month, year-over-year)
- Customizable report templates
- Scheduled report generation and email delivery
- Report sharing with accountants or tax professionals
- Audit trail reports for compliance
- Depreciation calculation for property assets
- Property valuation tracking
```

### 3. Clarify Requirements (Optional but Recommended)
```
/speckit.clarify
```

### 4. Create Technical Implementation Plan
```
/speckit.plan Implement Meroghar with the following technical architecture:

BACKEND ARCHITECTURE:
- Python FastAPI for REST API endpoints with async support
- PostgreSQL 14+ with Row-Level Security for multi-tenant isolation
- SQLAlchemy 2.0+ ORM with Alembic for database migrations
- JWT tokens for stateless authentication with bcrypt password hashing
- Pydantic models for request/response validation
- Role-based middleware for endpoint protection
- Celery with Redis for background jobs (recurring bills, scheduled messages)
- CRON jobs for automatic recurring bill creation

FRONTEND ARCHITECTURE:
- Flutter 3.10+ for cross-platform mobile development
- Provider pattern (or Riverpod) for state management
- SQLite with sqflite for local mobile storage
- flutter_secure_storage for secure token storage
- Dio HTTP client with interceptors for auth and error handling
- Background sync using WorkManager (Android) / BackgroundFetch (iOS)
- Firebase Cloud Messaging for push notifications

AUTHENTICATION & SECURITY:
- JWT token validation on every API request
- Server-side role-based permission enforcement
- PostgreSQL Row-Level Security for data isolation
- HTTPS/TLS 1.3 for all API communication
- Certificate pinning for mobile API calls
- Encrypted local database on mobile
- PCI-DSS compliant payment processing

DATA SYNCHRONIZATION:
- Offline-first architecture with local SQLite storage
- Conflict resolution using last-write-wins with timestamp comparison
- Exponential backoff for retry logic on failed syncs
- API versioning (/api/v1/) for backward compatibility
- Database transactions for atomic operations
- Sync status tracking and error logging

DATABASE DESIGN:
- Core tables: users, properties, tenants, payments, bills, bill_allocations
- Supporting tables: expenses, messages, sync_logs, documents, notifications
- Payment gateway tables: transactions, payment_methods, refunds
- Analytics tables: analytics_cache, report_templates
- DECIMAL type for all monetary values (no FLOAT)
- Immutable financial records (soft deletes only)
- Indexed foreign keys for performance
- Audit trail columns (created_at, updated_at, created_by)
- JSONB columns for flexible metadata storage

BILL MANAGEMENT:
- PostgreSQL tables: bills, bill_items, bill_payments, recurring_bills
- Python decimal type for accurate financial calculations
- Deterministic remainder handling in bill division
- Flutter DataTable for bill display
- fl_chart library for financial visualizations

EXPORT FUNCTIONALITY:
- openpyxl (Python) for server-side Excel generation
- excel package (Flutter) for client-side exports
- ReportLab (Python) for PDF generation
- Customizable export templates with date range filters
- Background job processing for large exports
- Email delivery of generated reports

MESSAGING SYSTEM:
- SMS gateway integration (Twilio, AWS SNS, or local provider)
- WhatsApp Business API for message delivery
- Message queue using Celery for scheduled sending
- Jinja2 template engine for personalized messages
- Delivery status tracking and retry mechanism
- Rate limiting to prevent spam

DOCUMENT STORAGE:
- AWS S3 or equivalent cloud storage for document files
- boto3 library for S3 integration
- File upload with virus scanning (ClamAV)
- Document encryption at rest
- Presigned URLs for secure document access
- Document versioning with S3 versioning
- Thumbnail generation for image documents
- Full-text search using PostgreSQL full-text search
- Document retention policies and auto-deletion

PAYMENT GATEWAY INTEGRATION:
- Stripe SDK for payment processing
- Razorpay SDK for India market
- PayPal REST API for international payments
- Webhook handlers for payment confirmations
- PCI-DSS compliant tokenization
- 3D Secure authentication support
- Recurring payment subscriptions
- Payment reconciliation engine
- Multi-currency support with exchange rate API
- Refund and chargeback workflows

ANALYTICS & REPORTING:
- PostgreSQL materialized views for fast analytics queries
- Pandas for data analysis and aggregation
- Plotly or Chart.js for chart generation
- Scheduled report generation using Celery
- Report caching with Redis
- Real-time analytics using WebSockets
- Data export to CSV/Excel for further analysis
- Custom SQL queries for advanced reporting
- Dashboard widgets with customizable layouts

PUSH NOTIFICATIONS:
- Firebase Cloud Messaging (FCM) for Android/iOS
- APNs (Apple Push Notification service) for iOS
- Notification scheduling and batching
- Topic-based subscriptions for broadcast messages
- Device token management
- Notification analytics and delivery tracking
- Rich notifications with actions
- Silent notifications for data sync triggers

INTERNATIONALIZATION (i18n):
- Flutter intl package for UI translations
- JSON files for translation strings
- Language detection based on device locale
- Runtime language switching
- Date/time formatting with intl package
- Number and currency formatting per locale
- RTL layout support using Directionality widget
- Translation management system for easy updates
- Fallback language mechanism

TAX & COMPLIANCE REPORTING:
- Tax calculation engine with configurable rules
- Form generation using ReportLab templates
- GST/VAT calculation by region
- TDS (Tax Deducted at Source) tracking
- Financial year configuration
- Tax report scheduling and auto-generation
- Integration with accounting software (optional)
- Audit trail for all financial transactions
- Depreciation calculation using straight-line/declining balance methods
- Property valuation tracking with historical data

TESTING STRATEGY:
- pytest with pytest-asyncio for backend tests
- flutter_test with integration_test for mobile tests
- Contract tests for API endpoints
- Integration tests with real PostgreSQL (Docker containers)
- Load testing with Locust for performance validation
- Security testing with OWASP ZAP
- Minimum 80% backend coverage, 70% frontend coverage
- E2E tests for critical user flows
- Payment gateway testing in sandbox mode

DEPLOYMENT:
- Docker containers for backend services
- PostgreSQL with automated daily backups
- Redis for caching and message queuing
- Nginx as reverse proxy and load balancer
- Swagger UI for API documentation
- GitHub Actions or GitLab CI for CI/CD
- Environment-based configuration (.env files)
- Blue-green deployment for zero downtime
- Monitoring with Prometheus and Grafana
- Log aggregation with ELK stack or CloudWatch
- CDN for document storage and static assets
```

### 5. Generate Task List
```
/speckit.tasks
```

### 6. Analyze Consistency (Optional)
```
/speckit.analyze
```

### 7. Create Quality Checklist
```
/speckit.checklist Create comprehensive validation checklist for:

DATA PRIVACY COMPLIANCE:
- Tenant personal information encrypted at rest (AES-256)
- All API communications use HTTPS/TLS 1.3
- Passwords hashed with bcrypt (cost factor 12+)
- No PII in logs, error messages, or debugging output
- Secure token storage on mobile (flutter_secure_storage)
- Audit logs for all financial data access

FINANCIAL ACCURACY:
- All monetary values use DECIMAL/NUMERIC types (no FLOAT)
- Payment calculations verified with unit tests
- Bill division algorithms handle remainders correctly
- Balance calculations derive from transaction history
- Immutable financial records (soft deletes only)
- Receipt generation tested for all payment types
- Currency rounding follows consistent rules

ROLE-BASED ACCESS ENFORCEMENT:
- Server-side permission checks on all endpoints
- Tenants cannot access other tenants' data
- Intermediaries cannot see other intermediaries' data
- Owners have full visibility across all data
- Row-level security implemented in PostgreSQL
- API returns 404 for unauthorized resource access
- JWT token validation on every request

SYNC RELIABILITY:
- Offline mode fully functional without internet
- Sync conflict resolution tested with edge cases
- Failed syncs queued with exponential backoff
- Data validation before sync prevents corruption
- Multiple device sync tested for data consistency
- Network interruption handling verified
- Sync status indicators work correctly

MOBILE UX:
- App loads in under 3 seconds
- Screen transitions under 300ms
- Touch targets minimum 48x48 pixels
- Text readable at minimum 14sp font size
- Responsive layouts on all device sizes
- 60 FPS scrolling performance maintained
- Offline indicators clearly visible
- Error messages user-friendly with recovery steps

TESTING COVERAGE:
- Backend unit test coverage ≥80%
- Frontend unit test coverage ≥70%
- All API endpoints have contract tests
- Critical user flows have E2E tests
- Integration tests use real database
- Payment calculations have comprehensive tests
- Bill division edge cases covered

SECURITY AUDIT:
- Input sanitization on all user inputs
- SQL injection prevention verified
- XSS protection implemented
- Rate limiting configured on endpoints
- Certificate pinning on mobile
- Biometric authentication option available
- Auto-logout after inactivity period
- Secure session management

PERFORMANCE REQUIREMENTS:
- Authentication response < 500ms
- Tenant list load < 1s for 100 tenants
- Payment recording < 300ms
- Bill calculations < 2s for complex divisions
- Sync operation < 5s for typical dataset
- Excel export < 10s for 1 year data
- Database indexes on all foreign keys
```

### 8. Implement Features
```
/speckit.implement
```

---

## System Overview

**Meroghar** is a comprehensive house rental management system designed to streamline rent collection, tenant management, and financial tracking for property owners and intermediaries.

### Technology Stack
- **Backend**: Python + PostgreSQL
- **Frontend**: Flutter
- **Architecture**: Client-server with RESTful APIs

### User Types
1. **Owner** - Property owner with full visibility and control
2. **Intermediary** - Property manager handling day-to-day operations
3. **Tenant** - Renter with limited access to personal information

---

## Available Commands

### Core Workflow Commands

#### `/speckit.constitution`
Create or update the project's governing principles and development guidelines.

**Usage:**
```
/speckit.constitution Create principles for Meroghar focusing on:
- Data privacy and security for tenant information
- Role-based access control (Owner/Intermediary/Tenant)
- Offline-first architecture with sync capabilities
- Mobile-responsive design principles
- Financial data accuracy and audit trails
- Multi-tenant data isolation
- Test-driven development with integration tests
- API-first design for backend services
```

**Output:** Creates `memory/constitution.md` with project-specific architectural principles.

---

#### `/speckit.specify`
Define feature requirements focusing on WHAT and WHY, not implementation details.

**Usage - Complete Meroghar System Specification:**

```
/speckit.specify Build a comprehensive house rental management system with the following features:

FEATURE 1: User Management & Authentication
- Three user types exist: Owner, Intermediary, and Tenant
- Owners and Intermediaries can create Tenant accounts
- Each Tenant receives credentials to access their personal dashboard
- Role-based permissions control what each user can view and modify
- Owners can view all data across all tenants and intermediaries
- Intermediaries can view all their managed tenants but not other intermediaries
- Tenants can only view their own profile and payment information

FEATURE 2: Tenant Profile Management
- Basic information: name, mobile number, start date
- Financial summary: total paid, remaining balance, payment history
- Occupancy details: time stayed in the house (calculated from start date)
- Utility consumption: electricity units consumed with configurable pricing
- Water bill tracking with division among tenants
- Profile cards displayed in a grid/list view
- Click on card to view detailed tenant information
- Search and filter capabilities for finding tenants

FEATURE 3: Rent & Payment Tracking
- Intermediaries track rent collection from all tenants
- Intermediaries record their own rent payments if applicable
- System tracks money sent to owners and calculates remaining balance
- Payment history is maintained with dates and amounts
- Overdue payments are highlighted with visual indicators
- Generate payment receipts for tenants
- Support multiple payment methods (cash, bank transfer, digital payment)

FEATURE 4: Bill Management & Division
- Allows adding monthly bills (electricity, water, maintenance, etc.)
- Supports percentage-based division among tenants
- Supports fixed amount division methods
- Handles recurring bills with automatic monthly creation
- Tracks which tenants have paid their share
- Calculates remaining amounts per tenant
- Allows custom division rules for different bill types
- Shows bill history and trends over time

FEATURE 5: Maintenance & Emergency Expense Tracking
- Recording maintenance costs (painting, repairs, cleaning)
- Emergency fix expenses with descriptions and dates
- Categorizing expenses by type
- Uploading receipts or photos as evidence
- Tracking which party paid (Owner/Intermediary/Tenant)
- Expense approval workflow if needed
- Monthly and yearly expense reports
- Cost allocation and reimbursement tracking

FEATURE 6: Rent Increment Management
- Configure percentage-based or fixed amount increments
- Set increment schedule (every N years)
- Automatic calculation on tenant anniversary
- Manual override capability for special cases
- Notification to tenants before increment takes effect
- Historical rent rate tracking per tenant
- Preview future rent amounts

FEATURE 7: Data Synchronization
- Three sync modes: no sync, periodic automatic sync, manual sync
- Sync mobile app data with PostgreSQL server
- Conflict resolution for simultaneous edits
- Offline capability with local data storage
- Sync status indicators (synced, pending, failed)
- Retry mechanism for failed syncs
- Data validation before sync to prevent corruption
- Sync history and logs for troubleshooting

FEATURE 8: Excel Export Functionality
- Intermediaries can export all tenant data to Excel
- Export includes: tenant details, payment status, bills, outstanding amounts
- Tenants can export their individual payment history
- Customizable export templates
- Include date range filters for exports
- Generate summary sheets with totals and statistics
- Support for PDF export as alternative format

FEATURE 9: Mobile Messaging System
- Sends SMS/WhatsApp messages to tenants
- Supports message templates (rent reminders, bill notifications)
- Configurable delivery schedules (immediate, scheduled, recurring)
- Manual message sending for custom communications
- Bulk messaging to multiple tenants
- Message delivery status tracking
- Message history per tenant
- Configurable intervals in settings (daily, weekly, monthly)
- Personalized message variables (tenant name, amount due, etc.)

FEATURE 10: Settings & Configuration
- Electricity rate configuration (price per unit)
- Water bill calculation settings
- Default bill division methods
- Sync preferences (mode, frequency, auto-retry)
- Notification preferences
- Currency and date format settings
- Backup and restore options
- User profile management
- System theme (light/dark mode)

FEATURE 11: Document Storage & Management
- Upload and store lease agreements (PDF, images)
- Attach documents to tenant profiles
- Document versioning and history tracking
- Secure document access based on user role
- Document expiration reminders (lease renewal dates)
- Support for multiple document types (ID proof, agreements, NOCs)
- Document sharing with specific users
- Cloud storage integration for document backup
- Document categories and tagging
- Search documents by tenant, date, or type

FEATURE 12: Online Payment Gateway Integration
- Integrate payment gateways (Stripe, Razorpay, PayPal, etc.)
- Tenants can pay rent directly through the app
- Support for multiple payment methods (cards, UPI, wallets)
- Automatic payment receipt generation
- Payment confirmation notifications
- Recurring payment setup for monthly rent
- Payment history with transaction IDs
- Refund and chargeback handling
- Payment gateway fee tracking
- Secure PCI-DSS compliant payment processing
- Multi-currency support
- Payment links generation for sharing

FEATURE 13: Analytics Dashboard with Charts
- Interactive dashboard for Owners and Intermediaries
- Rent collection trends over time (line/bar charts)
- Payment status overview (paid/pending/overdue)
- Occupancy rates and vacancy analytics
- Bill payment patterns and averages
- Expense breakdown by category (pie charts)
- Revenue vs. expenses comparison
- Tenant payment behavior analysis
- Year-over-year comparison charts
- Property-wise performance metrics
- Customizable date ranges for reports
- Export analytics data to PDF/Excel
- Real-time data updates
- Drill-down capability for detailed insights

FEATURE 14: Mobile Push Notifications
- Real-time push notifications for important events
- Rent payment reminders before due date
- Bill allocation notifications to tenants
- Payment confirmation alerts
- Overdue payment warnings
- New message notifications
- Document upload/update alerts
- Lease expiration reminders
- Maintenance request updates
- Customizable notification preferences per user
- Quiet hours settings (no notifications during sleep time)
- Notification history and archive
- In-app notification center
- Badge counts for unread notifications

FEATURE 15: Multi-Language Support
- Support for multiple languages (English, Hindi, Spanish, etc.)
- User can select preferred language in settings
- All UI text translated based on language preference
- RTL (Right-to-Left) support for Arabic, Hebrew, etc.
- Date and number formatting based on locale
- Currency symbols based on region
- Language-specific message templates
- Fallback to English for untranslated content
- Translation management for easy updates
- Voice/text input in native language

FEATURE 16: Advanced Reporting & Tax Statements
- Generate comprehensive financial reports
- Annual rent income statements for tax filing
- Expense deduction reports for property owners
- Tenant-wise income breakdown
- GST/VAT calculation and reports
- Form generation (e.g., IRS Form 1099, local tax forms)
- Profit and loss statements
- Cash flow reports
- Comparative reports (month-over-month, year-over-year)
- Customizable report templates
- Scheduled report generation and email delivery
- Report sharing with accountants or tax professionals
- Audit trail reports for compliance
- Depreciation calculation for property assets
- Property valuation tracking
```

**Output:** Creates `specs/[feature-number]-[feature-name]/spec.md` with structured requirements, user stories, and acceptance criteria.

---

#### `/speckit.plan`
Generate technical implementation plans with architecture and technology choices.

**Usage - Complete Technical Plan for Meroghar:**

```
/speckit.plan Implement Meroghar with the following technical architecture:

BACKEND ARCHITECTURE:
- Python FastAPI for REST API endpoints with async support
- PostgreSQL 14+ with Row-Level Security for multi-tenant isolation
- SQLAlchemy 2.0+ ORM with Alembic for database migrations
- JWT tokens for stateless authentication with bcrypt password hashing
- Pydantic models for request/response validation
- Role-based middleware for endpoint protection
- Celery with Redis for background jobs (recurring bills, scheduled messages)
- CRON jobs for automatic recurring bill creation

FRONTEND ARCHITECTURE:
- Flutter 3.10+ for cross-platform mobile development
- Provider pattern (or Riverpod) for state management
- SQLite with sqflite for local mobile storage
- flutter_secure_storage for secure token storage
- Dio HTTP client with interceptors for auth and error handling
- Background sync using WorkManager (Android) / BackgroundFetch (iOS)
- Firebase Cloud Messaging for push notifications

AUTHENTICATION & SECURITY:
- JWT token validation on every API request
- Server-side role-based permission enforcement
- PostgreSQL Row-Level Security for data isolation
- HTTPS/TLS 1.3 for all API communication
- Certificate pinning for mobile API calls
- Encrypted local database on mobile
- PCI-DSS compliant payment processing

DATA SYNCHRONIZATION:
- Offline-first architecture with local SQLite storage
- Conflict resolution using last-write-wins with timestamp comparison
- Exponential backoff for retry logic on failed syncs
- API versioning (/api/v1/) for backward compatibility
- Database transactions for atomic operations
- Sync status tracking and error logging

DATABASE DESIGN:
- Core tables: users, properties, tenants, payments, bills, bill_allocations
- Supporting tables: expenses, messages, sync_logs, documents, notifications
- Payment gateway tables: transactions, payment_methods, refunds
- Analytics tables: analytics_cache, report_templates
- DECIMAL type for all monetary values (no FLOAT)
- Immutable financial records (soft deletes only)
- Indexed foreign keys for performance
- Audit trail columns (created_at, updated_at, created_by)
- JSONB columns for flexible metadata storage

BILL MANAGEMENT:
- PostgreSQL tables: bills, bill_items, bill_payments, recurring_bills
- Python decimal type for accurate financial calculations
- Deterministic remainder handling in bill division
- Flutter DataTable for bill display
- fl_chart library for financial visualizations

EXPORT FUNCTIONALITY:
- openpyxl (Python) for server-side Excel generation
- excel package (Flutter) for client-side exports
- ReportLab (Python) for PDF generation
- Customizable export templates with date range filters
- Background job processing for large exports
- Email delivery of generated reports

MESSAGING SYSTEM:
- SMS gateway integration (Twilio, AWS SNS, or local provider)
- WhatsApp Business API for message delivery
- Message queue using Celery for scheduled sending
- Jinja2 template engine for personalized messages
- Delivery status tracking and retry mechanism
- Rate limiting to prevent spam

DOCUMENT STORAGE:
- AWS S3 or equivalent cloud storage for document files
- boto3 library for S3 integration
- File upload with virus scanning (ClamAV)
- Document encryption at rest
- Presigned URLs for secure document access
- Document versioning with S3 versioning
- Thumbnail generation for image documents
- Full-text search using PostgreSQL full-text search
- Document retention policies and auto-deletion

PAYMENT GATEWAY INTEGRATION:
- Stripe SDK for payment processing
- Razorpay SDK for India market
- PayPal REST API for international payments
- Webhook handlers for payment confirmations
- PCI-DSS compliant tokenization
- 3D Secure authentication support
- Recurring payment subscriptions
- Payment reconciliation engine
- Multi-currency support with exchange rate API
- Refund and chargeback workflows

ANALYTICS & REPORTING:
- PostgreSQL materialized views for fast analytics queries
- Pandas for data analysis and aggregation
- Plotly or Chart.js for chart generation
- Scheduled report generation using Celery
- Report caching with Redis
- Real-time analytics using WebSockets
- Data export to CSV/Excel for further analysis
- Custom SQL queries for advanced reporting
- Dashboard widgets with customizable layouts

PUSH NOTIFICATIONS:
- Firebase Cloud Messaging (FCM) for Android/iOS
- APNs (Apple Push Notification service) for iOS
- Notification scheduling and batching
- Topic-based subscriptions for broadcast messages
- Device token management
- Notification analytics and delivery tracking
- Rich notifications with actions
- Silent notifications for data sync triggers

INTERNATIONALIZATION (i18n):
- Flutter intl package for UI translations
- JSON files for translation strings
- Language detection based on device locale
- Runtime language switching
- Date/time formatting with intl package
- Number and currency formatting per locale
- RTL layout support using Directionality widget
- Translation management system for easy updates
- Fallback language mechanism

TAX & COMPLIANCE REPORTING:
- Tax calculation engine with configurable rules
- Form generation using ReportLab templates
- GST/VAT calculation by region
- TDS (Tax Deducted at Source) tracking
- Financial year configuration
- Tax report scheduling and auto-generation
- Integration with accounting software (optional)
- Audit trail for all financial transactions
- Depreciation calculation using straight-line/declining balance methods
- Property valuation tracking with historical data

TESTING STRATEGY:
- pytest with pytest-asyncio for backend tests
- flutter_test with integration_test for mobile tests
- Contract tests for API endpoints
- Integration tests with real PostgreSQL (Docker containers)
- Load testing with Locust for performance validation
- Security testing with OWASP ZAP
- Minimum 80% backend coverage, 70% frontend coverage
- E2E tests for critical user flows
- Payment gateway testing in sandbox mode

DEPLOYMENT:
- Docker containers for backend services
- PostgreSQL with automated daily backups
- Redis for caching and message queuing
- Nginx as reverse proxy and load balancer
- Swagger UI for API documentation
- GitHub Actions or GitLab CI for CI/CD
- Environment-based configuration (.env files)
- Blue-green deployment for zero downtime
- Monitoring with Prometheus and Grafana
- Log aggregation with ELK stack or CloudWatch
- CDN for document storage and static assets
```

**Output:** Creates implementation plan with:
- `specs/[feature]/plan.md` - Technical architecture
- `specs/[feature]/data-model.md` - Database schemas
- `specs/[feature]/contracts/` - API specifications
- `specs/[feature]/research.md` - Technology comparisons

---

#### `/speckit.tasks`
Generate executable task lists derived from the implementation plan.

**Usage:**
```
/speckit.tasks
```

**Output:** Creates `specs/[feature]/tasks.md` with:
- Ordered tasks with dependencies
- Parallel execution markers `[P]` for independent tasks
- Test-first task ordering
- Clear acceptance criteria per task

**Example Task Structure:**
```markdown
## Phase 1: Database Setup
- [ ] [P] Create users table with role enum
- [ ] [P] Create tenants table with foreign key to users
- [ ] [P] Create payments table
- [ ] Create database indexes for performance
- [ ] Write migration scripts

## Phase 2: API Development
- [ ] Implement user registration endpoint (POST /api/users)
- [ ] Implement authentication endpoint (POST /api/auth/login)
- [ ] Implement tenant CRUD endpoints
- [ ] Add role-based middleware
- [ ] Write API contract tests

## Phase 3: Frontend Implementation
- [ ] [P] Create login screen
- [ ] [P] Create tenant list screen
- [ ] [P] Create tenant detail screen
- [ ] Implement state management
- [ ] Add offline storage
```

---

#### `/speckit.implement`
Execute all tasks and build the feature according to the plan.

**Usage:**
```
/speckit.implement
```

This command orchestrates the complete implementation by:
1. Reading the task list from `tasks.md`
2. Executing tasks in order, respecting dependencies
3. Running tests after each implementation phase
4. Validating against acceptance criteria
5. Creating a implementation log

---

### Optional Quality Commands

#### `/speckit.clarify`
Identify and clarify underspecified areas in the specification.

**Usage:**
```
/speckit.clarify
```

**What it does:**
- Analyzes spec.md for ambiguities
- Generates clarifying questions
- Identifies missing edge cases
- Suggests additional acceptance criteria

**Example Questions Generated:**
- "What happens when a tenant leaves mid-month? How is rent prorated?"
- "Should electricity bills be divided equally or based on room size?"
- "How far back should payment history be stored?"
- "What is the maximum number of tenants per property?"
- "Should intermediaries see each other's data?"

---

#### `/speckit.analyze`
Perform cross-artifact consistency and coverage analysis.

**Usage:**
```
/speckit.analyze
```

**Checks performed:**
- All spec requirements have corresponding tasks
- All API contracts have tests
- Data models support all required queries
- Security requirements are implemented
- Performance requirements are testable
- All user stories have acceptance criteria

---

#### `/speckit.checklist`
Generate custom quality checklists for validation.

**Usage - Complete Quality Checklist for Meroghar:**

```
/speckit.checklist Create comprehensive validation checklist for:

DATA PRIVACY COMPLIANCE:
- Tenant personal information encrypted at rest (AES-256)
- All API communications use HTTPS/TLS 1.3
- Passwords hashed with bcrypt (cost factor 12+)
- No PII in logs, error messages, or debugging output
- Secure token storage on mobile (flutter_secure_storage)
- Audit logs for all financial data access

FINANCIAL ACCURACY:
- All monetary values use DECIMAL/NUMERIC types (no FLOAT)
- Payment calculations verified with unit tests
- Bill division algorithms handle remainders correctly
- Balance calculations derive from transaction history
- Immutable financial records (soft deletes only)
- Receipt generation tested for all payment types
- Currency rounding follows consistent rules

ROLE-BASED ACCESS ENFORCEMENT:
- Server-side permission checks on all endpoints
- Tenants cannot access other tenants' data
- Intermediaries cannot see other intermediaries' data
- Owners have full visibility across all data
- Row-level security implemented in PostgreSQL
- API returns 404 for unauthorized resource access
- JWT token validation on every request

SYNC RELIABILITY:
- Offline mode fully functional without internet
- Sync conflict resolution tested with edge cases
- Failed syncs queued with exponential backoff
- Data validation before sync prevents corruption
- Multiple device sync tested for data consistency
- Network interruption handling verified
- Sync status indicators work correctly

MOBILE UX:
- App loads in under 3 seconds
- Screen transitions under 300ms
- Touch targets minimum 48x48 pixels
- Text readable at minimum 14sp font size
- Responsive layouts on all device sizes
- 60 FPS scrolling performance maintained
- Offline indicators clearly visible
- Error messages user-friendly with recovery steps

TESTING COVERAGE:
- Backend unit test coverage ≥80%
- Frontend unit test coverage ≥70%
- All API endpoints have contract tests
- Critical user flows have E2E tests
- Integration tests use real database
- Payment calculations have comprehensive tests
- Bill division edge cases covered

SECURITY AUDIT:
- Input sanitization on all user inputs
- SQL injection prevention verified
- XSS protection implemented
- Rate limiting configured on endpoints
- Certificate pinning on mobile
- Biometric authentication option available
- Auto-logout after inactivity period
- Secure session management

PERFORMANCE REQUIREMENTS:
- Authentication response < 500ms
- Tenant list load < 1s for 100 tenants
- Payment recording < 300ms
- Bill calculations < 2s for complex divisions
- Sync operation < 5s for typical dataset
- Excel export < 10s for 1 year data
- Database indexes on all foreign keys
```

**Output:** Custom checklist document in `specs/[feature]/checklist.md`

---

## Feature Breakdown for Meroghar

### Recommended Feature Implementation Order

```markdown
PHASE 1: FOUNDATION (Must-Have for MVP)
1. **001-user-authentication** (Foundation)
   - User management with three roles
   - Login/logout functionality
   - Role-based access control

2. **002-tenant-profiles** (Core Entity)
   - Tenant CRUD operations
   - Basic information management
   - Profile viewing

3. **003-payment-tracking** (Critical Feature)
   - Payment recording
   - Balance calculation
   - Payment history

4. **004-bill-management** (Critical Feature)
   - Bill creation and division
   - Monthly bill processing
   - Tenant bill allocation

PHASE 2: ESSENTIAL FEATURES
5. **005-expense-tracking** (Enhancement)
   - Maintenance expense recording
   - Expense categorization
   - Cost tracking

6. **006-rent-increment** (Automation)
   - Automated rent increase
   - Increment scheduling
   - Historical tracking

7. **007-data-sync** (Infrastructure)
   - Offline capability
   - Server synchronization
   - Conflict resolution

8. **008-excel-export** (Reporting)
   - Data export functionality
   - Report generation
   - Template customization

PHASE 3: COMMUNICATION & CONFIGURATION
9. **009-messaging** (Communication)
   - Message templates
   - Scheduled messaging
   - Delivery tracking

10. **010-settings** (Configuration)
    - System configuration
    - User preferences
    - Backup/restore

PHASE 4: ADVANCED FEATURES
11. **011-document-storage** (Document Management)
    - Lease agreement uploads
    - Document versioning
    - Secure access control
    - Cloud storage integration

12. **012-payment-gateway** (Online Payments)
    - Payment gateway integration
    - Multiple payment methods
    - Recurring payments
    - Transaction management

13. **013-analytics-dashboard** (Business Intelligence)
    - Interactive charts and graphs
    - Revenue/expense analytics
    - Performance metrics
    - Customizable reports

14. **014-push-notifications** (Real-time Alerts)
    - Firebase Cloud Messaging
    - Payment reminders
    - Event notifications
    - Notification preferences

PHASE 5: LOCALIZATION & COMPLIANCE
15. **015-multi-language** (Internationalization)
    - Multiple language support
    - RTL support
    - Locale-based formatting
    - Translation management

16. **016-tax-reporting** (Compliance)
    - Tax calculations
    - Form generation
    - Financial statements
    - Audit trails
```

---

## Database Schema Overview

### Core Tables

```
users
├── id (PK)
├── email
├── password_hash
├── role (owner/intermediary/tenant)
├── created_at
└── updated_at

properties
├── id (PK)
├── owner_id (FK -> users)
├── address
├── total_units
└── created_at

tenants
├── id (PK)
├── user_id (FK -> users)
├── property_id (FK -> properties)
├── intermediary_id (FK -> users)
├── mobile_number
├── start_date
├── current_rent
├── electricity_rate
└── status (active/inactive)

payments
├── id (PK)
├── tenant_id (FK -> tenants)
├── amount
├── payment_date
├── payment_type (rent/bill/other)
├── payment_method
└── notes

bills
├── id (PK)
├── property_id (FK -> properties)
├── bill_type (electricity/water/maintenance)
├── total_amount
├── billing_month
├── is_recurring
└── created_at

bill_allocations
├── id (PK)
├── bill_id (FK -> bills)
├── tenant_id (FK -> tenants)
├── allocation_percentage
├── allocated_amount
├── paid_amount
└── payment_status

expenses
├── id (PK)
├── property_id (FK -> properties)
├── expense_type (maintenance/repair/emergency)
├── amount
├── description
├── paid_by (FK -> users)
├── expense_date
└── receipt_url

messages
├── id (PK)
├── tenant_id (FK -> tenants)
├── message_text
├── scheduled_time
├── sent_time
├── delivery_status
└── message_type

sync_logs
├── id (PK)
├── user_id (FK -> users)
├── sync_timestamp
├── sync_status
├── records_synced
└── error_message

documents
├── id (PK)
├── tenant_id (FK -> tenants)
├── property_id (FK -> properties)
├── document_type (lease/id_proof/noc/other)
├── file_name
├── file_url (S3 path)
├── file_size
├── mime_type
├── version
├── expiration_date
├── uploaded_by (FK -> users)
├── created_at
└── updated_at

transactions
├── id (PK)
├── payment_id (FK -> payments)
├── gateway_name (stripe/razorpay/paypal)
├── transaction_id
├── amount
├── currency
├── status (pending/success/failed/refunded)
├── payment_method (card/upi/wallet)
├── gateway_response (JSONB)
├── created_at
└── completed_at

payment_methods
├── id (PK)
├── user_id (FK -> users)
├── gateway_name
├── token (encrypted)
├── card_last4
├── card_brand
├── expiry_month
├── expiry_year
├── is_default
└── created_at

notifications
├── id (PK)
├── user_id (FK -> users)
├── title
├── body
├── notification_type (payment/bill/message/document)
├── related_id (generic reference)
├── is_read
├── sent_at
├── read_at
└── created_at

analytics_cache
├── id (PK)
├── property_id (FK -> properties)
├── metric_name
├── metric_value (JSONB)
├── period_start
├── period_end
├── created_at
└── expires_at

report_templates
├── id (PK)
├── user_id (FK -> users)
├── template_name
├── report_type (financial/tax/tenant/custom)
├── template_config (JSONB)
├── schedule (cron expression)
├── created_at
└── updated_at

tax_records
├── id (PK)
├── property_id (FK -> properties)
├── financial_year
├── total_income
├── total_expenses
├── taxable_income
├── tax_rate
├── tax_amount
├── form_type
├── form_data (JSONB)
├── generated_at
└── filed_at

languages
├── id (PK)
├── language_code (en/hi/es/ar)
├── language_name
├── is_rtl
├── is_active
└── created_at

translations
├── id (PK)
├── language_id (FK -> languages)
├── translation_key
├── translation_value
└── updated_at
```

---

## API Endpoints Overview

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Authenticate user
- `POST /api/auth/logout` - Invalidate token
- `GET /api/auth/me` - Get current user info

### Tenants
- `GET /api/tenants` - List tenants (filtered by role)
- `GET /api/tenants/{id}` - Get tenant details
- `POST /api/tenants` - Create tenant
- `PUT /api/tenants/{id}` - Update tenant
- `DELETE /api/tenants/{id}` - Deactivate tenant

### Payments
- `GET /api/payments` - List payments
- `GET /api/payments/tenant/{id}` - Get tenant payments
- `POST /api/payments` - Record payment
- `GET /api/payments/summary/{tenant_id}` - Payment summary

### Bills
- `GET /api/bills` - List bills
- `POST /api/bills` - Create bill
- `PUT /api/bills/{id}` - Update bill
- `POST /api/bills/{id}/allocate` - Allocate bill to tenants
- `POST /api/bills/{id}/payment` - Record bill payment

### Expenses
- `GET /api/expenses` - List expenses
- `POST /api/expenses` - Record expense
- `GET /api/expenses/summary` - Expense summary

### Reports
- `GET /api/reports/tenant/{id}/export` - Export tenant data
- `GET /api/reports/property/{id}/export` - Export property data
- `GET /api/reports/financial-summary` - Financial summary

### Sync
- `POST /api/sync/push` - Push local changes
- `GET /api/sync/pull` - Pull server changes
- `GET /api/sync/status` - Check sync status

### Messages
- `POST /api/messages/send` - Send message
- `POST /api/messages/schedule` - Schedule message
- `GET /api/messages/history` - Message history

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update settings
- `POST /api/backup` - Create backup
- `POST /api/restore` - Restore from backup

### Documents
- `GET /api/documents` - List documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/download` - Download document
- `DELETE /api/documents/{id}` - Delete document
- `PUT /api/documents/{id}` - Update document metadata
- `GET /api/documents/tenant/{id}` - Get tenant documents

### Payment Gateway
- `POST /api/payments/gateway/initiate` - Initiate payment
- `POST /api/payments/gateway/callback` - Payment callback/webhook
- `GET /api/payments/gateway/methods` - List saved payment methods
- `POST /api/payments/gateway/methods` - Add payment method
- `DELETE /api/payments/gateway/methods/{id}` - Remove payment method
- `POST /api/payments/gateway/recurring` - Setup recurring payment
- `POST /api/payments/gateway/refund` - Process refund
- `GET /api/transactions` - List transactions
- `GET /api/transactions/{id}` - Get transaction details

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard metrics
- `GET /api/analytics/revenue` - Revenue analytics
- `GET /api/analytics/expenses` - Expense analytics
- `GET /api/analytics/occupancy` - Occupancy rates
- `GET /api/analytics/payment-trends` - Payment trend analysis
- `GET /api/analytics/tenant-behavior` - Tenant behavior insights
- `POST /api/analytics/custom` - Run custom analytics query
- `GET /api/analytics/export` - Export analytics data

### Notifications
- `GET /api/notifications` - List notifications
- `PUT /api/notifications/{id}/read` - Mark as read
- `PUT /api/notifications/read-all` - Mark all as read
- `DELETE /api/notifications/{id}` - Delete notification
- `POST /api/notifications/register-device` - Register FCM token
- `DELETE /api/notifications/unregister-device` - Unregister device
- `GET /api/notifications/preferences` - Get notification preferences
- `PUT /api/notifications/preferences` - Update preferences

### Tax & Reporting
- `GET /api/tax/calculate` - Calculate tax
- `POST /api/tax/generate-report` - Generate tax report
- `GET /api/tax/reports` - List tax reports
- `GET /api/tax/reports/{id}` - Get tax report details
- `GET /api/reports/financial-statement` - Generate P&L statement
- `GET /api/reports/cash-flow` - Cash flow report
- `GET /api/reports/depreciation` - Depreciation report
- `POST /api/reports/schedule` - Schedule recurring report
- `GET /api/reports/templates` - List report templates
- `POST /api/reports/templates` - Create report template

### Internationalization
- `GET /api/languages` - List available languages
- `GET /api/translations/{lang_code}` - Get translations for language
- `PUT /api/user/language` - Set user language preference

---

## Development Workflow Example

### Complete Feature Development Flow

Follow this exact sequence to build the Meroghar system from scratch:

```bash
# Step 1: Initialize project with constitution (see Quick Start section above)
/speckit.constitution Create principles for Meroghar...

# Step 2: Create complete system specification (copy from Quick Start section)
/speckit.specify Build a comprehensive house rental management system...

# Step 3: Clarify ambiguities (optional but recommended)
/speckit.clarify

# Step 4: Create technical implementation plan (copy from Quick Start section)
/speckit.plan Implement Meroghar with the following technical architecture...

# Step 5: Generate executable task list
/speckit.tasks

# Step 6: Analyze consistency (optional but recommended)
/speckit.analyze

# Step 7: Create quality checklist (copy from Quick Start section)
/speckit.checklist Create comprehensive validation checklist for...

# Step 8: Implement all features
/speckit.implement
```

**Note:** All complete commands are available in the "🚀 Quick Start" section at the top of this document for easy copy-paste.

---

## Quality Gates & Checklists

### Pre-Implementation Checklist
- [ ] All user stories have acceptance criteria
- [ ] No `[NEEDS CLARIFICATION]` markers remain
- [ ] Database schema supports all queries
- [ ] API contracts are complete
- [ ] Security requirements are defined
- [ ] Performance targets are specified

### Implementation Checklist
- [ ] All tests written before implementation
- [ ] Database migrations created
- [ ] API endpoints implemented
- [ ] Frontend screens completed
- [ ] Error handling added
- [ ] Logging configured

### Pre-Deployment Checklist
- [ ] All tests passing (unit, integration, e2e)
- [ ] Security audit completed
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Backup/restore tested
- [ ] Sync edge cases verified

---

## Edge Cases to Consider

### Data Synchronization
- Tenant deleted on server while editing offline
- Multiple devices syncing same tenant data
- Network interruption during sync
- Large data sets exceeding mobile storage
- Schema version mismatches

### Payment & Bills
- Partial payments across multiple transactions
- Bill amount changes after allocation
- Tenant leaves before paying full bill share
- Currency rounding errors in division
- Negative balances (overpayment)

### User Management
- Intermediary creates tenant, then intermediary is deleted
- Owner transfers property to new owner
- Tenant account deleted but payments exist
- Role changes mid-transaction

### Messaging
- Message scheduled but tenant deactivated
- Bulk message failure handling
- SMS/WhatsApp API rate limits
- Message character limits

### Document Storage
- Document upload fails mid-transfer
- Storage quota exceeded
- File virus detection during upload
- Document access after tenant moves out
- Version conflicts when multiple users edit
- Large file uploads (>10MB) handling

### Payment Gateway
- Payment gateway downtime during transaction
- Webhook delivery failures or delays
- Duplicate webhook processing
- Partial refunds and chargebacks
- Currency conversion rate changes mid-transaction
- 3D Secure authentication failures
- Recurring payment card expiration
- Payment method auto-deletion after failures

### Analytics & Reporting
- Real-time data vs cached data conflicts
- Report generation timeout for large datasets
- Concurrent report generation requests
- Custom date range edge cases (leap years, DST)
- Missing data points in trend charts
- Dashboard performance with multiple properties

### Push Notifications
- Device token expiration or invalidation
- User has multiple devices (iOS + Android)
- Notification delivery when app is killed
- Notification grouping for bulk operations
- Silent notification failures
- Badge count synchronization across devices

---

## Security Considerations

### Data Privacy
- Encrypt sensitive data at rest (passwords, personal info)
- Use HTTPS for all API communication
- Implement rate limiting on endpoints
- Sanitize all user inputs
- Log access to sensitive data

### Access Control
- Validate JWT tokens on every request
- Enforce role-based permissions server-side
- Never trust client-side role validation
- Implement row-level security in PostgreSQL
- Audit logs for data access

### Mobile Security
- Secure token storage (flutter_secure_storage)
- Certificate pinning for API calls
- Biometric authentication option
- Auto-logout after inactivity
- Encrypted local database

---

## Performance Requirements

### API Response Times
- Authentication: < 500ms
- Tenant list: < 1s for 100 tenants
- Payment recording: < 300ms
- Bill calculation: < 2s for complex divisions
- Sync operation: < 5s for typical dataset

### Mobile App
- App startup: < 3s
- Screen transitions: < 300ms
- Offline mode: Full functionality
- Export generation: < 10s for 1 year data

### Database
- Index all foreign keys
- Optimize queries with EXPLAIN
- Partition large tables if needed
- Regular vacuum and analyze
- Connection pooling configured

---

## Testing Strategy

### Unit Tests
- Business logic in isolation
- Payment calculations
- Bill division algorithms
- Rent increment calculations
- Date/time utilities

### Integration Tests
- API endpoint functionality
- Database operations
- Authentication flows
- Role-based access
- Sync operations

### End-to-End Tests
- User registration → tenant creation → payment recording
- Bill creation → allocation → payment
- Offline edit → sync → conflict resolution
- Message scheduling → delivery

### Manual Testing
- Mobile UX on various devices
- Network interruption scenarios
- Edge case workflows
- Accessibility features

---

## Configuration Files

### Backend (Python/FastAPI)
```
backend/
├── .env (environment variables)
├── requirements.txt (dependencies)
├── alembic.ini (database migrations)
├── pytest.ini (test configuration)
└── logging.conf (logging setup)
```

### Frontend (Flutter)
```
frontend/
├── .env (API endpoints)
├── pubspec.yaml (dependencies)
├── analysis_options.yaml (linting)
└── test/ (test configuration)
```

---

## Deployment Checklist

### Backend Deployment
- [ ] PostgreSQL database provisioned
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] API server deployed (Docker/VM)
- [ ] SSL certificates installed
- [ ] Backup schedule configured
- [ ] Monitoring/logging setup

### Mobile App Deployment
- [ ] App Store/Play Store accounts ready
- [ ] App icons and splash screens
- [ ] App signing certificates
- [ ] Privacy policy and terms
- [ ] Beta testing completed
- [ ] App store listings prepared
- [ ] Release notes written

---

## Maintenance & Support

### Regular Tasks
- Database backups (daily)
- Log rotation (weekly)
- Security updates (as needed)
- Performance monitoring (continuous)
- User feedback review (weekly)

### Troubleshooting
- Sync failures → Check sync_logs table
- Payment discrepancies → Audit payment history
- Permission issues → Verify role assignments
- Performance issues → Analyze slow query log

---

## Future Enhancements (Not in Initial Scope)

- Multi-property management for portfolio owners
- Tenant-to-tenant messaging and community features
- Property marketplace integration
- Smart home device integration (IoT)
- Tenant screening and background checks
- Maintenance ticket system with vendor management
- Insurance tracking and claims management
- Energy consumption monitoring and optimization
- AI-powered rent pricing recommendations
- Predictive maintenance alerts
- Virtual property tours with AR/VR
- Blockchain-based lease contracts
- Chatbot for tenant support
- Voice-activated commands (Alexa/Google Home)
- Social media integration for property listings

---

## References

- [Spec-Driven Development Methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://docs.flutter.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## Contact & Support

For questions or issues during development:
- Review specification documents in `specs/` directory
- Check implementation plans for technical decisions
- Refer to API contracts for endpoint details
- Consult data models for database schema

---

**Document Version**: 1.0  
**Last Updated**: October 26, 2025  
**Project**: Meroghar - House Rental Management System