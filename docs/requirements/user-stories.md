# User Stories

> **Superseded for MVP planning:** Story prioritization, v1 scope, measurable acceptance criteria, and implementation traceability are consolidated in `docs/requirements/mvp-backlog-matrix.md`.

## Landlord / Property Owner User Stories

### Account & Property Portfolio

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| LND-001 | As a landlord, I want to register my account so that I can manage my rental properties | - Email/phone validated<br>- OTP verified<br>- Profile created |
| LND-002 | As a landlord, I want to upload my identity and property ownership documents so that the platform can verify me | - Document upload form<br>- Verification status shown<br>- Rejection reason provided |
| LND-003 | As a landlord, I want to select a property type so that my listings are organised correctly | - Property type selected (Apartment, House, Room, Studio, Villa, Commercial Space)<br>- Property features/amenities fields defined<br>- Saved successfully |
| LND-004 | As a landlord, I want to add a new property so that tenants can apply to rent it | - Listing form with name, photos, amenities (bedrooms, bathrooms, floor area, furnishing status, parking, balcony)<br>- Pricing rules configured<br>- Property saved as draft |
| LND-005 | As a landlord, I want to set pricing rules (monthly rent, daily/weekly for short-term stays) so that tenants are billed correctly | - Rate tiers configured<br>- Min/max duration set<br>- Peak pricing windows defined |
| LND-006 | As a landlord, I want to manage the property's availability calendar so that applications reflect real availability | - Availability window set<br>- Blocked dates visible<br>- Rented dates locked automatically |
| LND-007 | As a landlord, I want to publish a property listing so that tenants can discover and apply for it | - Toggle publish/unpublish<br>- Listing visible in search<br>- Draft mode available |

### Rental Application Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| LND-008 | As a landlord, I want to review and approve rental applications so that I control who rents my properties | - Pending application list shown<br>- Tenant profile and documents visible<br>- Approve/decline with reason |
| LND-009 | As a landlord, I want to enable instant booking so that tenants can confirm without waiting for manual approval | - Instant booking toggle per property<br>- Auto-confirmed on availability check<br>- Landlord notified |
| LND-010 | As a landlord, I want to view all active and upcoming tenancies so that I can plan operations | - Tenancy list with status<br>- Calendar view available<br>- Filterable by property and status |
| LND-011 | As a landlord, I want to cancel a tenancy with a reason so that the tenant is informed promptly | - Cancellation reason recorded<br>- Refund policy applied<br>- Tenant notified |

### Lease Agreements & Deposits

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| LND-012 | As a landlord, I want to generate a lease agreement for a confirmed tenancy so that terms are formalised | - Template selected<br>- Agreement pre-filled with tenancy details<br>- Sent to tenant for signing |
| LND-013 | As a landlord, I want to countersign the lease agreement so that it becomes legally binding | - Tenant signature confirmed<br>- Countersign action available<br>- Signed PDF stored and emailed |
| LND-014 | As a landlord, I want to configure the security deposit for each property so that damages are covered | - Deposit amount set per property<br>- Collected on lease confirmation<br>- Refund window configurable |
| LND-015 | As a landlord, I want to release or partially deduct the security deposit after move-out so that fair settlement is processed | - Deposit itemisation form<br>- Deduction reasons recorded with evidence<br>- Refund/deduction processed |

### Payments & Charges

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| LND-016 | As a landlord, I want rent invoices generated automatically on lease confirmation and each due date so that billing is consistent | - Invoice with period and amount<br>- Tenant notified<br>- Tax included |
| LND-017 | As a landlord, I want to add additional charges after move-out so that damage or outstanding fees are collected | - Charge type selected (damage, cleaning, outstanding utility, etc.)<br>- Tenant notified<br>- Evidence attachment supported |
| LND-018 | As a landlord, I want to view my payout history so that I can track my rental income | - Payout list with dates and amounts<br>- Commission deduction visible<br>- Export to CSV |

### Property Inspections & Maintenance

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| LND-019 | As a landlord, I want staff to complete a move-in property inspection so that the property's condition is recorded before handover | - Checklist form per property type (walls, flooring, fixtures, appliances, etc.)<br>- Photos uploaded<br>- Tenant countersigns |
| LND-020 | As a landlord, I want staff to complete a move-out property inspection so that any damage is documented | - Move-out checklist filled<br>- Comparison with move-in inspection shown<br>- Damage charge prompted if discrepancy found |
| LND-021 | As a landlord, I want to log a maintenance request for a property so that repairs are tracked | - Request created with description<br>- Relevant staff assigned<br>- Status tracking enabled |
| LND-022 | As a landlord, I want to schedule preventive servicing for properties so that they remain in good condition | - Service task with recurrence set (plumbing, electrical, pest control)<br>- Reminder sent before due date<br>- Service history logged |

### Reporting

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| LND-023 | As a landlord, I want to view a financial dashboard so that I understand my portfolio performance | - Total rental income, expenses, and net income shown<br>- Property occupancy rate shown<br>- Month-over-month comparison |
| LND-024 | As a landlord, I want to generate an occupancy report so that I can identify underperforming properties | - Rented days vs. available days per property<br>- Exportable to CSV/PDF |
| LND-025 | As a landlord, I want to generate a tax summary report so that I can file taxes correctly | - Annual rental income totals<br>- Deductible expenses listed<br>- Export to PDF |

---

## Tenant User Stories

### Account Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TNT-001 | As a tenant, I want to register an account so that I can apply for rental properties | - Email/phone validated<br>- OTP verified<br>- Profile created |
| TNT-002 | As a tenant, I want to upload my ID so that landlords can verify my identity | - Document upload form<br>- Upload confirmation<br>- Visible to landlord on application |
| TNT-003 | As a tenant, I want to manage my profile so that my contact and payment info stays current | - Edit name/phone/email<br>- Saved payment methods manageable<br>- Save confirmed |

### Search & Rental Application

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TNT-004 | As a tenant, I want to search available properties so that I can find a suitable home | - Property type filter (Apartment, House, Room, Studio, Villa, Commercial Space)<br>- Date range picker<br>- Location filter<br>- Price range filter<br>- Amenity filters (bedrooms, bathrooms, furnishing status, parking) |
| TNT-005 | As a tenant, I want to view a property's listing so that I can assess it before applying | - Photos gallery<br>- Property features and amenities shown (bedrooms, bathrooms, floor area, furnishing, parking, balcony)<br>- Pricing breakdown shown<br>- Availability calendar shown |
| TNT-006 | As a tenant, I want to submit a rental application so that I can reserve the property | - Dates selected<br>- Pricing summary confirmed<br>- Application submitted |
| TNT-007 | As a tenant, I want to track my application status so that I know if it is confirmed | - Status visible (pending, confirmed, declined)<br>- Decline reason shown<br>- Confirmation notification sent |
| TNT-008 | As a tenant, I want to request changes to my tenancy dates so that I can adjust my move-in plan | - Modification request form<br>- Price difference shown<br>- Landlord approval required if manual mode |
| TNT-009 | As a tenant, I want to cancel my rental application so that I can change my plans | - Cancellation button available<br>- Refund amount calculated and shown<br>- Cancellation confirmed |

### Lease Agreements & Payments

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TNT-010 | As a tenant, I want to review and sign the lease agreement digitally so that I can proceed with the tenancy | - Lease agreement document readable<br>- E-sign action available<br>- Signed copy emailed to me |
| TNT-011 | As a tenant, I want to pay the rent invoice online so that my tenancy is confirmed | - Payment method selection<br>- Secure checkout<br>- Receipt emailed |
| TNT-012 | As a tenant, I want to view my payment history so that I have records of all transactions | - All past invoices listed<br>- Receipts downloadable<br>- Outstanding balances shown |
| TNT-013 | As a tenant, I want to dispute an additional charge so that unfair fees are reviewed | - Dispute reason submitted<br>- Landlord notified<br>- Resolution tracked |

### Property Inspections & Move-Out

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TNT-014 | As a tenant, I want to countersign the move-in inspection report so that I acknowledge the property's condition at handover | - Move-in checklist visible<br>- Photos viewable<br>- Countersign action available |
| TNT-015 | As a tenant, I want to initiate a move-out so that the landlord is notified I am vacating the property | - Move-out initiation form<br>- Actual vacating date recorded<br>- Landlord and property manager notified |
| TNT-016 | As a tenant, I want to view the move-out inspection report so that I know if any charges apply | - Report visible after move-out<br>- Comparison with move-in inspection shown<br>- Damage charges itemised |

### Reviews

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TNT-017 | As a tenant, I want to rate and review a property after a completed tenancy so that others can make informed decisions | - Star rating (1–5)<br>- Optional text review<br>- Submitted after tenancy closes |
| TNT-018 | As a tenant, I want to view reviews of a property so that I can trust the listing | - Reviews visible on listing page<br>- Average rating shown<br>- Sorted by most recent |

---

## Property Manager / Staff User Stories

### Daily Operations

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| STF-001 | As a property manager, I want to view my assigned tasks so that I know what inspections and maintenance to perform | - Task list with type (move-in inspection, move-out inspection, maintenance)<br>- Property and tenancy info shown<br>- Due time visible |
| STF-002 | As a property manager, I want to complete a move-in property inspection so that the property's condition is captured before tenant handover | - Property-type-specific checklist (walls, flooring, fixtures, appliances, etc.)<br>- Photo capture per item<br>- Submit inspection report |
| STF-003 | As a property manager, I want to complete a move-out property inspection so that any damage is documented | - Move-out checklist<br>- Photo capture<br>- Comparison summary with move-in inspection shown |
| STF-004 | As a property manager, I want to update a maintenance task status so that the landlord knows the progress | - Status update (in-progress, completed)<br>- Work notes and photos added<br>- Completion submitted for approval |
| STF-005 | As a property manager, I want to log parts and materials used in a maintenance job so that costs are tracked | - Item name and cost entered<br>- Linked to maintenance task<br>- Saved to record |

### Schedule & History

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| STF-006 | As a property manager, I want to view my work schedule so that I can plan my day | - Upcoming tasks in time order<br>- Property address shown<br>- Calendar view available |
| STF-007 | As a property manager, I want to view my completed task history so that I can reference past work | - Completed tasks listed<br>- Notes and photos accessible<br>- Filterable by property and date |

---

## Admin User Stories

### Dashboard & Oversight

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-001 | As an admin, I want to view platform metrics so that I can monitor system health | - Total landlords, tenants, active tenancies, and revenue shown<br>- Recent activity feed<br>- Alert indicators |
| ADM-002 | As an admin, I want to generate platform-wide reports so that usage trends are understood | - Custom date range<br>- Export to CSV<br>- Scheduled reports |
| ADM-003 | As an admin, I want to view audit logs so that all actions are traceable | - Filterable by user, action, date<br>- Immutable entries<br>- Export to CSV |

### User & Content Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-004 | As an admin, I want to verify landlord identity and property ownership documents so that the platform is trustworthy | - Document review interface<br>- Approve/reject with reason<br>- Landlord notified |
| ADM-005 | As an admin, I want to suspend or deactivate user accounts so that policy violations are enforced | - Suspension reason recorded<br>- User notified<br>- Audit log entry created |
| ADM-006 | As an admin, I want to manage property type templates so that landlords create consistent listings | - Property type editor<br>- Custom feature/amenity field management (bedrooms, bathrooms, floor area, furnishing status, parking, balcony)<br>- Publish/archive property types |
| ADM-007 | As an admin, I want to manage lease agreement templates so that landlords have standardised contracts | - Template editor<br>- Version control<br>- Publish/unpublish |

### Dispute Resolution

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-008 | As an admin, I want to view and mediate disputes between landlords and tenants so that conflicts are resolved fairly | - Dispute list with context<br>- Messaging thread visible<br>- Binding resolution recorded |
| ADM-009 | As an admin, I want to override a payment or charge status in exceptional cases so that records are corrected | - Override action with justification<br>- Audit log entry<br>- Both parties notified |

### Platform Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-010 | As an admin, I want to configure platform commission rates so that landlord payouts are correct | - Commission rate set (flat or percentage)<br>- Effective date configured<br>- Changes versioned |
| ADM-011 | As an admin, I want to configure notification templates so that communications are consistent | - Template editor per event type<br>- Preview function<br>- Save and publish |
| ADM-012 | As an admin, I want to manage admin roles and permissions so that access is controlled | - Role creation<br>- Permission matrix<br>- Assign to admin users |
