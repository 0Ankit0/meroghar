# Data Model Specification
# Meroghar Rental Management System

**Date**: 2025-10-26  
**Feature**: 001-rental-management  
**Database**: PostgreSQL 14+  
**ORM**: SQLAlchemy 2.0+

---

## Entity Relationship Diagram

```
┌──────────────┐
│    User      │
└──────┬───────┘
       │ 1
       │ owns
       │ *
┌──────▼────────────┐         ┌──────────────────────┐
│    Property       │◄────────┤ PropertyAssignment   │
└──────┬────────────┘    *    └──────────┬───────────┘
       │ 1                              * │
       │ has                              │ assigned_to
       │ *                              1 │
┌──────▼───────┐                   ┌─────▼──────┐
│   Tenant     │                   │ User       │
└──────┬───────┘                   │ (Intermed) │
       │ 1                         └────────────┘
       │ makes
       │ *
┌──────▼───────┐         ┌──────────────┐
│   Payment    │────────►│ Transaction  │
└──────────────┘    1:1  └──────────────┘
       │ 1
       │ for
       │ *
┌──────▼────────┐
│     Bill      │◄───────┐
└──────┬────────┘     *  │
       │ 1             generates
       │ allocated_to  │
       │ *            1│
┌──────▼──────────┐  ┌──▼───────────────┐
│ BillAllocation  │  │ RecurringBill    │
└─────────────────┘  └──────────────────┘

┌──────────────┐         ┌──────────────┐
│   Expense    │         │  Document    │
└──────────────┘         └──────────────┘

┌──────────────┐         ┌──────────────┐
│   Message    │         │ Notification │
└──────────────┘         └──────────────┘

┌──────────────┐         ┌──────────────┐
│  SyncLog     │         │ ReportTemplate│
└──────────────┘         └──────────────┘
```

---

## Core Entities

### 1. User

Represents all system users with role-based access.

**Table**: `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| phone | VARCHAR(20) | NULL | Contact phone number |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| full_name | VARCHAR(255) | NOT NULL | User's full name |
| role | ENUM('owner', 'intermediary', 'tenant') | NOT NULL | User role |
| is_active | BOOLEAN | DEFAULT TRUE | Account active status |
| created_at | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |
| last_login_at | TIMESTAMP | NULL | Last login timestamp |

**Indexes**:
- `idx_users_email` ON (email)
- `idx_users_role` ON (role)
- `idx_users_active` ON (is_active) WHERE is_active = TRUE

**Validation Rules**:
- Email must match regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Password must be at least 8 characters with bcrypt cost factor 12+
- Phone must match E.164 format if provided
- Role cannot be changed after creation (immutable)

**RLS Policy**:
```sql
-- Users can only view/edit their own profile
CREATE POLICY user_self_access ON users
  FOR ALL
  USING (id = current_setting('app.current_user_id')::uuid);

-- Owners and intermediaries can view their managed users
CREATE POLICY owner_intermediary_view_tenants ON users
  FOR SELECT
  USING (
    role = 'tenant' AND id IN (
      SELECT user_id FROM tenants WHERE property_id IN (
        SELECT property_id FROM property_assignments 
        WHERE intermediary_id = current_setting('app.current_user_id')::uuid
      )
    )
  );
```

---

### 2. Property

Represents a rental property owned by an owner.

**Table**: `properties`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique property identifier |
| owner_id | UUID | FK → users(id), NOT NULL | Property owner |
| name | VARCHAR(255) | NOT NULL | Property name/identifier |
| address_line1 | VARCHAR(255) | NOT NULL | Street address |
| address_line2 | VARCHAR(255) | NULL | Apartment/unit number |
| city | VARCHAR(100) | NOT NULL | City |
| state | VARCHAR(100) | NOT NULL | State/province |
| postal_code | VARCHAR(20) | NOT NULL | Postal/ZIP code |
| country | VARCHAR(100) | NOT NULL | Country |
| total_units | INTEGER | NOT NULL, CHECK > 0 | Number of rental units |
| base_currency | VARCHAR(3) | NOT NULL | ISO 4217 currency code (immutable) |
| created_at | TIMESTAMP | DEFAULT NOW() | Property creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_properties_owner` ON (owner_id)
- `idx_properties_city` ON (city, state)

**Validation Rules**:
- `base_currency` must be valid ISO 4217 code (USD, INR, EUR, etc.)
- `base_currency` is immutable after property creation
- `total_units` must be positive integer
- Address fields cannot be empty strings

**RLS Policy**:
```sql
-- Owners see all their properties
CREATE POLICY owner_property_access ON properties
  FOR ALL
  USING (owner_id = current_setting('app.current_user_id')::uuid);

-- Intermediaries see only assigned properties
CREATE POLICY intermediary_property_access ON properties
  FOR SELECT
  USING (
    id IN (
      SELECT property_id FROM property_assignments
      WHERE intermediary_id = current_setting('app.current_user_id')::uuid
    )
  );
```

---

### 3. PropertyAssignment

Junction table for many-to-many relationship between intermediaries and properties.

**Table**: `property_assignments`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Assignment identifier |
| property_id | UUID | FK → properties(id), NOT NULL | Assigned property |
| intermediary_id | UUID | FK → users(id), NOT NULL | Assigned intermediary |
| assigned_by | UUID | FK → users(id), NOT NULL | Owner who made assignment |
| assigned_at | TIMESTAMP | DEFAULT NOW() | Assignment timestamp |
| removed_at | TIMESTAMP | NULL | Removal timestamp (soft delete) |
| is_active | BOOLEAN | DEFAULT TRUE | Active assignment flag |

**Unique Constraint**: (property_id, intermediary_id, is_active) WHERE is_active = TRUE

**Indexes**:
- `idx_pa_property` ON (property_id)
- `idx_pa_intermediary` ON (intermediary_id)
- `idx_pa_active` ON (is_active) WHERE is_active = TRUE

**Validation Rules**:
- `intermediary_id` must reference user with role='intermediary'
- `assigned_by` must reference user with role='owner'
- `assigned_by` must be the owner of `property_id`
- Cannot assign same intermediary to same property twice (active only)

---

### 4. Tenant

Represents a person renting a property.

**Table**: `tenants`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Tenant identifier |
| user_id | UUID | FK → users(id), UNIQUE, NOT NULL | Associated user account |
| property_id | UUID | FK → properties(id), NOT NULL | Rented property |
| intermediary_id | UUID | FK → users(id), NOT NULL | Managing intermediary |
| move_in_date | DATE | NOT NULL | Tenant move-in date |
| move_out_date | DATE | NULL | Tenant move-out date |
| monthly_rent | DECIMAL(12,2) | NOT NULL, CHECK > 0 | Monthly rent amount |
| security_deposit | DECIMAL(12,2) | NULL | Security deposit amount |
| electricity_rate | DECIMAL(8,4) | NULL | Per-unit electricity rate |
| status | ENUM('active', 'inactive', 'pending_move_out') | DEFAULT 'active' | Tenant status |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |
| created_by | UUID | FK → users(id), NOT NULL | User who created tenant |

**Indexes**:
- `idx_tenants_property` ON (property_id)
- `idx_tenants_intermediary` ON (intermediary_id)
- `idx_tenants_status` ON (status)
- `idx_tenants_user` ON (user_id)

**Validation Rules**:
- `move_out_date` must be > `move_in_date` if set
- `monthly_rent` must be positive
- `user_id` must reference user with role='tenant'
- `intermediary_id` must have active assignment to `property_id`
- `status` transitions: active → pending_move_out → inactive (one-way)

**Calculated Fields** (not stored):
- `days_stayed`: Current date - move_in_date (or move_out_date if set)
- `current_balance`: SUM(payments) - SUM(expected_rent + bill_allocations)

**RLS Policy**:
```sql
-- Tenants see only themselves
CREATE POLICY tenant_self_access ON tenants
  FOR SELECT
  USING (user_id = current_setting('app.current_user_id')::uuid);

-- Intermediaries see their assigned tenants
CREATE POLICY intermediary_tenant_access ON tenants
  FOR ALL
  USING (
    property_id IN (
      SELECT property_id FROM property_assignments
      WHERE intermediary_id = current_setting('app.current_user_id')::uuid
        AND is_active = TRUE
    )
  );

-- Owners see all tenants in their properties
CREATE POLICY owner_tenant_access ON tenants
  FOR ALL
  USING (
    property_id IN (
      SELECT id FROM properties
      WHERE owner_id = current_setting('app.current_user_id')::uuid
    )
  );
```

---

### 5. Payment

Represents a financial transaction (rent payment, security deposit, etc.).

**Table**: `payments`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Payment identifier |
| tenant_id | UUID | FK → tenants(id), NOT NULL | Paying tenant |
| property_id | UUID | FK → properties(id), NOT NULL | Related property |
| amount | DECIMAL(12,2) | NOT NULL, CHECK > 0 | Payment amount |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 currency code |
| payment_method | ENUM('cash', 'bank_transfer', 'online', 'upi', 'card', 'other') | NOT NULL | Payment method |
| payment_type | ENUM('rent', 'security_deposit', 'bill_share', 'penalty', 'other') | NOT NULL | Type of payment |
| payment_date | DATE | NOT NULL | Date payment received |
| reference_number | VARCHAR(100) | NULL | Transaction reference |
| notes | TEXT | NULL | Additional notes |
| receipt_url | VARCHAR(500) | NULL | S3 URL to receipt PDF |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| created_by | UUID | FK → users(id), NOT NULL | User who recorded payment |
| device_id | VARCHAR(100) | NULL | Device that created record (for sync) |
| is_voided | BOOLEAN | DEFAULT FALSE | Payment voided flag |
| voided_at | TIMESTAMP | NULL | Void timestamp |
| voided_by | UUID | FK → users(id), NULL | User who voided payment |
| void_reason | TEXT | NULL | Reason for voiding |

**Indexes**:
- `idx_payments_tenant` ON (tenant_id)
- `idx_payments_property` ON (property_id)
- `idx_payments_date` ON (payment_date DESC)
- `idx_payments_type` ON (payment_type)

**Validation Rules**:
- `currency` must match property's `base_currency`
- `payment_date` cannot be in future
- `amount` must be positive
- `is_voided` immutable once TRUE (cannot un-void)
- When voiding: `voided_at`, `voided_by`, `void_reason` all required

**Immutability**: Payments are append-only. Corrections done via void + new payment.

---

### 6. Transaction

Represents online payment gateway transaction (Stripe, Razorpay, PayPal).

**Table**: `transactions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Transaction identifier |
| payment_id | UUID | FK → payments(id), UNIQUE, NOT NULL | Associated payment record |
| gateway | ENUM('stripe', 'razorpay', 'paypal') | NOT NULL | Payment gateway used |
| gateway_transaction_id | VARCHAR(255) | UNIQUE, NOT NULL | Gateway's transaction ID |
| gateway_payment_intent | VARCHAR(255) | NULL | Payment intent ID |
| amount | DECIMAL(12,2) | NOT NULL | Transaction amount |
| currency | VARCHAR(3) | NOT NULL | Transaction currency |
| status | ENUM('pending', 'processing', 'succeeded', 'failed', 'refunded', 'partially_refunded') | DEFAULT 'pending' | Transaction status |
| payment_method_type | VARCHAR(50) | NULL | card, upi, wallet, etc. |
| payment_method_last4 | VARCHAR(4) | NULL | Last 4 digits of card/account |
| gateway_fee | DECIMAL(12,2) | NULL | Gateway processing fee |
| failure_code | VARCHAR(100) | NULL | Failure reason code |
| failure_message | TEXT | NULL | Human-readable failure message |
| metadata | JSONB | NULL | Additional gateway-specific data |
| created_at | TIMESTAMP | DEFAULT NOW() | Transaction creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last status update timestamp |

**Indexes**:
- `idx_transactions_payment` ON (payment_id)
- `idx_transactions_gateway_id` ON (gateway_transaction_id)
- `idx_transactions_status` ON (status)

**State Transitions**:
```
pending → processing → succeeded
                     → failed
succeeded → refunded
          → partially_refunded
```

**Validation Rules**:
- `gateway_transaction_id` must be unique across all gateways
- `amount` and `currency` must match linked payment
- Status transitions must follow state machine
- `failure_code` and `failure_message` required when status='failed'

---

### 7. Bill

Represents a utility or service bill for a property.

**Table**: `bills`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Bill identifier |
| property_id | UUID | FK → properties(id), NOT NULL | Related property |
| bill_type | ENUM('electricity', 'water', 'gas', 'maintenance', 'internet', 'other') | NOT NULL | Type of bill |
| billing_period_start | DATE | NOT NULL | Billing period start date |
| billing_period_end | DATE | NOT NULL | Billing period end date |
| total_amount | DECIMAL(12,2) | NOT NULL, CHECK > 0 | Total bill amount |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 currency code |
| due_date | DATE | NOT NULL | Payment due date |
| bill_number | VARCHAR(100) | NULL | Utility bill number |
| units_consumed | DECIMAL(10,2) | NULL | Units consumed (for electricity/water) |
| rate_per_unit | DECIMAL(10,4) | NULL | Rate per unit |
| notes | TEXT | NULL | Additional notes |
| receipt_url | VARCHAR(500) | NULL | S3 URL to bill document |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| created_by | UUID | FK → users(id), NOT NULL | User who created bill |
| recurring_bill_id | UUID | FK → recurring_bills(id), NULL | Source recurring bill |

**Indexes**:
- `idx_bills_property` ON (property_id)
- `idx_bills_period` ON (billing_period_start, billing_period_end)
- `idx_bills_type` ON (bill_type)
- `idx_bills_due_date` ON (due_date)

**Validation Rules**:
- `billing_period_end` must be > `billing_period_start`
- `due_date` typically >= `billing_period_end`
- `currency` must match property's `base_currency`
- `total_amount` must equal sum of all bill_allocations amounts

---

### 8. BillAllocation

Represents a tenant's share of a bill.

**Table**: `bill_allocations`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Allocation identifier |
| bill_id | UUID | FK → bills(id), NOT NULL | Parent bill |
| tenant_id | UUID | FK → tenants(id), NOT NULL | Assigned tenant |
| allocation_type | ENUM('percentage', 'fixed_amount') | NOT NULL | Division method |
| allocation_value | DECIMAL(10,4) | NOT NULL | Percentage or fixed amount |
| allocated_amount | DECIMAL(12,2) | NOT NULL, CHECK >= 0 | Calculated amount for tenant |
| paid_amount | DECIMAL(12,2) | DEFAULT 0.00 | Amount paid by tenant |
| status | ENUM('pending', 'partially_paid', 'paid') | DEFAULT 'pending' | Payment status |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Unique Constraint**: (bill_id, tenant_id)

**Indexes**:
- `idx_ba_bill` ON (bill_id)
- `idx_ba_tenant` ON (tenant_id)
- `idx_ba_status` ON (status)

**Validation Rules**:
- For percentage allocation: `allocation_value` must be 0-100
- `paid_amount` cannot exceed `allocated_amount`
- Status derived from paid_amount:
  - pending: paid_amount = 0
  - partially_paid: 0 < paid_amount < allocated_amount
  - paid: paid_amount >= allocated_amount

---

### 9. RecurringBill

Template for automatically creating monthly bills.

**Table**: `recurring_bills`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Recurring bill identifier |
| property_id | UUID | FK → properties(id), NOT NULL | Related property |
| bill_type | ENUM('electricity', 'water', 'gas', 'maintenance', 'internet', 'other') | NOT NULL | Type of bill |
| name | VARCHAR(255) | NOT NULL | Recurring bill name |
| expected_amount | DECIMAL(12,2) | NULL | Expected monthly amount (can be NULL for variable bills) |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 currency code |
| generation_day | INTEGER | NOT NULL, CHECK 1-28 | Day of month to generate |
| due_days_after | INTEGER | NOT NULL, CHECK >= 0 | Days after generation for due date |
| allocation_rules | JSONB | NOT NULL | Division rules per tenant |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| start_date | DATE | NOT NULL | First generation date |
| end_date | DATE | NULL | Last generation date (NULL = indefinite) |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| created_by | UUID | FK → users(id), NOT NULL | User who created template |

**Indexes**:
- `idx_rb_property` ON (property_id)
- `idx_rb_active` ON (is_active) WHERE is_active = TRUE
- `idx_rb_generation_day` ON (generation_day)

**Validation Rules**:
- `generation_day` must be 1-28 (avoid month-end complications)
- `allocation_rules` JSON schema:
  ```json
  [
    {"tenant_id": "uuid", "type": "percentage", "value": 33.33},
    {"tenant_id": "uuid", "type": "fixed_amount", "value": 1000.00}
  ]
  ```
- Sum of percentage allocations must equal 100
- `end_date` must be > `start_date` if set

---

### 10. Expense

Represents property maintenance or emergency expense.

**Table**: `expenses`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Expense identifier |
| property_id | UUID | FK → properties(id), NOT NULL | Related property |
| category | ENUM('maintenance', 'repair', 'cleaning', 'renovation', 'emergency', 'other') | NOT NULL | Expense category |
| description | TEXT | NOT NULL | Expense description |
| amount | DECIMAL(12,2) | NOT NULL, CHECK > 0 | Expense amount |
| currency | VARCHAR(3) | NOT NULL | ISO 4217 currency code |
| expense_date | DATE | NOT NULL | Date expense occurred |
| paid_by | ENUM('owner', 'intermediary', 'tenant') | NOT NULL | Who paid |
| paid_by_user_id | UUID | FK → users(id), NULL | Specific user who paid |
| approval_status | ENUM('pending', 'approved', 'rejected') | DEFAULT 'approved' | Approval status |
| approved_by | UUID | FK → users(id), NULL | User who approved |
| approved_at | TIMESTAMP | NULL | Approval timestamp |
| receipt_urls | TEXT[] | NULL | Array of S3 URLs to receipts |
| notes | TEXT | NULL | Additional notes |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| created_by | UUID | FK → users(id), NOT NULL | User who recorded expense |

**Indexes**:
- `idx_expenses_property` ON (property_id)
- `idx_expenses_category` ON (category)
- `idx_expenses_date` ON (expense_date DESC)
- `idx_expenses_approval` ON (approval_status)

**Validation Rules**:
- `currency` must match property's `base_currency`
- `expense_date` cannot be in future
- `amount` must be positive
- If `approval_status` = 'approved' or 'rejected', `approved_by` and `approved_at` required

---

### 11. Document

Represents a stored file (lease agreement, ID proof, etc.).

**Table**: `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Document identifier |
| property_id | UUID | FK → properties(id), NULL | Related property |
| tenant_id | UUID | FK → tenants(id), NULL | Related tenant |
| document_type | ENUM('lease_agreement', 'id_proof', 'noc', 'police_verification', 'other') | NOT NULL | Document type |
| title | VARCHAR(255) | NOT NULL | Document title |
| description | TEXT | NULL | Document description |
| file_name | VARCHAR(255) | NOT NULL | Original file name |
| file_size | BIGINT | NOT NULL | File size in bytes |
| mime_type | VARCHAR(100) | NOT NULL | MIME type |
| s3_key | VARCHAR(500) | NOT NULL | S3 object key |
| version | INTEGER | DEFAULT 1 | Document version number |
| previous_version_id | UUID | FK → documents(id), NULL | Previous version reference |
| expiration_date | DATE | NULL | Document expiration date |
| tags | TEXT[] | NULL | Searchable tags |
| uploaded_by | UUID | FK → users(id), NOT NULL | User who uploaded |
| created_at | TIMESTAMP | DEFAULT NOW() | Upload timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_documents_property` ON (property_id)
- `idx_documents_tenant` ON (tenant_id)
- `idx_documents_type` ON (document_type)
- `idx_documents_expiration` ON (expiration_date) WHERE expiration_date IS NOT NULL
- `idx_documents_tags` ON USING GIN (tags)

**Validation Rules**:
- Either `property_id` or `tenant_id` must be NOT NULL (at least one)
- `file_size` cannot exceed 10 MB (10,485,760 bytes)
- `mime_type` must be in allowed list: application/pdf, image/jpeg, image/png
- `version` auto-increments when new version uploaded

---

### 12. Message

Represents SMS/WhatsApp message sent to tenant.

**Table**: `messages`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Message identifier |
| tenant_id | UUID | FK → tenants(id), NOT NULL | Recipient tenant |
| property_id | UUID | FK → properties(id), NOT NULL | Related property |
| message_type | ENUM('rent_reminder', 'bill_notification', 'payment_confirmation', 'custom') | NOT NULL | Message type |
| channel | ENUM('sms', 'whatsapp', 'both') | NOT NULL | Delivery channel |
| template_id | VARCHAR(100) | NULL | Template identifier |
| message_content | TEXT | NOT NULL | Message text |
| scheduled_at | TIMESTAMP | NULL | Scheduled send time |
| sent_at | TIMESTAMP | NULL | Actual send time |
| delivery_status | ENUM('pending', 'sent', 'delivered', 'failed', 'read') | DEFAULT 'pending' | Delivery status |
| gateway_message_id | VARCHAR(255) | NULL | Gateway message ID |
| failure_reason | TEXT | NULL | Failure reason if failed |
| created_at | TIMESTAMP | DEFAULT NOW() | Message creation timestamp |
| created_by | UUID | FK → users(id), NOT NULL | User who created message |

**Indexes**:
- `idx_messages_tenant` ON (tenant_id)
- `idx_messages_scheduled` ON (scheduled_at) WHERE scheduled_at IS NOT NULL AND sent_at IS NULL
- `idx_messages_status` ON (delivery_status)

**State Transitions**:
```
pending → sent → delivered → read
               → failed
```

**Validation Rules**:
- `scheduled_at` cannot be in past (if set)
- `sent_at` must be >= `scheduled_at` (if scheduled)
- `message_content` max length: 1600 characters (SMS limit consideration)

---

### 13. Notification

Represents push notification sent to user.

**Table**: `notifications`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Notification identifier |
| user_id | UUID | FK → users(id), NOT NULL | Recipient user |
| notification_type | ENUM('rent_reminder', 'bill_allocated', 'payment_received', 'document_uploaded', 'system_alert') | NOT NULL | Notification type |
| title | VARCHAR(255) | NOT NULL | Notification title |
| body | TEXT | NOT NULL | Notification body |
| data | JSONB | NULL | Additional data payload |
| related_entity_type | VARCHAR(50) | NULL | Entity type (payment, bill, etc.) |
| related_entity_id | UUID | NULL | Entity identifier |
| is_read | BOOLEAN | DEFAULT FALSE | Read status |
| read_at | TIMESTAMP | NULL | Read timestamp |
| sent_at | TIMESTAMP | DEFAULT NOW() | Send timestamp |
| fcm_message_id | VARCHAR(255) | NULL | FCM message ID |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |

**Indexes**:
- `idx_notifications_user` ON (user_id)
- `idx_notifications_unread` ON (user_id, is_read) WHERE is_read = FALSE
- `idx_notifications_type` ON (notification_type)

**Validation Rules**:
- `title` max length: 255 characters
- `body` max length: 4000 characters
- `is_read` can only transition FALSE → TRUE (not reversible)
- `read_at` automatically set when `is_read` becomes TRUE

---

### 14. ReportTemplate

Represents saved report configuration.

**Table**: `report_templates`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Template identifier |
| property_id | UUID | FK → properties(id), NULL | Property scope (NULL = all) |
| owner_id | UUID | FK → users(id), NOT NULL | Template owner |
| name | VARCHAR(255) | NOT NULL | Template name |
| report_type | ENUM('financial_summary', 'tax_statement', 'payment_history', 'expense_report', 'occupancy_report', 'custom') | NOT NULL | Report type |
| configuration | JSONB | NOT NULL | Report parameters |
| schedule | ENUM('manual', 'daily', 'weekly', 'monthly', 'quarterly', 'annually') | DEFAULT 'manual' | Generation schedule |
| last_generated_at | TIMESTAMP | NULL | Last generation timestamp |
| next_generation_at | TIMESTAMP | NULL | Next scheduled generation |
| output_format | ENUM('pdf', 'excel', 'csv') | DEFAULT 'pdf' | Output format |
| recipients | TEXT[] | NULL | Email recipients for scheduled reports |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `idx_rt_owner` ON (owner_id)
- `idx_rt_property` ON (property_id)
- `idx_rt_schedule` ON (next_generation_at) WHERE is_active = TRUE AND schedule != 'manual'

**Validation Rules**:
- `configuration` JSON schema varies by `report_type`
- If `schedule` != 'manual', `next_generation_at` required
- `recipients` array must contain valid email addresses

---

### 15. SyncLog

Represents data synchronization event.

**Table**: `sync_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Sync log identifier |
| user_id | UUID | FK → users(id), NOT NULL | User who synced |
| device_id | VARCHAR(100) | NOT NULL | Device identifier |
| sync_direction | ENUM('push', 'pull') | NOT NULL | Sync direction |
| entity_type | VARCHAR(50) | NOT NULL | Entity being synced |
| entity_id | UUID | NULL | Specific entity ID |
| operation | ENUM('create', 'update', 'delete') | NOT NULL | CRUD operation |
| status | ENUM('success', 'failed', 'conflict') | NOT NULL | Sync status |
| error_message | TEXT | NULL | Error message if failed |
| conflict_data | JSONB | NULL | Conflict details |
| records_synced | INTEGER | DEFAULT 1 | Number of records |
| started_at | TIMESTAMP | NOT NULL | Sync start timestamp |
| completed_at | TIMESTAMP | NULL | Sync completion timestamp |
| created_at | TIMESTAMP | DEFAULT NOW() | Log creation timestamp |

**Indexes**:
- `idx_sl_user` ON (user_id)
- `idx_sl_device` ON (device_id)
- `idx_sl_status` ON (status)
- `idx_sl_started` ON (started_at DESC)

**Validation Rules**:
- If `status` = 'failed', `error_message` required
- If `status` = 'conflict', `conflict_data` required with both versions

---

## Relationships Summary

| Parent | Child | Relationship | Cascade |
|--------|-------|--------------|---------|
| User (Owner) | Property | 1:M | RESTRICT (prevent deletion if properties exist) |
| Property | PropertyAssignment | 1:M | CASCADE |
| User (Intermediary) | PropertyAssignment | 1:M | CASCADE |
| Property | Tenant | 1:M | RESTRICT |
| User (Tenant) | Tenant | 1:1 | CASCADE |
| Tenant | Payment | 1:M | RESTRICT |
| Payment | Transaction | 1:1 | CASCADE |
| Property | Bill | 1:M | RESTRICT |
| Bill | BillAllocation | 1:M | CASCADE |
| Tenant | BillAllocation | 1:M | RESTRICT |
| Property | RecurringBill | 1:M | RESTRICT |
| RecurringBill | Bill | 1:M | SET NULL |
| Property | Expense | 1:M | RESTRICT |
| Property | Document | 1:M | CASCADE |
| Tenant | Document | 1:M | CASCADE |
| Tenant | Message | 1:M | RESTRICT |
| User | Notification | 1:M | CASCADE |
| User (Owner) | ReportTemplate | 1:M | CASCADE |
| User | SyncLog | 1:M | CASCADE |

**Cascade Strategy**:
- **CASCADE**: Child deleted when parent deleted (safe for dependent data)
- **RESTRICT**: Prevent parent deletion if children exist (preserve financial data)
- **SET NULL**: Child's FK set to NULL when parent deleted (preserve child)

---

## Data Integrity Constraints

### Business Rules Enforced by Database

1. **Single Currency Per Property**:
   ```sql
   ALTER TABLE payments ADD CONSTRAINT payment_currency_match
     CHECK (currency = (SELECT base_currency FROM properties WHERE id = property_id));
   ```

2. **Payment Amount Positivity**:
   ```sql
   ALTER TABLE payments ADD CONSTRAINT payment_amount_positive
     CHECK (amount > 0);
   ```

3. **Bill Allocation Sum**:
   ```sql
   CREATE FUNCTION check_bill_allocation_sum() RETURNS TRIGGER AS $$
   BEGIN
     IF (SELECT SUM(allocated_amount) FROM bill_allocations WHERE bill_id = NEW.bill_id)
        > (SELECT total_amount FROM bills WHERE id = NEW.bill_id) THEN
       RAISE EXCEPTION 'Bill allocation sum exceeds total bill amount';
     END IF;
     RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER bill_allocation_sum_check
     AFTER INSERT OR UPDATE ON bill_allocations
     FOR EACH ROW EXECUTE FUNCTION check_bill_allocation_sum();
   ```

4. **Tenant Status Transition**:
   ```sql
   CREATE FUNCTION check_tenant_status_transition() RETURNS TRIGGER AS $$
   BEGIN
     IF OLD.status = 'inactive' AND NEW.status != 'inactive' THEN
       RAISE EXCEPTION 'Cannot reactivate inactive tenant';
     END IF;
     RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER tenant_status_transition_check
     BEFORE UPDATE ON tenants
     FOR EACH ROW EXECUTE FUNCTION check_tenant_status_transition();
   ```

5. **Intermediary Role Validation**:
   ```sql
   ALTER TABLE property_assignments ADD CONSTRAINT intermediary_role_check
     CHECK ((SELECT role FROM users WHERE id = intermediary_id) = 'intermediary');
   ```

---

## Performance Optimization

### Materialized Views

#### 1. Tenant Balance Summary
```sql
CREATE MATERIALIZED VIEW tenant_balance_summary AS
SELECT
  t.id AS tenant_id,
  t.property_id,
  t.monthly_rent,
  COALESCE(SUM(p.amount), 0) AS total_paid,
  (
    (EXTRACT(YEAR FROM AGE(COALESCE(t.move_out_date, CURRENT_DATE), t.move_in_date)) * 12 +
     EXTRACT(MONTH FROM AGE(COALESCE(t.move_out_date, CURRENT_DATE), t.move_in_date)))
    * t.monthly_rent
  ) AS total_expected_rent,
  COALESCE(SUM(ba.allocated_amount), 0) AS total_bill_allocations,
  (
    COALESCE(SUM(p.amount), 0) -
    (
      (EXTRACT(YEAR FROM AGE(COALESCE(t.move_out_date, CURRENT_DATE), t.move_in_date)) * 12 +
       EXTRACT(MONTH FROM AGE(COALESCE(t.move_out_date, CURRENT_DATE), t.move_in_date)))
      * t.monthly_rent
    ) -
    COALESCE(SUM(ba.allocated_amount), 0)
  ) AS current_balance
FROM tenants t
LEFT JOIN payments p ON t.id = p.tenant_id AND p.is_voided = FALSE
LEFT JOIN bill_allocations ba ON t.id = ba.tenant_id
GROUP BY t.id, t.property_id, t.monthly_rent, t.move_in_date, t.move_out_date;

CREATE UNIQUE INDEX idx_tbs_tenant ON tenant_balance_summary (tenant_id);
CREATE INDEX idx_tbs_property ON tenant_balance_summary (property_id);

-- Refresh strategy: Hourly via Celery task
```

#### 2. Property Revenue Summary
```sql
CREATE MATERIALIZED VIEW property_revenue_summary AS
SELECT
  p.id AS property_id,
  p.owner_id,
  DATE_TRUNC('month', pm.payment_date) AS month,
  SUM(pm.amount) AS total_revenue,
  COUNT(DISTINCT pm.tenant_id) AS paying_tenants,
  COALESCE(SUM(e.amount), 0) AS total_expenses,
  SUM(pm.amount) - COALESCE(SUM(e.amount), 0) AS net_income
FROM properties p
LEFT JOIN payments pm ON p.id = pm.property_id AND pm.is_voided = FALSE
LEFT JOIN expenses e ON p.id = e.property_id AND DATE_TRUNC('month', e.expense_date) = DATE_TRUNC('month', pm.payment_date)
GROUP BY p.id, p.owner_id, DATE_TRUNC('month', pm.payment_date);

CREATE INDEX idx_prs_property_month ON property_revenue_summary (property_id, month DESC);
CREATE INDEX idx_prs_owner ON property_revenue_summary (owner_id);
```

### Partitioning Strategy

#### Time-based Partitioning for Logs
```sql
-- Partition sync_logs by month for better performance
CREATE TABLE sync_logs_template (LIKE sync_logs INCLUDING ALL);

CREATE TABLE sync_logs_2025_01 PARTITION OF sync_logs
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE sync_logs_2025_02 PARTITION OF sync_logs
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Automatic partition creation via Celery task
```

---

## Migration Strategy

### Initial Schema Creation
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE user_role AS ENUM ('owner', 'intermediary', 'tenant');
CREATE TYPE payment_method AS ENUM ('cash', 'bank_transfer', 'online', 'upi', 'card', 'other');
CREATE TYPE payment_type AS ENUM ('rent', 'security_deposit', 'bill_share', 'penalty', 'other');
-- [Additional types...]

-- Create tables in dependency order
CREATE TABLE users (...);
CREATE TABLE properties (...);
CREATE TABLE property_assignments (...);
CREATE TABLE tenants (...);
-- [Additional tables...]

-- Add foreign key constraints
ALTER TABLE properties ADD CONSTRAINT fk_properties_owner
  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT;
-- [Additional constraints...]

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
-- [Additional indexes...]

-- Enable Row-Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_self_access ON users ...;
-- [Additional RLS policies...]

-- Create materialized views
CREATE MATERIALIZED VIEW tenant_balance_summary AS ...;
-- [Additional views...]
```

---

## Backup & Recovery

### Backup Strategy
- **Full backup**: Daily at 2 AM UTC (pg_dump)
- **Incremental backup**: Continuous WAL archiving
- **Retention**: 30 days of full backups, 7 days of WAL
- **Testing**: Monthly restore test to staging environment

### Point-in-Time Recovery
```bash
# Restore to specific timestamp
pg_restore --dbname=meroghar_recovery \
           --clean --if-exists \
           backup_2025-01-26.dump

# Apply WAL logs to specific time
pg_waldump --start=... --end=... wal_archive/
```

---

**Data Model Complete**: All entities defined with fields, relationships, validation rules, RLS policies, indexes, and performance optimizations. Ready for API contract generation.