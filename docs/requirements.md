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
    - [x] **Multi-tenancy**: Support logical isolation of data by `Organization`.
    - [x] **User Management**: Registration, Login, Profile management.
    - [x] **Group Management**: Create custom permission groups for staff.
    - [ ] **Invitation System**: Invite users to join an organization (Staff/Tenant).

### 3.2. Property Management (Housing)
* **Goal**: Centralized inventory of real estate assets.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **Properties**: Manage buildings/compounds (Name, Address, Amenities).
    - [x] **Units**: Manage individual rental units (Unit Number, Floor, Bed/Bath, Sqft, Market Rent).
    - [x] **Unit Status**: Track status (Vacant, Occupied, Under Maintenance).
    - [ ] **Unit Inspections**: Record move-in/move-out inspections with photos (Missing).
    - [ ] **Inventory Management**: Track appliances and furniture within units (Missing).

### 3.3. Tenant & Lease Management
* **Goal**: Manage tenant lifecycle and legal contracts.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **Tenant Profiles**: Personal details, Contact info, Emergency contacts, ID Proof.
    - [x] **Lease Creation**: Define start/end dates, rent amount, security deposit.
    - [x] **Lease Status**: Draft, Active, Expired, Terminated.
    - [x] **Document Storage**: Upload signed lease agreements.
    - [ ] **Lease Renewals**: Automated workflow for extending leases (Missing).
    - [ ] **Tenant Screening**: Background checks and credit scoring (Future).

### 3.4. Finance & Billing
* **Goal**: Automate revenue collection and track financial health.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **Invoicing**: Generate rent and utility invoices.
    - [x] **Payments**: Record payments (Cash, Bank Transfer, Khalti, eSewa).
    - [x] **Payment Status**: Track Pending, Success, Failed, Refunded payments.
    - [x] **Taxation**: tax calculation support.
    - [ ] **Expense Tracking**: Record property-related expenses (Maintenance, Utilities, Taxes) (Missing).
    - [ ] **Late Fees**: Automated calculation and application of late payment fees (Missing).
    - [ ] **Financial Reporting**: P&L statements per property (Missing).

### 3.5. Operations & Maintenance
* **Goal**: Maintain property value and tenant satisfaction.
* **Status**: [Partially Implemented]
* **Requirements**:
    - [x] **Work Orders**: Tenants/Staff submit requests (Title, Description, Priority).
    - [x] **Work Order Lifecycle**: Open -> In Progress -> Resolved -> Closed.
    - [x] **Notifications**: System alerts for various events (Info, Warning, Error, Success).
    - [ ] **Assignment**: Auto-assign work orders to specific vendors or staff (Missing).
    - [ ] **Vendor Management**: Database of service providers (Plumbers, Electricians) (Missing).

### 3.6. CRM & Lead Management (Leasing)
* **Goal**: Manage prospective tenants and inquiries before lease creation.
* **Status**: [New Requirement]
* **Requirements**:
    - [ ] **Lead Tracking**: Capture inquiries from website/listing portals.
    - [ ] **Applications**: Online rental application forms with custom fields.
    - [ ] **Showings**: Schedule and track property viewings.
    - [ ] **Follow-ups**: Automated email sequences for leads.

### 3.7. Scheduling & Calendar
* **Goal**: centralized view of time-sensitive activities.
* **Status**: [New Requirement]
* **Requirements**:
    - [ ] **Calendar View**: Unified view of Lease startups/endings, Maintenance visits, and Showings.
    - [ ] **Reminders**: Automated alerts for upcoming events.

### 3.8. Advanced Reporting & Analytics
* **Goal**: Data-driven insights for property performance.
* **Status**: [New Requirement]
* **Requirements**:
    - [ ] **Occupancy Reports**: Occupancy rates over time per property.
    - [ ] **Financial Statements**: Cash flow, Rent Roll, Aged Receivables.
    - [ ] **Maintenance Analytics**: Average resolution time, cost per unit.

## 4. Non-Functional Requirements

### 4.1. Security
- **Data Isolation**: Strict query filtering by `active_organization` to prevent data leaks between tenants.
- **Encryption**: HTTPS for all transit; hashing for passwords.
- **Audit Logs**: Track sensitive actions (who changed what and when).

### 4.2. Performance
- **Response Time**: API response time < 200ms for 95th percentile.
- **Scalability**: Support horizontal scaling for web servers and celery workers.

### 4.3. Usability
- **Mobile Responsive**: Dashboard must be fully usable on mobile devices.
- **Localization**: Support for English and Nepali languages (Future).

## 5. System Interfaces

### 5.1. Payment Gateways
- **Khalti**: Integrated for online wallet payments.
- **eSewa**: Planned integration.
- **ConnectIPS**: Connect to bank APIs for direct transfers (Future).

### 5.2. Notifications
- **Email**: Send invoices and reset passwords (SMTP/SendGrid).
- **SMS**: Critical alerts (Future).
