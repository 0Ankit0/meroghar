# Tasks: Meroghar Rental Management System

**Input**: Design documents from `/specs/001-rental-management/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: This feature specification does NOT explicitly request TDD or test-first approach. Tests are OPTIONAL and marked below for reference only.

**Organization**: Tasks are grouped by user story (14 total stories) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US14)
- Include exact file paths in descriptions

## Path Conventions

This is a Mobile + API project with:

- Backend: `backend/src/`
- Frontend: `mobile/lib/`
- Tests: `backend/tests/` and `mobile/test/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend directory structure: backend/src/{api,models,schemas,services,core,tasks}
- [x] T002 Create mobile directory structure: mobile/lib/{screens,widgets,services,models,providers,utils}
- [x] T003 Initialize Python project with FastAPI, SQLAlchemy, Alembic, PyJWT, bcrypt, Pydantic in backend/requirements.txt
- [x] T004 [P] Initialize Flutter project with dependencies: provider, sqflite, flutter_secure_storage, dio, fl_chart in mobile/pubspec.yaml
- [x] T005 [P] Configure Python linting (ruff) and formatting (black) in backend/pyproject.toml
- [x] T006 [P] Configure Dart linting and formatting in mobile/analysis_options.yaml
- [x] T007 Setup Docker Compose with PostgreSQL 14+ and Redis services in docker-compose.yml
- [x] T008 [P] Create .env.example for backend environment variables (DATABASE_URL, SECRET_KEY, JWT config)
- [x] T009 [P] Create mobile/lib/config/env.example.dart for Flutter environment configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Setup database connection and session management in backend/src/core/database.py
- [x] T011 Initialize Alembic migrations framework in backend/alembic/
- [x] T012 [P] Implement password hashing utilities (bcrypt cost 12+) in backend/src/core/security.py
- [x] T013 [P] Implement JWT token generation/validation (access + refresh tokens) in backend/src/core/security.py
- [x] T014 Create FastAPI dependencies for auth and DB sessions in backend/src/api/dependencies.py
- [x] T015 [P] Setup CORS middleware and error handlers in backend/src/core/middleware.py
- [x] T016 [P] Configure logging infrastructure in backend/src/core/config.py
- [x] T017 Setup API router with /api/v1 prefix in backend/src/main.py
- [x] T018 [P] Create base Pydantic schemas (SuccessResponse, ErrorResponse) in backend/src/schemas/**init**.py
- [x] T019 [P] Setup SQLite local database helper for mobile in mobile/lib/services/database_service.dart
- [x] T020 [P] Create secure storage service for JWT tokens in mobile in mobile/lib/services/secure_storage_service.dart
- [x] T021 [P] Setup Dio HTTP client with interceptors for auth in mobile/lib/services/api_service.dart
- [x] T022 Create Celery app configuration with Redis broker in backend/src/tasks/celery_app.py
- [x] T023 [P] Setup app configuration and environment loader in backend/src/core/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Owner Onboards Property and First Tenant (Priority: P1) 🎯 MVP

**Goal**: Property owner registers, sets up property, creates intermediary account, and intermediary creates first tenant with rent details

**Independent Test**: Complete user registration → property setup → tenant creation → viewing tenant in list, delivering a working system that tracks who lives where

### Implementation for User Story 1

- [ ] T024 [P] [US1] Create User model with role enum in backend/src/models/user.py
- [ ] T025 [P] [US1] Create Property model with owner_id FK in backend/src/models/property.py
- [ ] T026 [P] [US1] Create PropertyAssignment junction model in backend/src/models/property.py
- [ ] T027 [P] [US1] Create Tenant model with property and user FKs in backend/src/models/tenant.py
- [ ] T028 [US1] Create Alembic migration for User, Property, PropertyAssignment, Tenant tables in backend/alembic/versions/
- [ ] T029 [P] [US1] Create auth request/response schemas in backend/src/schemas/auth.py
- [ ] T030 [P] [US1] Create user request/response schemas in backend/src/schemas/user.py
- [ ] T031 [P] [US1] Create property request/response schemas in backend/src/schemas/property.py
- [ ] T032 [P] [US1] Create tenant request/response schemas in backend/src/schemas/tenant.py
- [ ] T033 [US1] Implement AuthService with register, login, token refresh in backend/src/services/auth_service.py
- [ ] T034 [US1] Implement authentication endpoints (register, login, refresh) in backend/src/api/v1/auth.py
- [ ] T035 [US1] Implement user creation endpoint (POST /api/v1/users) in backend/src/api/v1/users.py
- [ ] T036 [US1] Implement property creation endpoint (POST /api/v1/properties) in backend/src/api/v1/properties.py
- [ ] T037 [US1] Implement intermediary assignment endpoint (POST /api/v1/properties/{id}/assign) in backend/src/api/v1/properties.py
- [ ] T038 [US1] Implement tenant creation endpoint (POST /api/v1/tenants) in backend/src/api/v1/tenants.py
- [ ] T039 [US1] Implement tenant list endpoint (GET /api/v1/tenants) with RLS in backend/src/api/v1/tenants.py
- [ ] T040 [P] [US1] Create User model for mobile local storage in mobile/lib/models/user.dart
- [ ] T041 [P] [US1] Create Property model for mobile local storage in mobile/lib/models/property.dart
- [ ] T042 [P] [US1] Create Tenant model for mobile local storage in mobile/lib/models/tenant.dart
- [ ] T043 [US1] Create auth provider with login/register state in mobile/lib/providers/auth_provider.dart
- [ ] T044 [US1] Create registration screen for owners in mobile/lib/screens/auth/register_screen.dart
- [ ] T045 [US1] Create login screen for all users in mobile/lib/screens/auth/login_screen.dart
- [ ] T046 [US1] Create property setup screen in mobile/lib/screens/properties/property_form_screen.dart
- [ ] T047 [US1] Create intermediary creation form in mobile/lib/screens/users/intermediary_form_screen.dart
- [ ] T048 [US1] Create tenant creation form in mobile/lib/screens/tenants/tenant_form_screen.dart
- [ ] T049 [US1] Create tenant list screen with card view in mobile/lib/screens/tenants/tenant_list_screen.dart
- [ ] T050 [US1] Implement RLS policies for users table in backend/alembic/versions/
- [ ] T051 [US1] Implement RLS policies for properties table in backend/alembic/versions/
- [ ] T052 [US1] Implement RLS policies for tenants table in backend/alembic/versions/
- [ ] T053 [US1] Add RLS session variable middleware in backend/src/core/middleware.py
- [ ] T054 [US1] Add validation and error handling to all US1 endpoints in backend/src/api/v1/
- [ ] T055 [US1] Add logging for user registration and tenant creation in backend/src/services/

**Checkpoint**: At this point, User Story 1 should be fully functional - users can register, create properties, assign intermediaries, and create tenants

---

## Phase 4: User Story 2 - Intermediary Records Monthly Rent Payment (Priority: P1)

**Goal**: Intermediary collects rent from tenant, records payment in system, and generates receipt

**Independent Test**: Record a payment → view updated balance → generate receipt, delivering immediate value for rent tracking

### Implementation for User Story 2

- [ ] T056 [P] [US2] Create Payment model with tenant_id, amount, method in backend/src/models/payment.py
- [ ] T057 [P] [US2] Create Transaction model for payment gateway records in backend/src/models/payment.py
- [ ] T058 [US2] Create Alembic migration for Payment and Transaction tables in backend/alembic/versions/
- [ ] T059 [P] [US2] Create payment request/response schemas in backend/src/schemas/payment.py
- [ ] T060 [US2] Implement PaymentService with record_payment, calculate_balance methods in backend/src/services/payment_service.py
- [ ] T061 [US2] Implement payment recording endpoint (POST /api/v1/payments) in backend/src/api/v1/payments.py
- [ ] T062 [US2] Implement payment history endpoint (GET /api/v1/payments?tenant_id=) in backend/src/api/v1/payments.py
- [ ] T063 [US2] Implement tenant balance endpoint (GET /api/v1/tenants/{id}/balance) in backend/src/api/v1/tenants.py
- [ ] T064 [US2] Implement receipt generation endpoint (GET /api/v1/payments/{id}/receipt) with PDF in backend/src/api/v1/payments.py
- [ ] T065 [P] [US2] Create Payment model for mobile local storage in mobile/lib/models/payment.dart
- [ ] T066 [US2] Create payment provider with payment state in mobile/lib/providers/payment_provider.dart
- [ ] T067 [US2] Create payment recording screen in mobile/lib/screens/payments/payment_form_screen.dart
- [ ] T068 [US2] Create payment history screen in mobile/lib/screens/payments/payment_history_screen.dart
- [ ] T069 [US2] Add payment status indicator to tenant list cards in mobile/lib/widgets/tenant_card.dart
- [ ] T070 [US2] Create receipt view/download widget in mobile/lib/screens/payments/receipt_view_screen.dart
- [ ] T071 [US2] Implement overdue payment highlighting logic in mobile/lib/widgets/tenant_card.dart
- [ ] T072 [US2] Implement RLS policies for payments table in backend/alembic/versions/
- [ ] T073 [US2] Add pro-rated rent calculation for mid-month move-in in backend/src/services/payment_service.py
- [ ] T074 [US2] Add validation and error handling to all US2 endpoints in backend/src/api/v1/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - full rent payment tracking is functional

---

## Phase 5: User Story 3 - Intermediary Divides Monthly Utility Bills (Priority: P2)

**Goal**: Intermediary receives utility bills and divides costs among tenants based on percentage or fixed amount rules

**Independent Test**: Create bill → set division rules → allocate to tenants → track payments, delivering automated bill splitting

### Implementation for User Story 3

- [ ] T075 [P] [US3] Create Bill model with total_amount, bill_type, period in backend/src/models/bill.py
- [ ] T076 [P] [US3] Create BillAllocation model with tenant_id, percentage, amount in backend/src/models/bill.py
- [ ] T077 [P] [US3] Create RecurringBill model with schedule and template in backend/src/models/bill.py
- [ ] T078 [US3] Create Alembic migration for Bill, BillAllocation, RecurringBill tables in backend/alembic/versions/
- [ ] T079 [P] [US3] Create bill request/response schemas in backend/src/schemas/bill.py
- [ ] T080 [US3] Implement BillService with division algorithm (DECIMAL, deterministic rounding) in backend/src/services/bill_service.py
- [ ] T081 [US3] Implement bill creation endpoint (POST /api/v1/bills) in backend/src/api/v1/bills.py
- [ ] T082 [US3] Implement bill allocation endpoint (POST /api/v1/bills/{id}/allocate) in backend/src/api/v1/bills.py
- [ ] T083 [US3] Implement bill list endpoint (GET /api/v1/bills) with filters in backend/src/api/v1/bills.py
- [ ] T084 [US3] Implement bill payment marking endpoint (PATCH /api/v1/bills/{bill_id}/allocations/{id}/pay) in backend/src/api/v1/bills.py
- [ ] T085 [US3] Implement recurring bill setup endpoint (POST /api/v1/bills/recurring) in backend/src/api/v1/bills.py
- [ ] T086 [US3] Create Celery task for automatic monthly bill generation in backend/src/tasks/bill_tasks.py
- [ ] T087 [P] [US3] Create Bill and BillAllocation models for mobile in mobile/lib/models/bill.dart
- [ ] T088 [US3] Create bill provider with bill state in mobile/lib/providers/bill_provider.dart
- [ ] T089 [US3] Create bill creation screen with division rules UI in mobile/lib/screens/bills/bill_form_screen.dart
- [ ] T090 [US3] Create bill allocation screen showing tenant shares in mobile/lib/screens/bills/bill_allocation_screen.dart
- [ ] T091 [US3] Create bill list screen with payment status in mobile/lib/screens/bills/bill_list_screen.dart
- [ ] T092 [US3] Add bill share display to tenant dashboard in mobile/lib/screens/tenants/tenant_dashboard_screen.dart
- [ ] T093 [US3] Implement RLS policies for bills and allocations tables in backend/alembic/versions/
- [ ] T094 [US3] Add validation and error handling to all US3 endpoints in backend/src/api/v1/

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - bill management is fully functional

---

## Phase 6: User Story 4 - Owner Views Financial Analytics (Priority: P2)

**Goal**: Owner views interactive dashboard with rent collection trends, expense breakdown, and revenue vs expenses comparison

**Independent Test**: Record transactions → view dashboard with charts → export data, delivering instant business insights

### Implementation for User Story 4

- [ ] T095 [US4] Create AnalyticsService with data aggregation methods in backend/src/services/analytics_service.py
- [ ] T096 [US4] Implement rent collection trends endpoint (GET /api/v1/analytics/rent-trends) in backend/src/api/v1/analytics.py
- [ ] T097 [US4] Implement payment status overview endpoint (GET /api/v1/analytics/payment-status) in backend/src/api/v1/analytics.py
- [ ] T098 [US4] Implement expense breakdown endpoint (GET /api/v1/analytics/expense-breakdown) in backend/src/api/v1/analytics.py
- [ ] T099 [US4] Implement revenue vs expenses endpoint (GET /api/v1/analytics/revenue-expenses) in backend/src/api/v1/analytics.py
- [ ] T100 [US4] Implement property-wise performance endpoint (GET /api/v1/analytics/property-performance) in backend/src/api/v1/analytics.py
- [ ] T101 [US4] Add date range filtering to all analytics endpoints in backend/src/api/v1/analytics.py
- [ ] T102 [US4] Create analytics provider with chart data state in mobile/lib/providers/analytics_provider.dart
- [ ] T103 [US4] Create analytics dashboard screen with multiple chart widgets in mobile/lib/screens/analytics/analytics_dashboard_screen.dart
- [ ] T104 [P] [US4] Create line chart widget for rent trends using fl_chart in mobile/lib/widgets/charts/line_chart_widget.dart
- [ ] T105 [P] [US4] Create pie chart widget for expense breakdown using fl_chart in mobile/lib/widgets/charts/pie_chart_widget.dart
- [ ] T106 [P] [US4] Create bar chart widget for revenue vs expenses using fl_chart in mobile/lib/widgets/charts/bar_chart_widget.dart
- [ ] T107 [US4] Add date range picker to analytics dashboard in mobile/lib/widgets/date_range_picker.dart
- [ ] T108 [US4] Implement drill-down detail view for chart elements in mobile/lib/screens/analytics/analytics_detail_screen.dart
- [ ] T109 [US4] Add analytics data export endpoint (POST /api/v1/analytics/export) with PDF/Excel in backend/src/api/v1/analytics.py

## **Checkpoint**: At this point, owners can view comprehensive financial analytics and insights

## Phase 7: User Story 5 - Tenant Pays Rent Online via Payment Gateway (Priority: P3)

**Goal**: Tenant receives reminder, opens app, and pays rent directly using credit card or UPI through integrated gateway

**Independent Test**: Tenant selects payment ? enters card details ? receives confirmation ? sees updated balance

### Implementation for User Story 5

- [ ] T110 [US5] Implement Stripe payment gateway integration in backend/src/services/payment_gateway/stripe_service.py
- [ ] T111 [P] [US5] Implement Razorpay payment gateway integration in backend/src/services/payment_gateway/razorpay_service.py
- [ ] T112 [P] [US5] Implement PayPal payment gateway integration in backend/src/services/payment_gateway/paypal_service.py
- [ ] T113 [US5] Create payment gateway factory in backend/src/services/payment_gateway/**init**.py
- [ ] T114 [US5] Implement payment initiation endpoint (POST /api/v1/payments/initiate) in backend/src/api/v1/payments.py
- [ ] T115 [P] [US5] Implement payment webhook handler for Stripe (POST /api/v1/webhooks/stripe) in backend/src/api/v1/webhooks.py
- [ ] T116 [P] [US5] Implement payment webhook handler for Razorpay (POST /api/v1/webhooks/razorpay) in backend/src/api/v1/webhooks.py
- [ ] T117 [P] [US5] Implement payment webhook handler for PayPal (POST /api/v1/webhooks/paypal) in backend/src/api/v1/webhooks.py
- [ ] T118 [US5] Implement payment status polling endpoint (GET /api/v1/payments/{id}/status) in backend/src/api/v1/payments.py
- [ ] T119 [US5] Create payment gateway integration in mobile using webview in mobile/lib/screens/payments/payment_gateway_screen.dart
- [ ] T120 [US5] Create payment method selection screen in mobile/lib/screens/payments/payment_method_screen.dart
- [ ] T121 [US5] Implement auto-receipt generation after successful gateway payment in backend/src/services/payment_service.py
- [ ] T122 [US5] Add payment confirmation notification in backend/src/tasks/notification_tasks.py
- [ ] T123 [US5] Implement failed payment retry mechanism in mobile/lib/providers/payment_provider.dart
- [ ] T124 [US5] Add payment gateway fee tracking in Transaction model in backend/src/models/payment.py

**Checkpoint**: At this point, tenants can pay rent online through multiple payment gateways

---

## Phase 8: User Story 6 - Intermediary Tracks Maintenance Expenses (Priority: P3)

**Goal**: Intermediary records maintenance expenses with receipt photos for owner reimbursement tracking

**Independent Test**: Record expense → upload receipt → categorize → view in reports, delivering expense accountability

### Implementation for User Story 6

- [ ] T125 [P] [US6] Create Expense model with amount, category, description, paid_by in backend/src/models/expense.py
- [ ] T126 [US6] Create Alembic migration for Expense table in backend/alembic/versions/
- [ ] T127 [P] [US6] Create expense request/response schemas in backend/src/schemas/expense.py
- [ ] T128 [US6] Implement S3 document upload service in backend/src/services/document_service.py
- [ ] T129 [US6] Implement expense recording endpoint (POST /api/v1/expenses) in backend/src/api/v1/expenses.py
- [ ] T130 [US6] Implement receipt upload endpoint (POST /api/v1/expenses/{id}/receipt) in backend/src/api/v1/expenses.py
- [ ] T131 [US6] Implement expense list endpoint (GET /api/v1/expenses) with filters in backend/src/api/v1/expenses.py
- [ ] T132 [US6] Implement expense approval endpoint (PATCH /api/v1/expenses/{id}/approve) in backend/src/api/v1/expenses.py
- [ ] T133 [US6] Implement expense report generation endpoint (GET /api/v1/reports/expenses) in backend/src/api/v1/reports.py
- [ ] T134 [P] [US6] Create Expense model for mobile in mobile/lib/models/expense.dart
- [ ] T135 [US6] Create expense provider in mobile/lib/providers/expense_provider.dart
- [ ] T136 [US6] Create expense recording screen with image picker in mobile/lib/screens/expenses/expense_form_screen.dart
- [ ] T137 [US6] Create expense list screen with category filters in mobile/lib/screens/expenses/expense_list_screen.dart
- [ ] T138 [US6] Create expense approval screen for owners in mobile/lib/screens/expenses/expense_approval_screen.dart
- [ ] T139 [US6] Add expense category breakdown to analytics dashboard in mobile/lib/screens/analytics/analytics_dashboard_screen.dart
- [ ] T140 [US6] Implement RLS policies for expenses table in backend/alembic/versions/

**Checkpoint**: At this point, all maintenance expenses can be tracked with receipts and approvals

---

## Phase 9: User Story 7 - System Syncs Data Across Offline Mobile Devices (Priority: P2)

**Goal**: Intermediary records changes offline, and system automatically syncs when connection restored without data loss

**Independent Test**: Make changes offline → go online → verify sync → check for conflicts, delivering reliable offline operation

### Implementation for User Story 7

- [ ] T141 [P] [US7] Create SyncLog model with timestamp, status, records_synced in backend/src/models/sync.py
- [ ] T142 [US7] Create Alembic migration for SyncLog table in backend/alembic/versions/
- [ ] T143 [US7] Implement SyncService with conflict resolution logic in backend/src/services/sync_service.py
- [ ] T144 [US7] Implement bulk sync endpoint (POST /api/v1/sync) accepting multiple operations in backend/src/api/v1/sync.py
- [ ] T145 [US7] Implement sync status endpoint (GET /api/v1/sync/status) in backend/src/api/v1/sync.py
- [ ] T146 [US7] Implement conflict resolution UI endpoint (GET /api/v1/sync/conflicts) in backend/src/api/v1/sync.py
- [ ] T147 [US7] Add updated_at timestamp to all models for LWW comparison in backend/src/models/
- [ ] T148 [US7] Add device_id tracking to mobile local database in mobile/lib/services/database_service.dart
- [ ] T149 [US7] Create sync service with queue and retry logic in mobile/lib/services/sync_service.dart
- [ ] T150 [US7] Implement offline operation queueing in mobile/lib/services/offline_queue_service.dart
- [ ] T151 [US7] Create sync status indicator widget in mobile/lib/widgets/sync_status_indicator.dart
- [ ] T152 [US7] Implement automatic sync on connection restore in mobile/lib/services/connectivity_service.dart
- [ ] T153 [US7] Create conflict resolution UI screen in mobile/lib/screens/sync/conflict_resolution_screen.dart
- [ ] T154 [US7] Implement exponential backoff retry mechanism in mobile/lib/services/sync_service.dart
- [ ] T155 [US7] Add sync preferences to settings screen in mobile/lib/screens/settings/sync_settings_screen.dart
- [ ] T156 [US7] Create sync log viewer screen in mobile/lib/screens/sync/sync_log_screen.dart

**Checkpoint**: At this point, offline functionality is fully operational with conflict resolution

---

## Phase 10: User Story 8 - Intermediary Sends Bulk Payment Reminders (Priority: P3)

**Goal**: Intermediary selects multiple tenants with overdue rent and sends personalized SMS/WhatsApp reminders with one click

**Independent Test**: Select tenants → choose template → send messages → track delivery, delivering automated reminders

### Implementation for User Story 8

- [ ] T157 [P] [US8] Create Message model with content, schedule, status in backend/src/models/message.py
- [ ] T158 [US8] Create Alembic migration for Message table in backend/alembic/versions/
- [ ] T159 [P] [US8] Create message request/response schemas in backend/src/schemas/message.py
- [ ] T160 [US8] Implement Twilio SMS integration in backend/src/services/message_service.py
- [ ] T161 [US8] Implement WhatsApp messaging via Twilio in backend/src/services/message_service.py
- [ ] T162 [US8] Create message template system in backend/src/services/message_service.py
- [ ] T163 [US8] Implement bulk message sending endpoint (POST /api/v1/messages/bulk) in backend/src/api/v1/messages.py
- [ ] T164 [US8] Implement scheduled message endpoint (POST /api/v1/messages/schedule) in backend/src/api/v1/messages.py
- [ ] T165 [US8] Implement message history endpoint (GET /api/v1/messages) in backend/src/api/v1/messages.py
- [ ] T166 [US8] Create Celery task for scheduled message delivery in backend/src/tasks/message_tasks.py
- [ ] T167 [US8] Create Celery beat schedule for recurring reminders in backend/src/tasks/celery_app.py
- [ ] T168 [P] [US8] Create Message model for mobile in mobile/lib/models/message.dart
- [ ] T169 [US8] Create message provider in mobile/lib/providers/message_provider.dart
- [ ] T170 [US8] Create bulk message screen with tenant selection in mobile/lib/screens/messages/bulk_message_screen.dart
- [ ] T171 [US8] Create message template picker in mobile/lib/widgets/message_template_picker.dart
- [ ] T172 [US8] Create message history screen in mobile/lib/screens/messages/message_history_screen.dart
- [ ] T173 [US8] Add delivery status tracking widget in mobile/lib/widgets/message_status_widget.dart
- [ ] T174 [US8] Implement RLS policies for messages table in backend/alembic/versions/

**Checkpoint**: At this point, bulk messaging functionality is operational

---

## Phase 11: User Story 9 - Tenant Uploads and Stores Lease Agreement (Priority: P3)

**Goal**: Tenant uploads signed lease agreement PDF with expiration reminder for renewal date

**Independent Test**: Upload document → set expiration → access securely → receive reminder, delivering document management

### Implementation for User Story 9

- [ ] T175 [P] [US9] Create Document model with file_url, type, expiration_date in backend/src/models/document.py
- [ ] T176 [US9] Create Alembic migration for Document table in backend/alembic/versions/
- [ ] T177 [P] [US9] Create document request/response schemas in backend/src/schemas/document.py
- [ ] T178 [US9] Implement document upload endpoint (POST /api/v1/documents) with S3 in backend/src/api/v1/documents.py
- [ ] T179 [US9] Implement document download endpoint (GET /api/v1/documents/{id}/download) in backend/src/api/v1/documents.py
- [ ] T180 [US9] Implement document list endpoint (GET /api/v1/documents) with filters in backend/src/api/v1/documents.py
- [ ] T181 [US9] Implement document expiration check task in backend/src/tasks/document_tasks.py
- [ ] T182 [US9] Add document expiration reminder notifications in backend/src/tasks/notification_tasks.py
- [ ] T183 [US9] Implement document version history tracking in backend/src/services/document_service.py
- [ ] T184 [US9] Implement document access revocation on tenant deactivation in backend/src/services/document_service.py
- [ ] T185 [P] [US9] Create Document model for mobile in mobile/lib/models/document.dart
- [ ] T186 [US9] Create document provider in mobile/lib/providers/document_provider.dart
- [ ] T187 [US9] Create document upload screen with file picker in mobile/lib/screens/documents/document_upload_screen.dart
- [ ] T188 [US9] Create document list screen with category filters in mobile/lib/screens/documents/document_list_screen.dart
- [ ] T189 [US9] Create document viewer screen for PDF/images in mobile/lib/screens/documents/document_viewer_screen.dart
- [ ] T190 [US9] Implement RLS policies for documents table in backend/alembic/versions/

**Checkpoint**: At this point, document storage and expiration tracking is functional

---

## Phase 12: User Story 10 - Owner Configures Automatic Rent Increment (Priority: P3)

**Goal**: Owner sets rent increment policy (5% every 2 years) and system automatically calculates and applies increases on tenant anniversaries

**Independent Test**: Set policy → wait for anniversary → see auto-increment → notify tenant, delivering automated rent increases

### Implementation for User Story 10

- [ ] T191 [US10] Add rent_increment_policy JSON column to Tenant model in backend/src/models/tenant.py
- [ ] T192 [US10] Add rent_history JSON column to Tenant model for historical rates in backend/src/models/tenant.py
- [ ] T193 [US10] Create Alembic migration for rent increment columns in backend/alembic/versions/
- [ ] T194 [US10] Implement rent increment calculation service in backend/src/services/rent_increment_service.py
- [ ] T195 [US10] Implement rent increment policy endpoint (PUT /api/v1/tenants/{id}/rent-policy) in backend/src/api/v1/tenants.py
- [ ] T196 [US10] Implement manual rent override endpoint (POST /api/v1/tenants/{id}/rent-override) in backend/src/api/v1/tenants.py
- [ ] T197 [US10] Implement rent history endpoint (GET /api/v1/tenants/{id}/rent-history) in backend/src/api/v1/tenants.py
- [ ] T198 [US10] Create Celery task for daily rent increment check in backend/src/tasks/rent_tasks.py
- [ ] T199 [US10] Add rent increment notification 30 days before in backend/src/tasks/notification_tasks.py
- [ ] T200 [US10] Create rent policy configuration screen in mobile/lib/screens/tenants/rent_policy_screen.dart
- [ ] T201 [US10] Create rent history view in tenant detail screen in mobile/lib/screens/tenants/tenant_detail_screen.dart
- [ ] T202 [US10] Add manual rent override UI in mobile/lib/screens/tenants/rent_override_screen.dart

**Checkpoint**: At this point, automatic rent increment system is operational

---

## Phase 13: User Story 11 - Tenant Exports Personal Payment History (Priority: P3)

**Goal**: Tenant needs payment records for personal accounting and exports complete payment history to Excel with one click

**Independent Test**: Select date range → click export → download Excel file, delivering instant record access

### Implementation for User Story 11

- [ ] T203 [US11] Implement Excel export service using openpyxl in backend/src/services/export_service.py
- [ ] T204 [US11] Implement PDF export service using ReportLab in backend/src/services/export_service.py
- [ ] T205 [US11] Implement payment history export endpoint (POST /api/v1/payments/export) in backend/src/api/v1/payments.py
- [ ] T206 [US11] Add date range filtering to export endpoint in backend/src/api/v1/payments.py
- [ ] T207 [US11] Add format selection (Excel/PDF) to export endpoint in backend/src/api/v1/payments.py
- [ ] T208 [US11] Create export screen with date range picker in mobile/lib/screens/exports/export_screen.dart
- [ ] T209 [US11] Implement file download and sharing in mobile in mobile/lib/services/file_service.dart
- [ ] T210 [US11] Add export history tracking in mobile/lib/providers/export_provider.dart

**Checkpoint**: At this point, tenants can export their payment history

---

## Phase 14: User Story 12 - User Switches App Language (Priority: P3)

**Goal**: Hindi-speaking tenant changes app language to Hindi in settings, and all UI text displays in Hindi with proper number/currency formatting

**Independent Test**: Change language → view screens → verify translations → check RTL for Arabic, delivering localized experience

### Implementation for User Story 12

- [ ] T211 [P] [US12] Setup Flutter localization with l10n.yaml in mobile/
- [ ] T212 [P] [US12] Create English translations in mobile/lib/l10n/app_en.arb
- [ ] T213 [P] [US12] Create Hindi translations in mobile/lib/l10n/app_hi.arb
- [ ] T214 [P] [US12] Create Spanish translations in mobile/lib/l10n/app_es.arb
- [ ] T215 [US12] Configure RTL support for Arabic/Hebrew in mobile/lib/main.dart
- [ ] T216 [US12] Create language provider with locale state in mobile/lib/providers/language_provider.dart
- [ ] T217 [US12] Create language selection screen in mobile/lib/screens/settings/language_settings_screen.dart
- [ ] T218 [US12] Implement number/currency formatting per locale in mobile/lib/utils/formatters.dart
- [ ] T219 [US12] Create language-specific message templates in backend/src/services/message_service.py
- [ ] T220 [US12] Add language preference to User model in backend/src/models/user.py
- [ ] T221 [US12] Implement English fallback for missing translations in mobile/lib/l10n/

**Checkpoint**: At this point, multi-language support is functional

---

## Phase 15: User Story 13 - Owner Generates Annual Tax Report (Priority: P3)

**Goal**: Owner generates annual tax statement with total rent income, deductible expenses, and tax form for filing with accountant

**Independent Test**: Select financial year → generate report → export with tax calculations, delivering tax-ready reports

### Implementation for User Story 13

- [ ] T222 [P] [US13] Create ReportTemplate model with template config in backend/src/models/report.py
- [ ] T223 [US13] Create Alembic migration for ReportTemplate table in backend/alembic/versions/
- [ ] T224 [US13] Implement tax calculation service in backend/src/services/report_service.py
- [ ] T225 [US13] Implement annual income statement endpoint (GET /api/v1/reports/tax/income) in backend/src/api/v1/reports.py
- [ ] T226 [US13] Implement expense deduction report endpoint (GET /api/v1/reports/tax/deductions) in backend/src/api/v1/reports.py
- [ ] T227 [US13] Implement GST/VAT report endpoint (GET /api/v1/reports/tax/gst) in backend/src/api/v1/reports.py
- [ ] T228 [US13] Implement profit/loss statement endpoint (GET /api/v1/reports/financial/pnl) in backend/src/api/v1/reports.py
- [ ] T229 [US13] Implement cash flow report endpoint (GET /api/v1/reports/financial/cashflow) in backend/src/api/v1/reports.py
- [ ] T230 [US13] Implement report scheduling endpoint (POST /api/v1/reports/schedule) in backend/src/api/v1/reports.py
- [ ] T231 [US13] Create Celery task for scheduled report generation in backend/src/tasks/report_tasks.py
- [ ] T232 [US13] Create tax report screen with year selector in mobile/lib/screens/reports/tax_report_screen.dart
- [ ] T233 [US13] Create financial report screen with report type selector in mobile/lib/screens/reports/financial_report_screen.dart
- [ ] T234 [US13] Implement secure share link generation in backend/src/services/report_service.py

**Checkpoint**: At this point, comprehensive tax reporting is functional

---

## Phase 16: User Story 14 - Intermediary Receives Push Notification for Payment (Priority: P3)

**Goal**: When tenant completes online payment, intermediary immediately receives push notification on mobile with payment details

**Independent Test**: Complete payment → see notification → tap to view details, delivering instant alerts

### Implementation for User Story 14

- [ ] T235 [P] [US14] Create Notification model with title, body, type, read_status in backend/src/models/notification.py
- [ ] T236 [US14] Create Alembic migration for Notification table in backend/alembic/versions/
- [ ] T237 [P] [US14] Create notification request/response schemas in backend/src/schemas/notification.py
- [ ] T238 [US14] Implement FCM push notification service in backend/src/services/notification_service.py
- [ ] T239 [US14] Implement notification creation endpoint (POST /api/v1/notifications) in backend/src/api/v1/notifications.py
- [ ] T240 [US14] Implement notification list endpoint (GET /api/v1/notifications) in backend/src/api/v1/notifications.py
- [ ] T241 [US14] Implement notification mark-read endpoint (PATCH /api/v1/notifications/{id}/read) in backend/src/api/v1/notifications.py
- [ ] T242 [US14] Add payment confirmation notification trigger in backend/src/services/payment_service.py
- [ ] T243 [US14] Add bill allocation notification trigger in backend/src/services/bill_service.py
- [ ] T244 [US14] Add document upload notification trigger in backend/src/services/document_service.py
- [ ] T245 [P] [US14] Setup Firebase Cloud Messaging in mobile in mobile/lib/services/fcm_service.dart
- [ ] T246 [US14] Create notification provider in mobile/lib/providers/notification_provider.dart
- [ ] T247 [US14] Create in-app notification center screen in mobile/lib/screens/notifications/notification_center_screen.dart
- [ ] T248 [US14] Implement notification tap handling and deep linking in mobile/lib/services/notification_handler.dart
- [ ] T249 [US14] Create notification preferences screen with quiet hours in mobile/lib/screens/settings/notification_settings_screen.dart
- [ ] T250 [US14] Implement notification badge count on app icon in mobile/lib/main.dart
- [ ] T251 [US14] Implement notification grouping by type in mobile/lib/screens/notifications/notification_center_screen.dart
- [ ] T252 [US14] Implement RLS policies for notifications table in backend/alembic/versions/

**Checkpoint**: At this point, real-time push notifications are fully functional

---

## Phase 17: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T253 [P] Add comprehensive API documentation in backend/docs/api.md
- [ ] T254 [P] Create deployment guide in backend/docs/deployment.md
- [ ] T255 [P] Create mobile app user manual in mobile/docs/user-guide.md
- [ ] T256 Code cleanup and refactoring across backend services
- [ ] T257 Code cleanup and refactoring across mobile screens
- [ ] T258 [P] Performance optimization: add database indexes for frequent queries
- [ ] T259 [P] Performance optimization: implement response caching with Redis
- [ ] T260 [P] Performance optimization: optimize mobile database queries
- [ ] T261 [P] Security audit: verify all RLS policies are correct
- [ ] T262 [P] Security audit: check for SQL injection vulnerabilities
- [ ] T263 [P] Security audit: verify JWT token validation everywhere
- [ ] T264 [P] Add input validation to all API endpoints
- [ ] T265 [P] Add error logging to all exception handlers
- [ ] T266 [P] Setup monitoring and alerting with Sentry
- [ ] T267 Run through complete quickstart.md validation
- [ ] T268 Test all 14 user stories end-to-end
- [ ] T269 [P] Create demo data seeding script in backend/scripts/seed_demo_data.py
- [ ] T270 [P] Create backup and restore scripts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-16)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 (P1) → US2 (P1) → US3 (P2) → US4 (P2) → US7 (P2) → US5-6, US8-14 (P3)
- **Polish (Phase 17)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories ✅ MVP READY
- **User Story 2 (P1)**: Can start after Foundational - Depends on US1 (needs Tenant model)
- **User Story 3 (P2)**: Can start after Foundational - Depends on US1 (needs Tenant model)
- **User Story 4 (P2)**: Can start after US2, US6 (needs Payment and Expense data)
- **User Story 5 (P3)**: Can start after US2 (extends payment functionality)
- **User Story 6 (P3)**: Can start after Foundational - Independent
- **User Story 7 (P2)**: Can start after US1, US2, US3 (needs data to sync)
- **User Story 8 (P3)**: Can start after US1 (needs Tenant model)
- **User Story 9 (P3)**: Can start after US1 (needs Tenant model)
- **User Story 10 (P3)**: Can start after US1 (modifies Tenant model)
- **User Story 11 (P3)**: Can start after US2 (exports Payment data)
- **User Story 12 (P3)**: Can start after Foundational - Independent
- **User Story 13 (P3)**: Can start after US2, US6 (needs financial data)
- **User Story 14 (P3)**: Can start after US2, US3, US9 (needs events to notify)

### Within Each User Story

- Models before services
- Services before endpoints
- Backend endpoints before mobile screens
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Within Setup (Phase 1):**

- T004 (Flutter init), T005 (Python linting), T006 (Dart linting), T008 (backend .env), T009 (mobile env) can all run in parallel

**Within Foundational (Phase 2):**

- T012 (password hashing), T013 (JWT), T015 (CORS), T016 (logging), T018 (schemas), T019 (SQLite), T020 (secure storage), T021 (Dio), T023 (config) can all run in parallel

**Across User Stories (after Foundational):**

- Once Foundational is complete, multiple developers can work on different user stories simultaneously:
  - Developer A: US1 (foundational user/tenant management)
  - Developer B: US6 (expense tracking - independent)
  - Developer C: US12 (localization - independent)

**Within User Story 1:**

- T024, T025, T026, T027 (all models) in parallel
- T029, T030, T031, T032 (all schemas) in parallel
- T040, T041, T042 (mobile models) in parallel

---

## Parallel Example: User Story 1

```bash
# After Foundational phase is complete, launch all US1 models together:
Task T024: "Create User model with role enum in backend/src/models/user.py"
Task T025: "Create Property model with owner_id FK in backend/src/models/property.py"
Task T026: "Create PropertyAssignment junction model in backend/src/models/property.py"
Task T027: "Create Tenant model with property and user FKs in backend/src/models/tenant.py"

# Then launch all US1 schemas together:
Task T029: "Create auth request/response schemas in backend/src/schemas/auth.py"
Task T030: "Create user request/response schemas in backend/src/schemas/user.py"
Task T031: "Create property request/response schemas in backend/src/schemas/property.py"
Task T032: "Create tenant request/response schemas in backend/src/schemas/tenant.py"

# Then launch mobile models together:
Task T040: "Create User model for mobile local storage in mobile/lib/models/user.dart"
Task T041: "Create Property model for mobile local storage in mobile/lib/models/property.dart"
Task T042: "Create Tenant model for mobile local storage in mobile/lib/models/tenant.dart"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

This delivers a working system that property owners can immediately use:

1. ✅ Complete Phase 1: Setup
2. ✅ Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. ✅ Complete Phase 3: User Story 1 (Owner onboarding, property setup, tenant creation)
4. ✅ Complete Phase 4: User Story 2 (Rent payment recording and receipt generation)
5. **STOP and VALIDATE**: Test US1 & US2 independently
6. **Deploy MVP**: Property owners can now register, add tenants, and track rent payments

**MVP Delivers**:

- User registration and authentication
- Property and tenant management
- Rent payment tracking with receipts
- Basic financial tracking

### Incremental Delivery (Recommended)

1. **Foundation** (Phases 1-2) → Core infrastructure ready
2. **MVP** (US1 + US2) → Deploy and gather feedback ✅
3. **Bill Management** (US3) → Add utility bill splitting → Deploy
4. **Analytics** (US4) → Add financial dashboard → Deploy
5. **Offline Sync** (US7) → Add offline reliability → Deploy
6. **Online Payments** (US5) → Add payment gateway → Deploy
7. **Remaining P3 Stories** → Add one at a time based on user feedback

Each increment adds value without breaking previous functionality!

### Parallel Team Strategy

With 3+ developers after Foundational phase:

**Team A** (Critical Path):

- US1 → US2 → US3 (Core rental management)

**Team B** (Independent Features):

- US6 (Expense tracking)
- US8 (Messaging)
- US12 (Localization)

**Team C** (Advanced Features):

- US4 (Analytics)
- US5 (Payment gateway)
- US7 (Sync - after Team A completes US1-3)

---

## Task Statistics

**Total Tasks**: 270
**Setup Phase**: 9 tasks
**Foundational Phase**: 14 tasks (BLOCKS all user stories)
**User Story Phases**: 229 tasks across 14 stories

- US1 (P1 - MVP): 32 tasks
- US2 (P1 - MVP): 19 tasks
- US3 (P2): 20 tasks
- US4 (P2): 15 tasks
- US5 (P3): 15 tasks
- US6 (P3): 16 tasks
- US7 (P2): 16 tasks
- US8 (P3): 18 tasks
- US9 (P3): 16 tasks
- US10 (P3): 12 tasks
- US11 (P3): 8 tasks
- US12 (P3): 11 tasks
- US13 (P3): 13 tasks
- US14 (P3): 18 tasks
  **Polish Phase**: 18 tasks

**Parallelizable Tasks**: 89 tasks marked [P]

**MVP Scope** (US1 + US2): 51 tasks (19% of total)
**Complete P1+P2** (US1-4, US7): 102 tasks (38% of total)

**Estimated Timeline**:

- **MVP** (US1+US2): 3-4 weeks (single developer) or 2 weeks (team of 3)
- **P1+P2 Complete**: 6-8 weeks (single developer) or 3-4 weeks (team of 3)
- **All 14 Stories**: 12-16 weeks (single developer) or 6-8 weeks (team of 3)

---

## Notes

- **[P] tasks** = different files, no dependencies within phase - can run in parallel
- **[Story] label** (US1-US14) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are OPTIONAL - not explicitly requested in spec
- All file paths follow Mobile + API project structure from plan.md
- RLS policies ensure multi-tenant data isolation at database level
- Offline sync uses last-write-wins for non-financial, append-only for financial
- All currency calculations use DECIMAL type (no FLOAT)
- Follow constitution requirements: encryption, RBAC, offline-first, audit trails
