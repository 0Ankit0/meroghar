# Requirements Document

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for MeroGhar — a house and property rental platform that enables landlords and property managers to manage their entire rental business from a single system, while providing tenants with a seamless experience to find, lease, and manage rental properties.

### 1.2 Scope
The system will support:
- Property listing and availability management across property types (Apartment, House, Room, Studio, Villa, Commercial Space)
- Tenant rental application and lease agreement workflows
- Digital lease agreement creation and signing
- Flexible pricing (daily/weekly for short-term stays; monthly rent for long-term leases; peak pricing)
- Security deposit collection, hold, deduction, and refund
- Move-in and move-out property inspections
- Invoice generation, online rent payment collection, and overdue fee handling
- Property maintenance and servicing lifecycle
- Financial reporting and analytics for landlords and property managers
- Admin platform management and dispute resolution

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Property** | Any rental property listed on the platform (apartment, house, room, studio, villa, commercial space) |
| **Property Type** | A classification grouping similar properties (Apartment, House, Room, Studio, Villa, Commercial Space) |
| **Listing** | A published property made available for tenant discovery and rental applications |
| **Rental Application / Booking** | A tenant's request to rent a property for a specified period |
| **Rental Period** | The confirmed start and end date of a tenancy |
| **Lease Agreement / Tenancy Agreement** | A formal contract between the landlord and tenant for a rental period |
| **Pricing Rule** | A rate definition for a property (daily/weekly for short-term; monthly for long-term tenancy) |
| **Security Deposit** | A refundable amount collected at lease confirmation |
| **Property Inspection** | A move-in or move-out inspection of a property's condition with photo evidence |
| **Additional Charge** | Any fee beyond the base rental rate (damage, late payment, cleaning, etc.) |
| **Handover / Return** | The process of a tenant receiving or handing back a property at the start or end of the tenancy |

---

## 2. Functional Requirements

### 2.1 User Management Module

#### FR-UM-001: Landlord / Property Owner Registration
- System shall allow landlords and property owners to register with email or phone
- System shall support business profile creation with trading name and contact details
- System shall require identity and (optionally) business document verification
- System shall enforce OTP-based email/phone verification

#### FR-UM-002: Tenant Registration
- System shall allow tenants to create accounts via email or phone
- System shall collect basic profile information (name, ID, payment method)
- System shall support social login (Google, Apple)
- System shall support OTP-based phone verification

#### FR-UM-003: Staff / Property Manager Management
- Landlords shall add staff members to their account (e.g., property managers, maintenance staff)
- System shall support role assignment per staff member (inspection, maintenance, tenant relations)
- System shall maintain staff availability schedules

#### FR-UM-004: Admin Management
- System shall support role-based access control (RBAC) for admin users
- System shall maintain admin activity audit logs
- System shall support 2FA for all admin accounts

#### FR-UM-005: Authentication
- System shall implement JWT-based authentication with refresh tokens
- System shall support session management and concurrent device limits
- System shall enforce password complexity policies and account lockout

---

### 2.2 Property & Listing Management Module

#### FR-AL-001: Property Type Management
- Landlords shall define or select property types (Apartment, House, Room, Studio, Villa, Commercial Space)
- Each property type shall support configurable custom attribute fields (e.g., number of bedrooms, bathrooms, floor area in sqft/sqm, furnishing status, parking availability, balcony)
- Admins shall manage the global property type taxonomy

#### FR-AL-002: Property Creation
- Landlords shall create property listings with a name, description, property type, photos, and property features/amenities
- System shall support multiple photos and a cover image per property
- System shall track property registration numbers or land registry identifiers where applicable

#### FR-AL-003: Pricing Configuration
- Landlords shall define flexible pricing rules per property: daily/weekly rates for short-term stays, monthly rent for long-term leases
- System shall support peak pricing windows and seasonal rate adjustments
- System shall support minimum and maximum rental duration constraints
- Landlords shall configure security deposit amounts per property

#### FR-AL-004: Availability Management
- Landlords shall set property availability windows on a calendar
- System shall block out dates when a property is rented, under maintenance, or manually unavailable
- System shall support recurring unavailability

#### FR-AL-005: Listing Publication
- Landlords shall publish or unpublish properties for tenant browsing
- System shall support drafts before publication
- Landlords shall configure application lead time (e.g., must apply at least 24 hours in advance)

#### FR-AL-006: Property Documents
- Landlords shall upload property-level documents (ownership certificates, inspection certificates, floor plans)
- System shall store documents securely and link them to the property
- Landlords shall share specific documents with tenants at lease confirmation

---

### 2.3 Rental Application & Tenancy Module

#### FR-BR-001: Property Search & Discovery
- Tenants shall search available properties by property type, location, date range, and price
- System shall display a real-time availability calendar per property
- System shall show pricing breakdown for the selected period

#### FR-BR-002: Rental Application Submission
- Tenants shall submit a rental application for an available property and period
- System shall capture selected rental period, move-in preference, and special requests
- System shall place a temporary hold on the property's availability upon application submission

#### FR-BR-003: Application Confirmation
- Landlords shall approve or decline rental applications (for manual confirmation mode)
- System shall support instant booking mode where applications are auto-confirmed if the property is available
- System shall collect the security deposit upon lease confirmation
- System shall notify both parties of the confirmed tenancy

#### FR-BR-004: Tenancy Modification
- Tenants shall request changes to tenancy dates before the rental period starts
- Landlords shall approve or decline modification requests
- System shall recalculate the price difference and process additional charges or refunds

#### FR-BR-005: Tenancy Cancellation
- Tenants and landlords shall cancel tenancies subject to the configured cancellation policy
- System shall calculate and apply cancellation fees per policy
- System shall process refunds (full, partial, or none) based on the policy tier
- System shall release the property's availability upon cancellation

---

### 2.4 Lease Agreement Module

#### FR-RA-001: Agreement Generation
- System shall generate a lease agreement from a configurable template upon rental confirmation
- Agreement shall capture property details, rental period, pricing, deposit, policies, and liability terms
- System shall support landlord-defined custom clauses per property type

#### FR-RA-002: Digital Signing
- System shall send the lease agreement to the tenant for digital e-signature
- System shall record the signature timestamp and IP address
- System shall generate a signed PDF copy for both parties and store it securely
- Landlords shall countersign before the tenancy begins

#### FR-RA-003: Agreement Amendments
- Landlords shall issue an amendment agreement for tenancy modifications
- Amendment shall be re-signed by both parties
- System shall version-control all agreement revisions

---

### 2.5 Payment & Invoice Module

#### FR-PI-001: Invoice Generation
- System shall generate invoices automatically on lease confirmation and at each rent due date
- Invoices shall include base rental fee, applicable taxes, and any additional charges
- System shall support prorated billing for partial periods

#### FR-PI-002: Payment Collection
- Tenants shall pay via the platform (card, bank transfer, wallet, buy-now-pay-later)
- System shall integrate multiple payment gateways
- System shall collect security deposits as a separate hold or charge
- System shall send payment confirmation receipts

#### FR-PI-003: Additional Charges
- Landlords shall add post-tenancy charges (damage, late payment, cleaning)
- System shall notify tenants of additional charges before processing
- System shall allow tenants to dispute additional charges

#### FR-PI-004: Refunds
- System shall process security deposit refunds within a configurable window after move-out
- System shall process tenancy cancellation refunds per the cancellation policy
- System shall track all refund transactions

#### FR-PI-005: Overdue & Late Payment Fees
- System shall detect late rent payments and auto-calculate overdue fees per the property's configured late-payment policy
- System shall notify both the tenant and landlord of a detected overdue payment
- System shall apply the overdue fee to the tenant's outstanding balance

#### FR-PI-006: Payout to Landlords
- System shall calculate net payouts after platform commission deduction
- System shall process scheduled payouts to landlord bank accounts
- System shall provide landlords with a payout history and settlement export

---

### 2.6 Property Inspection Module

#### FR-CA-001: Move-In Inspection
- Staff or landlords shall complete a property inspection before handing over the property to the tenant
- Inspection shall capture property condition per property-type-specific checklist items (walls, flooring, fixtures, appliances, etc.)
- Inspection shall include timestamped photos
- Tenant shall countersign the move-in inspection report

#### FR-CA-002: Move-Out Inspection
- Staff or landlords shall complete a property inspection upon tenant move-out
- System shall compare move-out against move-in condition to highlight discrepancies
- Inspection shall include timestamped photos as evidence
- System shall prompt the landlord to raise damage charges based on inspection findings

#### FR-CA-003: Inspection Reports
- System shall generate a PDF inspection report for each inspection
- Both parties shall receive a copy of the completed inspection report
- Inspection reports shall be stored and linked to the tenancy

---

### 2.7 Maintenance & Servicing Module

#### FR-MS-001: Maintenance Request Logging
- Landlords, property managers, and tenants shall log maintenance requests for properties (damage, repairs, servicing)
- System shall assign a unique request ID and notify relevant staff
- System shall track the property's maintenance status without blocking availability unless critical

#### FR-MS-002: Maintenance Assignment
- Landlords shall assign requests to internal staff or external contractors
- System shall track assignment acceptance and task status updates
- Landlords shall approve completed maintenance before marking the property as serviced

#### FR-MS-003: Maintenance Scheduling
- Landlords shall schedule preventive servicing (plumbing checks, electrical safety inspections, pest control)
- System shall send reminders before scheduled service dates
- System shall log all service history per property

#### FR-MS-004: Maintenance Costs
- Landlords shall log costs (labour, parts, contractor fees) against maintenance requests
- Costs shall be included in property expense reports and financial summaries

---

### 2.8 Reporting & Analytics Module

#### FR-RP-001: Landlord Dashboard
- Landlords shall view total rental income, outstanding balances, active tenancies, and property occupancy rates
- Dashboard shall show property-level and portfolio-level performance metrics
- System shall provide month-over-month and year-over-year comparisons

#### FR-RP-002: Revenue & Expense Reports
- System shall generate revenue reports per property, property type, or full portfolio
- System shall categorise expenses (maintenance, commissions, insurance)
- System shall export reports to PDF and CSV

#### FR-RP-003: Tenancy & Occupancy Reports
- System shall report tenancy counts, occupancy rates, and vacancy periods per property
- System shall show peak demand periods and average tenancy durations

#### FR-RP-004: Tax Reports
- System shall generate annual rental income summaries for tax filing purposes
- System shall list deductible expenses per property
- System shall export to common accounting formats (CSV, PDF)

---

### 2.9 Notification Module

#### FR-NM-001: Email Notifications
- System shall send transactional emails for all key events (application, lease agreement, payment, move-in/move-out)
- System shall support configurable email templates per event type

#### FR-NM-002: SMS Notifications
- System shall send SMS for lease confirmations, rent reminders, and urgent alerts (overdue payment)
- System shall manage SMS quotas per account tier

#### FR-NM-003: In-App / Push Notifications
- System shall display real-time in-app notifications for all key events
- System shall support notification preference management per user
- System shall deliver real-time push via WebSocket for dashboard updates

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Requirement | Target |
|-------------|--------|
| API response time | < 300ms (p95) |
| Availability calendar load | < 500ms |
| Dashboard load time | < 2 seconds |
| Concurrent users | 50,000+ |
| File upload size | Up to 50 MB per file |

### 3.2 Scalability
- Horizontal scaling of all application services
- Database read replicas for analytics and reporting queries
- Auto-scaling based on traffic patterns
- CDN for property photos, documents, and report exports

### 3.3 Availability
- 99.9% uptime SLA
- Zero-downtime deployments
- Multi-AZ database deployment
- Graceful degradation of non-critical features

### 3.4 Security
- HTTPS/TLS 1.3 for all communications
- Encrypted storage of sensitive documents (lease agreements, IDs, inspection reports)
- PCI-DSS compliance for payment data
- GDPR and regional data privacy compliance
- Role-based access — tenants cannot view other tenants' data
- Audit logs for all financial, tenancy, and agreement actions
- Rate limiting and brute-force protection

### 3.5 Reliability
- Idempotent payment processing to prevent duplicate charges
- Transaction-safe tenancy creation and deposit operations
- Automated daily database backups with point-in-time recovery
- Circuit breaker patterns for payment gateway and e-signature calls

### 3.6 Maintainability
- Modular service-oriented architecture with pluggable property type adapters
- Comprehensive structured logging
- Distributed tracing for cross-service requests
- Health-check endpoints on all services
- Feature flags for gradual feature rollouts

### 3.7 Usability
- Mobile-responsive web interface for landlords and tenants
- Dedicated mobile app for tenants and property managers
- WCAG 2.1 AA accessibility compliance
- Multi-language and multi-currency support

---

## 4. System Constraints

### 4.1 Technical Constraints
- Cloud-native deployment (AWS / GCP / Azure)
- Container-based deployment (Docker / Kubernetes)
- Event-driven architecture for async operations (notifications, reports, billing)
- API-first design (REST / OpenAPI 3.0)
- Pluggable property type schema — custom attributes defined per property type without schema migrations

### 4.2 Business Constraints
- Multi-currency support for international operations
- Tax rule configuration per jurisdiction
- Support for individual landlords and multi-property portfolio operators
- Integration with external e-signature providers (DocuSign, Adobe Sign)
- White-label support for enterprise property management companies running branded platforms

### 4.3 Regulatory Constraints
- Compliance with consumer protection and tenancy regulations per jurisdiction
- Secure storage and handling of government-issued ID documents
- Payment data security (PCI-DSS)
- Data residency requirements for certain regions
