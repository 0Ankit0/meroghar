# Use Case Descriptions

## Overview
Detailed descriptions of primary use cases in MeroGhar, specific to house, flat, and apartment rentals.

---

## UC-001: Browse and Apply for a Rental Property

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-001 |
| **Name** | Browse and Apply for a Rental Property |
| **Actor** | Tenant |
| **Description** | A tenant searches available listings, selects a property, and submits a rental application |
| **Preconditions** | Tenant is registered and logged in; at least one property is published and available |
| **Postconditions** | Rental application created with status PENDING (or CONFIRMED for instant approval); availability hold placed |

**Main Flow:**
1. Tenant selects a property type (Apartment, House, Room, Studio, Villa, Commercial Space) and enters the desired rental period (start and end date)
2. System displays available listings with pricing preview for the selected period
3. Tenant applies optional filters (price range, location, bedrooms, bathrooms, furnishing status, parking, balcony)
4. Tenant clicks on a listing to view full property details, photos, floor plan, and availability calendar
5. Tenant selects the rental period and reviews the pricing breakdown
6. Tenant clicks "Apply Now" and confirms personal details
7. System validates availability and calculates the total price including security deposit
8. Tenant completes the security deposit payment
9. System creates the rental application record
10. If instant approval: application status is set to CONFIRMED immediately; both parties notified
11. If manual confirmation: application status is PENDING; landlord is notified for review

**Alternative Flows:**
- *A1 – Property unavailable for selected dates*: System shows the next available window
- *A2 – Deposit payment fails*: Rental application is not created; tenant is prompted to retry

---

## UC-002: Confirm Rental Application and Generate Lease Agreement

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-002 |
| **Name** | Confirm Rental Application and Generate Lease Agreement |
| **Actor** | Landlord (confirms), Tenant (signs) |
| **Description** | Landlord approves a rental application and generates a lease agreement for digital signing |
| **Preconditions** | Rental application is in PENDING status (manual confirmation mode) |
| **Postconditions** | Application CONFIRMED; lease agreement signed by both parties; property calendar blocked |

**Main Flow:**
1. Landlord receives a notification of a pending rental application
2. Landlord reviews the tenant's profile and uploaded documents
3. Landlord clicks "Confirm Application"
4. System updates application status to CONFIRMED and blocks the property calendar
5. Landlord navigates to the application and selects "Generate Lease Agreement"
6. Landlord selects an agreement template and reviews the pre-filled tenancy terms
7. Landlord sends the lease agreement to the tenant for signature
8. System dispatches a signature request via the e-signature provider
9. Tenant opens the agreement, reviews all tenancy terms, and signs digitally
10. E-signature provider sends a webhook confirming the tenant's signature
11. System notifies the landlord to countersign
12. Landlord countersigns the lease agreement
13. System retrieves the final signed PDF and stores it against the tenancy
14. Both parties receive the signed lease agreement via email

**Alternative Flows:**
- *A1 – Landlord declines application*: Status set to DECLINED; deposit refunded; tenant notified
- *A2 – Tenant requests amendment*: Tenant adds a comment; landlord revises and resends

---

## UC-003: Move-In Property Inspection

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-003 |
| **Name** | Move-In Property Inspection |
| **Actor** | Property Manager (conducts), Tenant (countersigns) |
| **Description** | Property manager records the property's condition with a detailed checklist and photos before handover to the tenant |
| **Preconditions** | Rental application is CONFIRMED; tenancy period has not yet started |
| **Postconditions** | Move-in inspection completed, signed by tenant; key handover recorded |

**Main Flow:**
1. Property manager opens the assigned inspection task for the tenancy
2. System presents a condition checklist tailored to the property (e.g., bedrooms: walls, flooring, windows, fixtures; kitchen: appliances, countertops, plumbing; bathrooms: sanitaryware, tiling, water pressure; common areas: doors, locks, lighting)
3. Property manager works through each checklist item and marks condition (Good / Fair / Damaged)
4. Property manager captures photos for each item showing current condition
5. Property manager submits the completed inspection report
6. System generates the inspection report and sends it to the tenant
7. Tenant reviews the report and photos
8. Tenant countersigns the report to acknowledge the property's condition at move-in
9. System records the countersignature and marks the key handover complete
10. Tenancy period officially begins

**Alternative Flows:**
- *A1 – Tenant disagrees with a finding*: Tenant adds a dispute note before signing; flagged for landlord review

---

## UC-004: Move-Out and Post-Tenancy Inspection

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-004 |
| **Name** | Move-Out and Post-Tenancy Inspection |
| **Actor** | Tenant (initiates move-out), Property Manager (conducts inspection), Landlord (approves charges) |
| **Description** | Tenant vacates the property; property manager conducts a move-out inspection; any damage or late-vacation fees are calculated |
| **Preconditions** | Tenancy is in ACTIVE status; rental period has started |
| **Postconditions** | Move-out inspection recorded; additional charges raised if applicable; deposit refund initiated |

**Main Flow:**
1. Tenant initiates a move-out via the app, logging the actual vacation date and time
2. System notifies property manager to prepare for move-out inspection
3. Property manager completes the move-out condition checklist and captures photos
4. System displays a side-by-side comparison of move-in and move-out conditions
5. If no discrepancies and move-out is on time:
   - System marks the tenancy as RETURNED
   - System initiates the full security deposit refund
   - System generates the final invoice
6. If damage discrepancies found:
   - Landlord is notified with the comparison report
   - Landlord itemises damage charges with evidence
   - Tenant is notified of proposed charges
7. If move-out is late:
   - System auto-calculates overdue fees based on the property's daily rate
   - Overdue fee added to final invoice
8. Tenant pays the final invoice (including any additional charges)
9. System releases the property back to available status on the calendar
10. Tenancy is marked CLOSED

**Alternative Flows:**
- *A1 – Tenant disputes damage charge*: Dispute submitted; admin can mediate

---

## UC-005: Flexible Pricing Calculation

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-005 |
| **Name** | Flexible Pricing Calculation |
| **Actor** | System (automated), Tenant (views breakdown) |
| **Description** | System calculates the rental fee for any property across daily, weekly, and monthly rate tiers including peak pricing; monthly rent is the standard for long-term tenancies |
| **Preconditions** | Property has at least one pricing rule configured |
| **Postconditions** | Total rental fee displayed and stored on the rental application |

**Main Flow:**
1. Tenant selects a rental period (e.g., 6 months)
2. System identifies all applicable pricing rules for the property and period
3. System applies peak pricing windows if the period overlaps peak dates (e.g., high season, festivals)
4. System selects the most cost-effective rate tier combination (e.g., monthly rate is cheaper than 30 daily rates)
5. System calculates taxes based on the property type and jurisdiction
6. System displays the full pricing breakdown to the tenant:
   - Base rental fee (with tier and rate shown — monthly, weekly, or daily)
   - Peak pricing surcharge (if applicable)
   - Tax
   - Security deposit (held separately)
   - Total due now

---

## UC-006: Maintenance Request Lifecycle

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-006 |
| **Name** | Maintenance Request Lifecycle |
| **Actor** | Tenant (logs), Landlord (assigns/approves), Property Manager (executes) |
| **Description** | Full lifecycle of a property maintenance request from logging to resolution |
| **Preconditions** | Landlord is authenticated; property exists |
| **Postconditions** | Maintenance completed and approved; property returned to available; costs logged |

**Main Flow:**
1. Landlord logs a maintenance request with a description, priority, and photos (e.g., plumbing leak, electrical fault, broken fixtures)
2. System creates the request (OPEN) and blocks the property's availability calendar
3. Landlord assigns the request to a property manager
4. Property manager receives a notification and accepts the assignment (status: ASSIGNED)
5. Property manager begins work; updates status to IN_PROGRESS
6. Property manager adds work notes, photos of completed work, and logs materials used
7. Property manager marks the task as COMPLETED
8. Landlord reviews the completion evidence
9. Landlord approves; status changes to CLOSED
10. Landlord logs the total maintenance cost
11. System unblocks the property's availability calendar

**Alternative Flows:**
- *A1 – Property manager declines*: Landlord is notified; reassigns to another property manager
- *A2 – Landlord reopens*: Status reverts to IN_PROGRESS with reopen reason

---

## UC-007: Security Deposit Settlement

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-007 |
| **Name** | Security Deposit Settlement |
| **Actor** | Landlord (settles), Tenant (receives) |
| **Description** | Landlord reviews move-out inspection and settles the deposit — full refund or partial deduction |
| **Preconditions** | Move-out inspection completed; tenancy is in PENDING_CLOSURE status |
| **Postconditions** | Deposit refunded or deducted; tenancy CLOSED |

**Main Flow:**
1. Landlord navigates to the completed tenancy
2. Landlord reviews the move-out inspection report
3. If no damage: Landlord confirms full deposit release
4. If damage found: Landlord itemises deductions with description, amount, and evidence photos for each item (e.g., broken tiles, damaged appliances, stained carpets)
5. System calculates the net refund amount (deposit minus deductions)
6. Landlord submits the settlement
7. Tenant is notified of the settlement details
8. Tenant may accept or dispute within the configured window
9. On acceptance (or after the dispute window): System processes the refund to the tenant's original payment method
10. System records the settlement and generates a deposit statement

---

## UC-008: Monthly Rent Collection and Reminder Cycle

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-008 |
| **Name** | Monthly Rent Collection and Reminder Cycle |
| **Actor** | System (automated), Tenant (pays), Landlord/Property Manager (monitors) |
| **Description** | Automated monthly rent cycle with reminders, payment tracking, and overdue escalation |
| **Preconditions** | Tenancy is ACTIVE with monthly billing enabled |
| **Postconditions** | Monthly invoice is PAID or marked OVERDUE with escalation timeline |

**Main Flow:**
1. System creates monthly rent invoice on configured billing date
2. System sends reminder notifications to tenant based on configured cadence (e.g., 7, 3, and 1 day before due date)
3. Tenant reviews invoice details and initiates payment
4. Payment gateway confirms transaction via webhook
5. System marks invoice as PAID and generates receipt
6. System notifies tenant and landlord/property manager of successful payment
7. Ledger and dashboard metrics update immediately

**Alternative Flows:**
- *A1 – Partial payment received*: System marks invoice PARTIALLY_PAID and keeps remaining balance active
- *A2 – Due date missed*: System marks invoice OVERDUE, applies late-fee policy, and notifies tenant + owner/manager
- *A3 – Payment failure*: System records failure reason and prompts tenant to retry with another method

---

## UC-009: Utility Bill Upload, Split, and Collection

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-009 |
| **Name** | Utility Bill Upload, Split, and Collection |
| **Actor** | Landlord/Property Manager (uploads and allocates), Tenant (pays) |
| **Description** | Owner/manager uploads utility bill photos and assigns payable amounts to one or multiple tenants |
| **Preconditions** | Property has one or more active tenants and billing permissions are available |
| **Postconditions** | Tenant-level payable entries generated from bill split and tracked through payment completion |

**Main Flow:**
1. Owner/manager opens the property billing workspace and selects "Add Utility Bill"
2. Owner/manager uploads bill photo/document and enters bill details (period, due date, total amount, notes)
3. System stores attachment and validates required metadata
4. Owner/manager chooses split mode:
   - Single tenant assignment (100% to one tenant), or
   - Multi-tenant split (equal, percentage-based, or custom fixed amount)
5. System validates that assigned totals match the expected payable amount
6. System generates tenant-level bill-share items and links the bill image
7. Tenants receive notifications with payable amount, due date, and bill evidence
8. Tenant opens payable item, reviews split basis + bill image, and completes payment
9. System updates bill status (UNPAID → PARTIALLY_PAID/PAID) and notifies owner/manager

**Alternative Flows:**
- *A1 – Split mismatch*: System blocks save and requests correction before publishing
- *A2 – Tenant raises dispute*: System opens bill dispute thread and pauses escalation until resolution
- *A3 – Owner subsidy*: Owner/manager marks a portion as owner-paid and invoices only tenant-share amount

---

## UC-010: Preventive Operations and Property Upkeep Workflow

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-010 |
| **Name** | Preventive Operations and Property Upkeep Workflow |
| **Actor** | Landlord/Property Manager (plans), Staff/Contractor (executes) |
| **Description** | Recurring operational workflows required to run rental properties, including inspections, meter readings, and compliance checks |
| **Preconditions** | Property is active and operations templates are configured |
| **Postconditions** | Task completed with evidence and audit trail available for reporting |

**Main Flow:**
1. Owner/manager configures recurring workflow template (task type, checklist, frequency, SLA, assignee)
2. System auto-creates tasks for due cycle
3. Assignee receives reminder notifications before due date
4. Assignee performs task and submits checklist results with notes/photos
5. Owner/manager reviews completion and closes task
6. System logs completion history and updates property operations dashboard

**Alternative Flows:**
- *A1 – SLA missed*: System escalates overdue task to owner/manager
- *A2 – Failed check item*: System creates follow-up maintenance request and links evidence
