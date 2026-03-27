# MeroGhar - House Rental Management System Requirements

## 1. Introduction
MeroGhar is an enterprise-grade SaaS platform designed to streamline property management operations for the Nepalese market. It serves property managers, landlords, and tenants by automating leasing, billing, maintenance, and communication.

## 2. User Roles & Permissions
The system supports a Role-Based Access Control (RBAC) model managed via the IAM module.

### 2.1. System Administrator (Superuser)
- Full access to all system configurations and organizations.
- Manage global settings and subscription plans.

### 2.2. Organization Owner (Property Manager/Landlord)
- Manage organization details and staff.
- Full access to properties, tenants, and financials within their organization.
- Configure organization-specific settings (payment gateways, notification preferences).

### 2.3. Staff
- Restricted access based on assigned groups (e.g., Maintenance Staff, Leasing Agent, Accountant).
- **Maintenance Staff**: Can view and update work orders.
- **Leasing Agent**: Can manage listings, showings, and draft leases.
- **Accountant**: Can manage invoices, payments, and expenses.

### 2.4. Tenant
- View lease details and documents.
- View and pay invoices (Rent/Utilities).
- Submit and track maintenance work orders.
- Receive notifications.

## 3. Functional Requirements

### 3.1. Identity & Access Management (IAM)
* **Goal**: Secure multi-tenant access and organization management.
* **Status**: [Implemented]
* **Requirements**:
    - [x] **IAM-01 — Multi-tenancy**: Support logical isolation of data by `Organization`.
    - [x] **IAM-02 — User Management**: Registration, Login, Profile management.
    - [x] **IAM-03 — Group Management**: Create custom permission groups for staff.
    - [ ] **IAM-04 — Invitation System**: Invite users to join an organization (Staff/Tenant).

### 3.2. Property Management (Housing)
* **Goal**: Centralized inventory of real estate assets.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **HOU-01 — Properties**: Manage buildings/compounds (Name, Address, Amenities).
    - [x] **HOU-02 — Units**: Manage individual rental units (Unit Number, Floor, Bed/Bath, Sqft, Market Rent).
    - [x] **HOU-03 — Unit Status**: Track status (Vacant, Occupied, Under Maintenance).
    - [ ] **HOU-04 — Unit Inspections**: Record move-in/move-out inspections with photos (Missing).
    - [ ] **HOU-05 — Inventory Management**: Track appliances and furniture within units (Missing).

### 3.3. Tenant & Lease Management
* **Goal**: Manage tenant lifecycle and legal contracts.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **TEN-01 — Tenant Profiles**: Personal details, Contact info, Emergency contacts, ID Proof.
    - [x] **TEN-02 — Lease Creation**: Define start/end dates, rent amount, security deposit.
    - [x] **TEN-03 — Lease Status**: Draft, Active, Expired, Terminated.
    - [x] **TEN-04 — Document Storage**: Upload signed lease agreements.
    - [ ] **TEN-05 — Lease Renewals**: Automated workflow for extending leases (Missing).
    - [ ] **TEN-06 — Tenant Screening**: Background checks and credit scoring (Future).

### 3.4. Finance & Billing
* **Goal**: Automate revenue collection and track financial health.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **FIN-01 — Invoicing**: Generate rent and utility invoices.
    - [x] **FIN-02 — Payments**: Record payments (Cash, Bank Transfer, Khalti, eSewa).
    - [x] **FIN-03 — Payment Status**: Track Pending, Success, Failed, Refunded payments.
    - [x] **FIN-04 — Taxation**: Tax calculation support.
    - [ ] **FIN-05 — Expense Tracking**: Record property-related expenses (Maintenance, Utilities, Taxes) (Missing).
    - [ ] **FIN-06 — Late Fees**: Automated calculation and application of late payment fees (Missing).
    - [ ] **FIN-07 — Financial Reporting**: P&L statements per property (Missing).

### 3.5. Operations & Maintenance
* **Goal**: Maintain property value and tenant satisfaction.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **OPS-01 — Work Orders**: Tenants/Staff submit requests (Title, Description, Priority).
    - [x] **OPS-02 — Work Order Lifecycle**: Open -> In Progress -> Resolved -> Closed.
    - [x] **OPS-03 — Notifications**: System alerts for various events (Info, Warning, Error, Success).
    - [ ] **OPS-04 — Assignment**: Auto-assign work orders to specific vendors or staff (Missing).
    - [ ] **OPS-05 — Vendor Management**: Database of service providers (Plumbers, Electricians) (Missing).

### 3.6. CRM & Lead Management (Leasing)
* **Goal**: Manage prospective tenants and inquiries before lease creation.
* **Status**: [New Requirement]
* **Requirements**:
    - [ ] **CRM-01 — Lead Tracking**: Capture inquiries from website/listing portals.
    - [ ] **CRM-02 — Applications**: Online rental application forms with custom fields.
    - [ ] **CRM-03 — Showings**: Schedule and track property viewings.
    - [ ] **CRM-04 — Follow-ups**: Automated email sequences for leads.

### 3.7. Scheduling & Calendar
* **Goal**: centralized view of time-sensitive activities.
* **Status**: [New Requirement]
* **Requirements**:
    - [ ] **SCH-01 — Calendar View**: Unified view of Lease startups/endings, Maintenance visits, and Showings.
    - [ ] **SCH-02 — Reminders**: Automated alerts for upcoming events.

### 3.8. Advanced Reporting & Analytics
* **Goal**: Data-driven insights for property performance.
* **Status**: [New Requirement]
* **Requirements**:
    - [ ] **RPT-01 — Occupancy Reports**: Occupancy rates over time per property.
    - [ ] **RPT-02 — Financial Statements**: Cash flow, Rent Roll, Aged Receivables.
    - [ ] **RPT-03 — Maintenance Analytics**: Average resolution time, cost per unit.

## 4. Requirement-to-Test Traceability

The current test-suite uses inline `Requirement coverage:` comments in `apps/*/tests/test_*.py` to make requirement coverage explicit.

| Requirement IDs | Current test trace |
| --- | --- |
| IAM-01, IAM-02, IAM-03 | `apps/iam/tests/test_api.py`, `apps/iam/tests/test_models.py`, `apps/iam/tests/test_views.py` |
| IAM-04 | Planned (feature not implemented) |
| HOU-01, HOU-02, HOU-03 | `apps/housing/tests/test_views.py`, `apps/housing/tests/test_models.py` |
| HOU-04, HOU-05 | `apps/housing/tests/test_api.py`, `apps/housing/tests/test_models.py` |
| TEN-01, TEN-02, TEN-03, TEN-04 | `apps/housing/tests/test_models.py`, `apps/reporting/tests/test_api.py` |
| TEN-05, TEN-06 | Planned (feature not implemented) |
| FIN-01, FIN-02, FIN-03, FIN-04, FIN-05 | `apps/finance/tests/test_models.py`, `apps/finance/tests/test_api.py`, `apps/finance/tests/test_views.py`, `apps/reporting/tests/test_api.py` |
| FIN-06, FIN-07 | Planned (feature not implemented) |
| OPS-01, OPS-02, OPS-03, OPS-05 | `apps/operations/tests/test_models.py`, `apps/operations/tests/test_api.py`, `apps/operations/tests/test_views.py` |
| OPS-04 | Planned (feature not implemented) |
| CRM-01, CRM-02, CRM-03 | `apps/crm/tests/test_models.py`, `apps/crm/tests/test_api.py`, `apps/crm/tests/test_views.py` |
| CRM-04 | Planned (feature not implemented) |
| SCH-01, SCH-02 | Planned (feature not implemented) |
| RPT-01, RPT-02, RPT-03 | `apps/reporting/tests/test_api.py` (partial), additional reporting tests planned |

## 5. Non-Functional Requirements

### 5.1. Security
- **Data Isolation**: Strict query filtering by `active_organization` to prevent data leaks between tenants.
- **Encryption**: HTTPS for all transit; hashing for passwords.
- **Audit Logs**: Track sensitive actions (who changed what and when).

### 5.2. Performance
- **Response Time**: API response time < 200ms for 95th percentile.
- **Scalability**: Support horizontal scaling for web servers and celery workers.

### 5.3. Usability
- **Mobile Responsive**: Dashboard must be fully usable on mobile devices.
- **Localization**: Support for English and Nepali languages (Future).

## 6. System Interfaces

### 6.1. Payment Gateways
- **Khalti**: Integrated for online wallet payments.
- **eSewa**: Planned integration.
- **ConnectIPS**: Connect to bank APIs for direct transfers (Future).

### 6.2. Notifications
- **Email**: Send invoices and reset passwords (SMTP/SendGrid).
- **SMS**: Critical alerts (Future).
