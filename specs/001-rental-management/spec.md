# Feature Specification: Meroghar Rental Management System

**Feature Branch**: `001-rental-management`  
**Created**: 2025-10-26  
**Status**: Draft  
**Input**: User description: "Build a comprehensive house rental management system with 16 features including user management, tenant profiles, payment tracking, bill management, expense tracking, rent increments, data sync, exports, messaging, settings, document storage, payment gateways, analytics, push notifications, multi-language support, and tax reporting"

## Clarifications

### Session 2025-10-26

- Q: For offline sync conflict resolution, should financial transactions (payments, bills) use last-write-wins or a safer append-only approach? → A: Append-only for financial transactions with manual conflict resolution UI (asks user for manual input to resolve conflicts)
- Q: What happens to rent calculation when a tenant moves in mid-month? → A: Pro-rated rent for first month based on days occupied, then full monthly rent thereafter (tenant only pays for days stayed)
- Q: How many days in advance should rent payment reminders be sent, and should there be multiple reminders? → A: Configurable reminder schedule with default: 7 days before, 3 days before, and on due date (owner/intermediary can customize schedule)
- Q: Can intermediaries manage multiple properties or is each intermediary tied to a single property? → A: Intermediary can manage multiple properties assigned by owner (owner has full control over property assignments)
- Q: Should properties support multiple currencies simultaneously or single currency per property? → A: Single currency per property (set at property creation), but dashboard and analytics charts allow viewing monetary data in different currency formats using real-time exchange rates for display purposes only

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Owner Onboards Property and First Tenant (Priority: P1)

A property owner registers in the system, sets up their property details, creates an intermediary account to manage the property, and the intermediary creates the first tenant account with rent details.

**Why this priority**: This is the foundational workflow that enables all other features. Without users, properties, and tenants, no other functionality can be tested or used.

**Independent Test**: Can be fully tested by completing user registration → property setup → tenant creation → viewing tenant in list, delivering a working system that tracks who lives where.

**Acceptance Scenarios**:

1. **Given** no existing account, **When** owner registers with email and password, **Then** owner account is created with full access permissions
2. **Given** owner is logged in, **When** owner creates intermediary account with contact details, **Then** intermediary receives login credentials and has limited property management access
3. **Given** intermediary is logged in, **When** intermediary creates tenant with name, mobile, start date, and monthly rent, **Then** tenant receives credentials and can view their own profile
4. **Given** multiple tenants exist, **When** intermediary views tenant list, **Then** all managed tenants appear with basic info cards
5. **Given** tenant is logged in, **When** tenant views dashboard, **Then** tenant sees only their own profile and payment information

---

### User Story 2 - Intermediary Records Monthly Rent Payment (Priority: P1)

An intermediary collects rent from a tenant and records the payment in the system, generating a receipt for the tenant.

**Why this priority**: Core business function - rent collection is the primary purpose of the system. Must work from day one.

**Independent Test**: Can be fully tested by recording a payment → viewing updated balance → generating receipt, delivering immediate value for rent tracking.

**Acceptance Scenarios**:

1. **Given** tenant has outstanding rent, **When** intermediary records payment with amount, date, and method, **Then** payment is saved and tenant balance updates
2. **Given** payment is recorded, **When** intermediary generates receipt, **Then** PDF receipt shows tenant name, amount, date, and payment method
3. **Given** payment history exists, **When** tenant views their payments, **Then** all payment records appear with dates and amounts
4. **Given** rent is overdue, **When** intermediary views tenant list, **Then** overdue tenants are highlighted with visual indicators
5. **Given** intermediary collects rent, **When** intermediary records payment to owner, **Then** system tracks money owed to owner

---

### User Story 3 - Intermediary Divides Monthly Utility Bills (Priority: P2)

An intermediary receives electricity and water bills for the property and divides the costs among tenants based on percentage or fixed amount rules.

**Why this priority**: Critical for fair cost sharing but can be manually calculated initially. Automation saves significant time for multi-tenant properties.

**Independent Test**: Can be fully tested by creating bill → setting division rules → allocating to tenants → tracking payments, delivering automated bill splitting.

**Acceptance Scenarios**:

1. **Given** monthly electricity bill arrives, **When** intermediary creates bill with total amount and type, **Then** bill is recorded in system
2. **Given** bill exists, **When** intermediary sets percentage division (e.g., 40%, 30%, 30%), **Then** system calculates individual amounts for each tenant
3. **Given** bill is allocated, **When** tenants view their dashboard, **Then** each tenant sees their bill share with due date
4. **Given** tenant pays bill share, **When** intermediary marks payment, **Then** tenant's bill status updates to paid
5. **Given** bill type is recurring, **When** month ends, **Then** system automatically creates next month's bill

---

### User Story 4 - Owner Views Financial Analytics (Priority: P2)

A property owner views interactive dashboard with rent collection trends, expense breakdown, and revenue vs. expenses comparison to understand property performance.

**Why this priority**: Essential for business decisions and ROI tracking, but property can operate without it initially using manual reports.

**Independent Test**: Can be fully tested by recording transactions → viewing dashboard with charts → exporting data, delivering instant business insights.

**Acceptance Scenarios**:

1. **Given** payment history exists, **When** owner views analytics dashboard, **Then** rent collection trends appear in line/bar charts
2. **Given** expenses are recorded, **When** owner views expense breakdown, **Then** pie chart shows categories with percentages
3. **Given** multiple months of data, **When** owner selects date range, **Then** charts update to show filtered period
4. **Given** dashboard is loaded, **When** owner clicks on chart element, **Then** detailed data appears for that element
5. **Given** analytics are displayed, **When** owner exports report, **Then** PDF/Excel file contains all chart data

---

### User Story 5 - Tenant Pays Rent Online via Payment Gateway (Priority: P3)

A tenant receives rent reminder notification, opens the app, and pays rent directly using Khalti (Nepal's leading digital wallet and payment gateway).

**Why this priority**: Convenience feature that reduces collection delays but offline payments are sufficient initially. Nepal-specific payment gateway integration required.

**Independent Test**: Can be fully tested by tenant selecting payment → entering Khalti PIN/credentials → receiving confirmation → seeing updated balance, delivering frictionless payments.

**Acceptance Scenarios**:

1. **Given** rent is due, **When** tenant receives payment reminder notification, **Then** notification shows amount due and quick pay link
2. **Given** tenant opens app, **When** tenant clicks pay rent, **Then** payment gateway options appear (Khalti, eSewa, IME Pay)
3. **Given** tenant selects payment method, **When** tenant completes payment, **Then** payment confirmation appears and receipt is auto-generated
4. **Given** payment is processed, **When** system receives webhook confirmation, **Then** transaction record is created with gateway ID
5. **Given** payment fails, **When** tenant retries, **Then** previous failed transaction is marked and new attempt is initiated

---

### User Story 6 - Intermediary Tracks Maintenance Expenses (Priority: P3)

An intermediary pays for property maintenance (painting, plumbing repair) and records the expense with receipt photo for owner reimbursement tracking.

**Why this priority**: Important for complete financial records but can be tracked manually initially in spreadsheets.

**Independent Test**: Can be fully tested by recording expense → uploading receipt → categorizing → viewing in reports, delivering expense accountability.

**Acceptance Scenarios**:

1. **Given** maintenance work is done, **When** intermediary records expense with amount, category, and description, **Then** expense is saved
2. **Given** expense is recorded, **When** intermediary uploads receipt photo, **Then** image is stored securely with expense
3. **Given** expense needs owner approval, **When** owner reviews expense, **Then** owner can approve or reject with notes
4. **Given** multiple expenses exist, **When** intermediary generates monthly report, **Then** expenses appear grouped by category with totals
5. **Given** year ends, **When** owner exports annual expense report, **Then** all expenses are included for tax purposes

---

### User Story 7 - System Syncs Data Across Offline Mobile Devices (Priority: P2)

An intermediary records payments while offline (no internet), and when connection is restored, the system automatically syncs changes to server without data loss.

**Why this priority**: Critical for mobile reliability in areas with poor connectivity, but optional if internet is always available.

**Independent Test**: Can be fully tested by making changes offline → going online → verifying sync → checking for conflicts, delivering reliable offline operation.

**Acceptance Scenarios**:

1. **Given** device loses internet, **When** intermediary records payment offline, **Then** payment is saved locally with sync pending status
2. **Given** connection is restored, **When** automatic sync triggers, **Then** local changes upload to server
3. **Given** multiple devices edit same tenant profile data, **When** sync occurs, **Then** last-write-wins with timestamp resolves conflict for non-financial data
4. **Given** multiple devices record conflicting financial transactions offline, **When** sync occurs, **Then** both transactions are preserved and intermediary receives conflict alert requiring manual resolution
5. **Given** sync fails, **When** retry mechanism activates, **Then** system retries with exponential backoff
6. **Given** large dataset, **When** sync completes, **Then** sync log shows records synced and status

---

### User Story 8 - Intermediary Sends Bulk Payment Reminders (Priority: P3)

An intermediary selects multiple tenants with overdue rent and sends personalized SMS/WhatsApp reminders with one click.

**Why this priority**: Useful for communication efficiency but individual messages work initially. Requires SMS gateway integration.

**Independent Test**: Can be fully tested by selecting tenants → choosing template → sending messages → tracking delivery, delivering automated reminders.

**Acceptance Scenarios**:

1. **Given** overdue tenants exist, **When** intermediary selects multiple tenants, **Then** bulk messaging option appears
2. **Given** tenants are selected, **When** intermediary chooses message template, **Then** template variables (name, amount) are populated
3. **Given** message is configured, **When** intermediary sends bulk message, **Then** messages are queued for delivery
4. **Given** messages are sent, **When** delivery status updates, **Then** intermediary sees delivered/failed count
5. **Given** scheduled messages exist, **When** scheduled time arrives, **Then** messages send automatically

---

### User Story 9 - Tenant Uploads and Stores Lease Agreement (Priority: P3)

A tenant uploads their signed lease agreement PDF, and the system stores it securely with expiration reminder set for renewal date.

**Why this priority**: Nice-to-have for document organization but physical/email documents work initially. Requires cloud storage.

**Independent Test**: Can be fully tested by uploading document → setting expiration → accessing securely → receiving reminder, delivering document management.

**Acceptance Scenarios**:

1. **Given** lease is signed, **When** tenant uploads PDF document, **Then** document is stored in cloud with encrypted access
2. **Given** document is uploaded, **When** tenant sets expiration date, **Then** system schedules reminder notification
3. **Given** expiration approaches, **When** reminder date arrives, **Then** tenant and intermediary receive expiration alert
4. **Given** document needs update, **When** new version is uploaded, **Then** old version is archived with version history
5. **Given** tenant leaves, **When** access is revoked, **Then** tenant can no longer view documents

---

### User Story 10 - Owner Configures Automatic Rent Increment (Priority: P3)

A property owner sets rent increment policy (5% every 2 years) and the system automatically calculates and applies increases on tenant anniversaries.

**Why this priority**: Convenience feature that prevents manual tracking but owners can manually adjust rent initially.

**Independent Test**: Can be fully tested by setting policy → waiting for anniversary → seeing auto-increment → notifying tenant, delivering automated rent increases.

**Acceptance Scenarios**:

1. **Given** tenant moves in, **When** owner sets 5% increment every 2 years, **Then** policy is attached to tenant
2. **Given** 2 years pass, **When** tenant anniversary arrives, **Then** system calculates new rent amount
3. **Given** new rent is calculated, **When** increment activates, **Then** tenant receives notification 30 days before
4. **Given** special case exists, **When** owner manually overrides increment, **Then** manual adjustment is applied
5. **Given** increment history exists, **When** owner views tenant, **Then** historical rent rates are displayed

---

### User Story 11 - Tenant Exports Personal Payment History (Priority: P3)

A tenant needs payment records for personal accounting and exports their complete payment history to Excel with one click.

**Why this priority**: Helpful for tenant record-keeping but screenshots or manual lists work initially.

**Independent Test**: Can be fully tested by selecting date range → clicking export → downloading Excel file, delivering instant record access.

**Acceptance Scenarios**:

1. **Given** payment history exists, **When** tenant clicks export, **Then** Excel file is generated with all payments
2. **Given** export is requested, **When** file is generated, **Then** file includes dates, amounts, methods, and receipt numbers
3. **Given** long history exists, **When** tenant selects date range, **Then** only filtered records are exported
4. **Given** PDF is preferred, **When** tenant selects PDF format, **Then** formatted PDF report is generated
5. **Given** export completes, **When** tenant downloads, **Then** file name includes date range for easy identification

---

### User Story 12 - User Switches App Language (Priority: P3)

A Hindi-speaking tenant changes app language to Hindi in settings, and all UI text displays in Hindi with proper number/currency formatting.

**Why this priority**: Important for non-English markets but English interface works for MVP launch.

**Independent Test**: Can be fully tested by changing language → viewing screens → verifying translations → checking RTL for Arabic, delivering localized experience.

**Acceptance Scenarios**:

1. **Given** user opens settings, **When** user selects Hindi language, **Then** all UI text changes to Hindi immediately
2. **Given** language is changed, **When** user views amounts, **Then** currency symbols and number formats update to locale
3. **Given** Arabic is selected, **When** user views screens, **Then** layout switches to right-to-left (RTL)
4. **Given** message templates exist, **When** language changes, **Then** templates use language-specific versions
5. **Given** translation missing, **When** text renders, **Then** English fallback appears

---

### User Story 13 - Owner Generates Annual Tax Report (Priority: P3)

A property owner generates annual tax statement with total rent income, deductible expenses, and tax form for filing with accountant.

**Why this priority**: Valuable for tax compliance but manual spreadsheet calculation works for first year.

**Independent Test**: Can be fully tested by selecting financial year → generating report → exporting with tax calculations, delivering tax-ready reports.

**Acceptance Scenarios**:

1. **Given** financial year ends, **When** owner requests tax report, **Then** system calculates total rent income
2. **Given** expenses exist, **When** report is generated, **Then** deductible expenses are itemized by category
3. **Given** tax rate is configured, **When** report calculates, **Then** taxable income and tax amount are shown
4. **Given** form generation is requested, **When** owner selects form type, **Then** pre-filled tax form PDF is created
5. **Given** report is complete, **When** owner shares with accountant, **Then** secure share link is generated

---

### User Story 14 - Intermediary Receives Push Notification for Payment (Priority: P3)

When a tenant completes online payment, the intermediary immediately receives push notification on mobile with payment details.

**Why this priority**: Nice real-time awareness feature but email notifications or manual checking works initially.

**Independent Test**: Can be fully tested by completing payment → seeing notification → tapping to view details, delivering instant alerts.

**Acceptance Scenarios**:

1. **Given** tenant pays online, **When** payment confirms, **Then** intermediary receives push notification instantly
2. **Given** notification is received, **When** intermediary taps notification, **Then** app opens to payment details
3. **Given** notification preferences exist, **When** user sets quiet hours, **Then** notifications pause during sleep time
4. **Given** multiple events occur, **When** notifications pile up, **Then** notifications are grouped by type
5. **Given** app is closed, **When** notification arrives, **Then** badge count increments on app icon

---

### Edge Cases

- What happens when a tenant leaves mid-month? System allows pro-rated rent calculation based on days occupied for final month and early exit date marking. Formula: (days stayed / total days in month) × monthly rent.
- What happens when a tenant moves in mid-month? System automatically calculates pro-rated rent for first month only: (days from move-in to month end / total days in month) × monthly rent. Subsequent months charge full rent.
- How does the system handle partial payments across multiple transactions? Each partial payment is recorded separately and balance updates incrementally.
- What if electricity bill amount changes after allocation to tenants? Intermediary can edit bill, and system recalculates allocations with change notification to affected tenants.
- How are currency rounding errors in bill division handled? System uses banker's rounding and assigns any remainder cents to first tenant deterministically.
- What happens when tenant is deleted but payment history exists? Tenant is soft-deleted (marked inactive) and historical data remains viewable but tenant cannot log in.
- How does conflict resolution work when same tenant data is edited on two devices offline? Non-financial data (profile updates) uses last-write-wins based on timestamp comparison; financial transactions (payments, bills, expenses) use append-only approach where both conflicting records are preserved and intermediary must manually resolve through conflict resolution UI showing both versions with timestamps and device information.
- What if payment gateway webhook fails to deliver? System polls payment status periodically as backup, and manual reconciliation tool is available.
- How are recurring bills handled when tenant count changes? System recalculates division percentages automatically or prompts for manual adjustment.
- What happens when document storage quota is exceeded? System notifies owner, prevents new uploads, and provides cleanup recommendations.
- How does the system handle multiple properties for one owner? Owner can switch property context in UI to manage each property separately, and owner can assign multiple properties to trusted intermediaries for distributed management.
- What happens when an intermediary is removed from a property? System revokes intermediary's access to that property's data while preserving access to other assigned properties; tenants remain active and historical data is preserved.

## Requirements *(mandatory)*

### Functional Requirements

**User Management & Authentication:**

- **FR-001**: System MUST support three distinct user roles: Owner, Intermediary, and Tenant with different permission levels
- **FR-002**: Owners and Intermediaries MUST be able to create Tenant user accounts
- **FR-003**: System MUST generate unique login credentials for each new tenant
- **FR-004**: Users MUST be able to authenticate with email/mobile and password
- **FR-005**: System MUST enforce role-based access control where Owners see all data, Intermediaries see their managed tenants, and Tenants see only their own data
- **FR-005a**: Owners MUST be able to assign one or multiple properties to an intermediary, and intermediaries can only access data for properties explicitly assigned to them by the owner

**Tenant Profile Management:**

- **FR-006**: System MUST store tenant basic information including name, mobile number, and move-in start date
- **FR-007**: System MUST calculate and display time stayed in property based on start date
- **FR-008**: Tenant profiles MUST display financial summary with total paid, remaining balance, and payment history
- **FR-009**: System MUST track electricity consumption per tenant with configurable per-unit pricing
- **FR-010**: System MUST support water bill division among multiple tenants
- **FR-011**: Tenant list MUST display as grid or card view with search and filter capabilities

**Payment Tracking:**

- **FR-012**: Intermediaries MUST be able to record rent payments with amount, date, payment method, and notes
- **FR-013**: System MUST track money sent from intermediary to owner and calculate remaining balance
- **FR-014**: System MUST maintain complete payment history with timestamps
- **FR-015**: System MUST highlight overdue payments with visual indicators
- **FR-016**: System MUST generate printable payment receipts with all transaction details
- **FR-017**: System MUST support multiple payment methods including cash, bank transfer, and digital payments
- **FR-017a**: System MUST calculate pro-rated rent for first month when tenant moves in mid-month, based on actual days occupied (days stayed / total days in month × monthly rent), then charge full monthly rent for subsequent months

**Bill Management:**

- **FR-018**: System MUST allow adding monthly bills for electricity, water, maintenance, and custom categories
- **FR-019**: System MUST support both percentage-based and fixed amount division methods for bills
- **FR-020**: System MUST handle recurring bills with automatic monthly generation
- **FR-021**: System MUST track which tenants have paid their bill share
- **FR-022**: System MUST calculate and display remaining amounts per tenant for each bill
- **FR-023**: System MUST allow custom division rules for different bill types

**Expense Tracking:**

- **FR-024**: System MUST record maintenance and emergency expense with amount, description, date, and category
- **FR-025**: System MUST support receipt/photo upload for expense documentation
- **FR-026**: System MUST track which party paid the expense (Owner/Intermediary/Tenant)
- **FR-027**: System MUST generate monthly and yearly expense reports
- **FR-028**: System MUST support expense approval workflow with approval status tracking

**Rent Increment Management:**

- **FR-029**: System MUST allow configuration of percentage-based or fixed amount rent increments
- **FR-030**: System MUST support increment schedule based on tenant anniversary years
- **FR-031**: System MUST automatically calculate new rent on scheduled date
- **FR-032**: System MUST provide manual override capability for special cases
- **FR-033**: System MUST send notifications to tenants before increment takes effect (configurable advance notice period, default 30 days)
- **FR-034**: System MUST maintain historical rent rate tracking per tenant

**Data Synchronization:**

- **FR-035**: System MUST support three sync modes: no sync, periodic automatic sync, and manual sync
- **FR-036**: Mobile app MUST store data locally for offline operation
- **FR-037**: System MUST sync mobile data with central server when connection is available
- **FR-038**: System MUST resolve edit conflicts using last-write-wins with timestamp comparison for non-financial data; financial transactions (payments, bills, expenses) MUST use append-only conflict resolution where both conflicting records are preserved and flagged for manual resolution by intermediary through dedicated conflict resolution UI
- **FR-039**: System MUST display sync status indicators (synced, pending, failed)
- **FR-040**: System MUST implement retry mechanism with exponential backoff for failed syncs
- **FR-041**: System MUST validate data before sync to prevent corruption
- **FR-041a**: System MUST provide conflict resolution UI for intermediaries to review and resolve conflicting financial transactions, showing both versions with timestamps and device information

**Export Functionality:**

- **FR-042**: Intermediaries MUST be able to export all tenant data to Excel format
- **FR-043**: Export MUST include tenant details, payment status, bills, and outstanding amounts
- **FR-044**: Tenants MUST be able to export their individual payment history
- **FR-045**: System MUST support customizable export templates
- **FR-046**: Export MUST support date range filters
- **FR-047**: System MUST generate summary sheets with totals and statistics
- **FR-048**: System MUST support PDF export as alternative format

**Messaging System:**

- **FR-049**: System MUST send SMS/WhatsApp messages to tenants through gateway integration
- **FR-050**: System MUST support message templates for rent reminders and bill notifications
- **FR-051**: System MUST support immediate, scheduled, and recurring message delivery
- **FR-052**: System MUST allow manual message composition for custom communications
- **FR-053**: System MUST support bulk messaging to multiple selected tenants
- **FR-054**: System MUST track message delivery status for each recipient
- **FR-055**: System MUST maintain message history per tenant
- **FR-056**: System MUST support personalized message variables (tenant name, amount due, etc.)

**Settings & Configuration:**

- **FR-057**: System MUST allow electricity rate configuration per unit
- **FR-058**: System MUST allow water bill calculation settings configuration
- **FR-059**: System MUST support default bill division method configuration
- **FR-060**: Users MUST be able to configure sync preferences (mode, frequency, auto-retry)
- **FR-061**: Users MUST be able to configure notification preferences
- **FR-061a**: Owners and Intermediaries MUST be able to configure payment reminder schedule (number of reminders, days before due date) with system default of 7 days before, 3 days before, and on due date
- **FR-062**: System MUST support currency and date format settings
- **FR-062a**: Users MUST be able to select preferred display currency for dashboard and analytics (different from property's base transaction currency) with automatic exchange rate conversion for viewing purposes
- **FR-063**: System MUST provide backup and restore functionality
- **FR-064**: Users MUST be able to manage their profile information
- **FR-065**: System MUST support theme selection (light/dark mode)

**Document Storage:**

- **FR-066**: System MUST allow upload and storage of lease agreements in PDF and image formats
- **FR-067**: System MUST attach documents to specific tenant profiles
- **FR-068**: System MUST maintain document version history
- **FR-069**: System MUST enforce role-based document access control
- **FR-070**: System MUST send document expiration reminders based on set dates
- **FR-071**: System MUST support multiple document types (ID proof, agreements, NOCs, etc.)
- **FR-072**: System MUST allow document sharing with specific users
- **FR-073**: System MUST integrate with cloud storage for backup
- **FR-074**: System MUST support document categories and tagging
- **FR-075**: System MUST provide document search by tenant, date, or type

**Payment Gateway Integration:**

- **FR-076**: System MUST integrate with Nepal-based payment gateways (Khalti, eSewa, IME Pay)
- **FR-077**: Tenants MUST be able to pay rent through the app using various payment methods
- **FR-078**: System MUST support digital wallet payments (Khalti, eSewa), mobile banking (IME Pay), and card payments
- **FR-079**: System MUST automatically generate payment receipts after successful transactions
- **FR-080**: System MUST send payment confirmation notifications
- **FR-081**: System MUST support recurring payment setup for monthly rent
- **FR-082**: System MUST maintain transaction history with gateway transaction IDs
- **FR-083**: System MUST handle refunds and chargebacks
- **FR-084**: System MUST track payment gateway fees
- **FR-085**: System MUST comply with PCI-DSS standards for payment processing
- **FR-086**: Each property MUST operate in a single base currency (set at property creation and immutable for all transactions); system does NOT support multi-currency transactions within a single property
- **FR-087**: System MUST generate shareable payment links

**Analytics Dashboard:**

- **FR-088**: System MUST provide interactive dashboard for Owners and Intermediaries
- **FR-089**: Dashboard MUST display rent collection trends with line/bar charts
- **FR-090**: Dashboard MUST show payment status overview (paid/pending/overdue)
- **FR-091**: Dashboard MUST display occupancy rates and vacancy analytics
- **FR-092**: Dashboard MUST show bill payment patterns and averages
- **FR-093**: Dashboard MUST display expense breakdown by category using pie charts
- **FR-094**: Dashboard MUST compare revenue vs. expenses
- **FR-095**: Dashboard MUST analyze tenant payment behavior
- **FR-096**: Dashboard MUST support year-over-year comparison charts
- **FR-097**: Dashboard MUST show property-wise performance metrics (for multi-property owners)
- **FR-098**: Dashboard MUST support customizable date ranges
- **FR-099**: System MUST allow exporting analytics data to PDF/Excel
- **FR-100**: Dashboard MUST update with real-time or near real-time data
- **FR-101**: Dashboard MUST support drill-down capability for detailed insights
- **FR-101a**: Dashboard and analytics charts MUST allow users to select display currency for viewing monetary data with real-time exchange rate conversion (for display only; actual transactions remain in property's base currency)

**Push Notifications:**

- **FR-102**: System MUST send real-time push notifications for important events
- **FR-103**: System MUST send rent payment reminders before due date with configurable schedule (default: 7 days before, 3 days before, and on due date; owner/intermediary can customize timing and frequency per property or tenant)
- **FR-104**: System MUST notify tenants of bill allocations
- **FR-105**: System MUST send payment confirmation alerts
- **FR-106**: System MUST send overdue payment warnings
- **FR-107**: System MUST notify users of new messages
- **FR-108**: System MUST send document upload/update alerts
- **FR-109**: System MUST send lease expiration reminders
- **FR-110**: System MUST notify about maintenance request updates
- **FR-111**: Users MUST be able to customize notification preferences per user
- **FR-112**: System MUST support quiet hours settings (no notifications during specified times)
- **FR-113**: System MUST maintain notification history and archive
- **FR-114**: System MUST provide in-app notification center
- **FR-115**: System MUST display badge counts for unread notifications

**Multi-Language Support:**

- **FR-116**: System MUST support multiple languages (minimum English, Hindi, Spanish)
- **FR-117**: Users MUST be able to select preferred language in settings
- **FR-118**: System MUST display all UI text in selected language
- **FR-119**: System MUST support RTL (Right-to-Left) layout for Arabic, Hebrew, etc.
- **FR-120**: System MUST format dates and numbers according to selected locale
- **FR-121**: System MUST display currency symbols based on region
- **FR-122**: System MUST provide language-specific message templates
- **FR-123**: System MUST fallback to English for untranslated content
- **FR-124**: System MUST support easy translation management and updates

**Tax & Reporting:**

- **FR-125**: System MUST generate comprehensive financial reports
- **FR-126**: System MUST generate annual rent income statements for tax filing
- **FR-127**: System MUST generate expense deduction reports
- **FR-128**: System MUST provide tenant-wise income breakdown
- **FR-129**: System MUST calculate and report GST/VAT based on region
- **FR-130**: System MUST generate tax forms (e.g., IRS Form 1099, local equivalents)
- **FR-131**: System MUST generate profit and loss statements
- **FR-132**: System MUST generate cash flow reports
- **FR-133**: System MUST support comparative reports (month-over-month, year-over-year)
- **FR-134**: System MUST support customizable report templates
- **FR-135**: System MUST support scheduled report generation and email delivery
- **FR-136**: System MUST allow report sharing with external parties (accountants, tax professionals)
- **FR-137**: System MUST generate audit trail reports for compliance
- **FR-138**: System MUST calculate property depreciation
- **FR-139**: System MUST track property valuation over time

### Key Entities

- **User**: Represents system users with role (Owner/Intermediary/Tenant), authentication credentials, contact information, and role-specific permissions
- **Property**: Represents rental property with address, owner, total units, base currency (immutable after creation), and associated metadata
- **Property Assignment**: Represents many-to-many relationship between intermediaries and properties, allowing owners to assign multiple properties to an intermediary and an intermediary to manage multiple properties
- **Tenant**: Represents person renting property with profile information, start date, current rent, associated user account, and assigned intermediary
- **Payment**: Represents financial transaction with amount, date, payment method, payer (tenant), receiver (intermediary/owner), transaction type, and currency (inherited from property)
- **Bill**: Represents utility or service bill with total amount, bill type, billing period, property, and recurring flag
- **Bill Allocation**: Represents individual tenant's share of a bill with tenant reference, allocation percentage/amount, paid amount, and payment status
- **Expense**: Represents property expense with amount, category, description, date, paid-by party, and attached receipts
- **Message**: Represents communication sent to tenant with content, delivery schedule, delivery status, and message type
- **Document**: Represents stored file with file location, document type, associated tenant/property, version, expiration date, and access permissions
- **Transaction**: Represents payment gateway transaction with gateway reference ID, amount, currency, status, payment method, and gateway response
- **Notification**: Represents push notification with title, body, recipient, notification type, read status, and related entity reference
- **Report Template**: Represents saved report configuration with template name, report type, configuration parameters, and schedule
- **Sync Log**: Represents data synchronization event with timestamp, user, sync status, records synced, and error details

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Property owners can onboard their first property and tenant within 10 minutes of account creation
- **SC-002**: Intermediaries can record a rent payment and generate receipt in under 1 minute
- **SC-003**: System can divide a monthly utility bill among 10 tenants in under 5 seconds
- **SC-004**: Mobile app operates fully offline for at least 7 days with automatic sync upon connection restore
- **SC-005**: 95% of online payments complete successfully within 30 seconds
- **SC-006**: Tenants can access and view their payment history within 2 seconds of opening the app
- **SC-007**: Analytics dashboard loads with charts for 12 months of data in under 3 seconds
- **SC-008**: Bulk messages to 100 tenants are queued and sent within 5 minutes
- **SC-009**: Document uploads complete within 10 seconds for files up to 5MB
- **SC-010**: Export of tenant data to Excel completes within 10 seconds for up to 100 tenants
- **SC-011**: System supports 1000 concurrent users without performance degradation
- **SC-012**: Push notifications are delivered within 5 seconds of triggering event
- **SC-013**: 90% of users successfully complete their primary task on first attempt
- **SC-014**: System reduces time spent on rent collection administrative tasks by 60%
- **SC-015**: Reduce payment collection delays by 40% through automated reminders
- **SC-016**: 85% of tenants report satisfaction with payment tracking transparency
- **SC-017**: System maintains 99.9% uptime during business hours
- **SC-018**: Data sync conflicts occur in less than 0.1% of sync operations
- **SC-019**: Annual tax report generation reduces accountant preparation time by 50%
- **SC-020**: System handles properties with up to 50 tenants without performance issues

## Assumptions

- Users have smartphones or computers with internet access (at least intermittently for sync)
- Property owners/intermediaries are responsible for legal compliance in their jurisdiction
- Payment gateway accounts will be set up by system administrator or property owner
- SMS/WhatsApp gateway services are available and configured
- Cloud storage service is available for document storage
- Users will use standard date formats according to their locale
- Rent payment due dates follow monthly cycles (customizable per tenant)
- Financial data will be retained indefinitely for audit purposes
- Maximum of 50 tenants per property (system can scale but initial target)
- Electricity rates and bill division methods are configured per property by intermediary
- Default language is English with additional languages added progressively
- Mobile devices run iOS 13+ or Android 8.0+
- Backend server infrastructure provides adequate storage and compute resources
- Payment gateway fees are transparently shown and tracked separately from rent amounts
- Document storage is limited to 1GB per property initially (expandable)
- System operates in single currency per property (multi-currency support is per-property setting, not per-transaction); property base currency is set at creation and cannot be changed
- Dashboard currency display conversion uses real-time exchange rates from external API for viewing purposes only; all actual transactions and storage remain in property's base currency
- Notification delivery depends on device connectivity and notification permission settings
- Tax calculation rules are configurable per region and may require periodic updates
- Intermediaries have authority to manage tenants and collect payments on behalf of owners

