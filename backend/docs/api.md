# MeroGhar API Documentation

**Version**: 1.0.0  
**Base URL**: `https://api.meroghar.com/api/v1`  
**Environment**: Production

## Table of Contents

1. [Authentication](#authentication)
2. [Users](#users)
3. [Properties](#properties)
4. [Tenants](#tenants)
5. [Payments](#payments)
6. [Bills](#bills)
7. [Expenses](#expenses)
8. [Documents](#documents)
9. [Messages](#messages)
10. [Notifications](#notifications)
11. [Reports](#reports)
12. [Analytics](#analytics)
13. [Sync](#sync)
14. [Webhooks](#webhooks)
15. [Error Handling](#error-handling)
16. [Rate Limiting](#rate-limiting)

---

## Authentication

All authenticated endpoints require a valid JWT token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### Register User

**POST** `/auth/register`

Create a new user account (Owner role only for self-registration).

**Request Body**:

```json
{
  "email": "owner@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone": "+977-9841234567"
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "email": "owner@example.com",
  "full_name": "John Doe",
  "role": "OWNER",
  "created_at": "2025-01-15T10:30:00Z",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors**:

- `400 Bad Request`: Invalid email format or weak password
- `409 Conflict`: Email already registered

---

### Login

**POST** `/auth/login`

Authenticate existing user and receive JWT tokens.

**Request Body**:

```json
{
  "email": "owner@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):

```json
{
  "user": {
    "id": "uuid",
    "email": "owner@example.com",
    "full_name": "John Doe",
    "role": "OWNER"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors**:

- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account disabled

---

### Refresh Token

**POST** `/auth/refresh`

Exchange refresh token for new access token.

**Request Body**:

```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Users

### Create Intermediary User

**POST** `/users`

**Permissions**: OWNER only

Create intermediary account for property management.

**Request Body**:

```json
{
  "email": "intermediary@example.com",
  "password": "SecurePass123!",
  "full_name": "Jane Smith",
  "phone": "+977-9841234567",
  "role": "INTERMEDIARY"
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "email": "intermediary@example.com",
  "full_name": "Jane Smith",
  "role": "INTERMEDIARY",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Get User Profile

**GET** `/users/me`

**Permissions**: All authenticated users

Retrieve current user's profile information.

**Response** (200 OK):

```json
{
  "id": "uuid",
  "email": "owner@example.com",
  "full_name": "John Doe",
  "phone": "+977-9841234567",
  "role": "OWNER",
  "language_preference": "en",
  "fcm_token": "firebase_token",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-20T14:20:00Z"
}
```

---

### Update User Profile

**PATCH** `/users/me`

**Permissions**: All authenticated users

**Request Body**:

```json
{
  "full_name": "John Updated Doe",
  "phone": "+977-9841234567",
  "language_preference": "hi"
}
```

**Response** (200 OK):

```json
{
  "id": "uuid",
  "email": "owner@example.com",
  "full_name": "John Updated Doe",
  "phone": "+977-9841234567",
  "language_preference": "hi"
}
```

---

## Properties

### Create Property

**POST** `/properties`

**Permissions**: OWNER only

**Request Body**:

```json
{
  "name": "Green Valley Apartments",
  "address": "Kathmandu, Nepal",
  "total_units": 10,
  "property_type": "APARTMENT",
  "description": "Modern apartments in central location"
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "name": "Green Valley Apartments",
  "address": "Kathmandu, Nepal",
  "total_units": 10,
  "property_type": "APARTMENT",
  "owner_id": "uuid",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Assign Intermediary to Property

**POST** `/properties/{property_id}/assign`

**Permissions**: OWNER only

**Request Body**:

```json
{
  "user_id": "intermediary_uuid",
  "permissions": ["VIEW", "CREATE_TENANT", "RECORD_PAYMENT"]
}
```

**Response** (200 OK):

```json
{
  "property_id": "uuid",
  "user_id": "uuid",
  "role": "INTERMEDIARY",
  "permissions": ["VIEW", "CREATE_TENANT", "RECORD_PAYMENT"],
  "assigned_at": "2025-01-15T10:30:00Z"
}
```

---

### List Properties

**GET** `/properties`

**Permissions**: OWNER sees all owned properties, INTERMEDIARY sees assigned properties

**Query Parameters**:

- `page` (integer, default: 1)
- `page_size` (integer, default: 20)
- `property_type` (string, optional)

**Response** (200 OK):

```json
{
  "total": 5,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "name": "Green Valley Apartments",
      "address": "Kathmandu, Nepal",
      "total_units": 10,
      "occupied_units": 7,
      "property_type": "APARTMENT"
    }
  ]
}
```

---

## Tenants

### Create Tenant

**POST** `/tenants`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "property_id": "uuid",
  "unit_number": "A-101",
  "full_name": "Alice Johnson",
  "email": "alice@example.com",
  "phone": "+977-9841234567",
  "move_in_date": "2025-02-01",
  "monthly_rent": 15000.0,
  "security_deposit": 30000.0,
  "billing_day": 1
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "property_id": "uuid",
  "user_id": "uuid",
  "unit_number": "A-101",
  "full_name": "Alice Johnson",
  "monthly_rent": 15000.0,
  "security_deposit": 30000.0,
  "move_in_date": "2025-02-01",
  "billing_day": 1,
  "status": "ACTIVE"
}
```

---

### List Tenants

**GET** `/tenants`

**Permissions**: OWNER sees all tenants, INTERMEDIARY sees assigned property tenants

**Query Parameters**:

- `property_id` (uuid, optional)
- `status` (string: ACTIVE, INACTIVE, optional)
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 15,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "full_name": "Alice Johnson",
      "unit_number": "A-101",
      "monthly_rent": 15000.0,
      "current_balance": -5000.0,
      "status": "ACTIVE",
      "payment_status": "OVERDUE"
    }
  ]
}
```

---

### Get Tenant Balance

**GET** `/tenants/{tenant_id}/balance`

**Permissions**: OWNER, INTERMEDIARY, TENANT (self only)

**Response** (200 OK):

```json
{
  "tenant_id": "uuid",
  "current_balance": -5000.0,
  "total_paid": 45000.0,
  "total_due": 50000.0,
  "last_payment_date": "2025-01-05",
  "next_due_date": "2025-02-01"
}
```

---

### Set Rent Increment Policy

**PUT** `/tenants/{tenant_id}/rent-policy`

**Permissions**: OWNER only

**Request Body**:

```json
{
  "increment_percentage": 5.0,
  "increment_frequency_months": 24,
  "next_increment_date": "2027-02-01",
  "notify_days_before": 30
}
```

**Response** (200 OK):

```json
{
  "tenant_id": "uuid",
  "rent_increment_policy": {
    "increment_percentage": 5.0,
    "increment_frequency_months": 24,
    "next_increment_date": "2027-02-01",
    "notify_days_before": 30
  }
}
```

---

### Get Rent History

**GET** `/tenants/{tenant_id}/rent-history`

**Permissions**: OWNER, TENANT (self only)

**Response** (200 OK):

```json
{
  "tenant_id": "uuid",
  "rent_history": [
    {
      "effective_date": "2025-02-01",
      "monthly_rent": 15000.0,
      "change_reason": "Initial rent"
    },
    {
      "effective_date": "2027-02-01",
      "monthly_rent": 15750.0,
      "change_reason": "5% automatic increment"
    }
  ]
}
```

---

## Payments

### Record Payment

**POST** `/payments`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "tenant_id": "uuid",
  "amount": 15000.0,
  "payment_method": "CASH",
  "payment_date": "2025-01-05",
  "notes": "January rent payment",
  "receipt_number": "REC-2025-001"
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "amount": 15000.0,
  "payment_method": "CASH",
  "payment_date": "2025-01-05",
  "status": "COMPLETED",
  "receipt_url": "/api/v1/payments/uuid/receipt",
  "created_at": "2025-01-05T14:30:00Z"
}
```

---

### Initiate Online Payment

**POST** `/payments/initiate`

**Permissions**: TENANT

**Request Body**:

```json
{
  "amount": 15000.0,
  "payment_method": "KHALTI",
  "return_url": "https://app.meroghar.com/payment/success"
}
```

**Response** (200 OK):

```json
{
  "payment_id": "uuid",
  "gateway": "KHALTI",
  "payment_url": "https://khalti.com/payment/xyz",
  "transaction_id": "TXN-123456",
  "status": "PENDING",
  "expires_at": "2025-01-05T15:00:00Z"
}
```

---

### Get Payment Status

**GET** `/payments/{payment_id}/status`

**Permissions**: All users (payment creator or property owner)

**Response** (200 OK):

```json
{
  "payment_id": "uuid",
  "status": "COMPLETED",
  "amount": 15000.0,
  "payment_method": "KHALTI",
  "transaction_id": "TXN-123456",
  "gateway_response": {
    "transaction_id": "KHALTI-789",
    "status": "SUCCESS"
  },
  "updated_at": "2025-01-05T14:35:00Z"
}
```

---

### Generate Receipt

**GET** `/payments/{payment_id}/receipt`

**Permissions**: All users (payment creator or property owner)

**Query Parameters**:

- `format` (string: pdf, json, default: pdf)

**Response** (200 OK):

- Content-Type: application/pdf (for PDF format)
- Content-Type: application/json (for JSON format)

**PDF Response**: Binary PDF file download

**JSON Response**:

```json
{
  "receipt_number": "REC-2025-001",
  "payment_id": "uuid",
  "tenant_name": "Alice Johnson",
  "amount": 15000.0,
  "payment_date": "2025-01-05",
  "payment_method": "CASH",
  "property": "Green Valley Apartments - A-101",
  "generated_at": "2025-01-05T14:30:00Z"
}
```

---

### Payment History

**GET** `/payments`

**Permissions**: OWNER sees all, INTERMEDIARY sees assigned properties, TENANT sees own

**Query Parameters**:

- `tenant_id` (uuid, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `payment_method` (string, optional)
- `status` (string, optional)
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 50,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "tenant_name": "Alice Johnson",
      "amount": 15000.0,
      "payment_method": "CASH",
      "payment_date": "2025-01-05",
      "status": "COMPLETED"
    }
  ]
}
```

---

### Export Payment History

**POST** `/payments/export`

**Permissions**: OWNER, TENANT (self only)

**Request Body**:

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "format": "EXCEL",
  "tenant_id": "uuid"
}
```

**Response** (200 OK):

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

Binary Excel file download with columns:

- Date, Tenant, Property, Amount, Method, Status, Receipt Number

---

## Bills

### Create Bill

**POST** `/bills`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "property_id": "uuid",
  "bill_type": "ELECTRICITY",
  "total_amount": 5000.0,
  "billing_period_start": "2025-01-01",
  "billing_period_end": "2025-01-31",
  "due_date": "2025-02-05",
  "notes": "January electricity bill"
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "property_id": "uuid",
  "bill_type": "ELECTRICITY",
  "total_amount": 5000.0,
  "billing_period_start": "2025-01-01",
  "billing_period_end": "2025-01-31",
  "due_date": "2025-02-05",
  "status": "PENDING_ALLOCATION",
  "created_at": "2025-01-02T10:00:00Z"
}
```

---

### Allocate Bill to Tenants

**POST** `/bills/{bill_id}/allocate`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "allocation_type": "PERCENTAGE",
  "allocations": [
    {
      "tenant_id": "uuid-1",
      "percentage": 40.0
    },
    {
      "tenant_id": "uuid-2",
      "percentage": 60.0
    }
  ]
}
```

**Response** (200 OK):

```json
{
  "bill_id": "uuid",
  "allocations": [
    {
      "id": "uuid",
      "tenant_id": "uuid-1",
      "tenant_name": "Alice Johnson",
      "amount": 2000.0,
      "percentage": 40.0,
      "status": "UNPAID"
    },
    {
      "id": "uuid",
      "tenant_id": "uuid-2",
      "tenant_name": "Bob Smith",
      "amount": 3000.0,
      "percentage": 60.0,
      "status": "UNPAID"
    }
  ]
}
```

---

### Mark Bill Allocation as Paid

**PATCH** `/bills/{bill_id}/allocations/{allocation_id}/pay`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "payment_method": "CASH",
  "payment_date": "2025-02-03",
  "notes": "Paid by tenant"
}
```

**Response** (200 OK):

```json
{
  "allocation_id": "uuid",
  "status": "PAID",
  "paid_date": "2025-02-03",
  "payment_method": "CASH"
}
```

---

### Setup Recurring Bill

**POST** `/bills/recurring`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "property_id": "uuid",
  "bill_type": "MAINTENANCE",
  "base_amount": 2000.0,
  "frequency": "MONTHLY",
  "day_of_month": 1,
  "allocation_template": [
    {
      "tenant_id": "uuid-1",
      "percentage": 50.0
    },
    {
      "tenant_id": "uuid-2",
      "percentage": 50.0
    }
  ]
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "property_id": "uuid",
  "bill_type": "MAINTENANCE",
  "frequency": "MONTHLY",
  "next_generation_date": "2025-02-01",
  "is_active": true
}
```

---

### List Bills

**GET** `/bills`

**Permissions**: OWNER sees all, INTERMEDIARY sees assigned properties, TENANT sees own allocations

**Query Parameters**:

- `property_id` (uuid, optional)
- `bill_type` (string, optional)
- `status` (string, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 25,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "bill_type": "ELECTRICITY",
      "total_amount": 5000.0,
      "billing_period": "January 2025",
      "due_date": "2025-02-05",
      "status": "ALLOCATED",
      "paid_allocations": 1,
      "total_allocations": 2
    }
  ]
}
```

---

## Expenses

### Record Expense

**POST** `/expenses`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "property_id": "uuid",
  "category": "MAINTENANCE",
  "amount": 3500.0,
  "expense_date": "2025-01-10",
  "description": "Plumbing repair in unit A-101",
  "paid_by": "INTERMEDIARY",
  "requires_approval": true
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "property_id": "uuid",
  "category": "MAINTENANCE",
  "amount": 3500.0,
  "expense_date": "2025-01-10",
  "status": "PENDING_APPROVAL",
  "created_by": "uuid",
  "created_at": "2025-01-10T16:00:00Z"
}
```

---

### Upload Expense Receipt

**POST** `/expenses/{expense_id}/receipt`

**Permissions**: OWNER, INTERMEDIARY (expense creator)

**Request**: Multipart form-data

- `file`: Image or PDF file (max 5MB)

**Response** (200 OK):

```json
{
  "expense_id": "uuid",
  "receipt_url": "https://s3.amazonaws.com/meroghar/receipts/uuid.pdf",
  "uploaded_at": "2025-01-10T16:05:00Z"
}
```

---

### Approve Expense

**PATCH** `/expenses/{expense_id}/approve`

**Permissions**: OWNER only

**Request Body**:

```json
{
  "approved": true,
  "notes": "Approved for reimbursement"
}
```

**Response** (200 OK):

```json
{
  "expense_id": "uuid",
  "status": "APPROVED",
  "approved_by": "uuid",
  "approved_at": "2025-01-11T09:00:00Z"
}
```

---

### List Expenses

**GET** `/expenses`

**Permissions**: OWNER sees all, INTERMEDIARY sees own expenses

**Query Parameters**:

- `property_id` (uuid, optional)
- `category` (string, optional)
- `status` (string, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 30,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "category": "MAINTENANCE",
      "amount": 3500.0,
      "expense_date": "2025-01-10",
      "description": "Plumbing repair",
      "status": "APPROVED",
      "receipt_url": "https://..."
    }
  ]
}
```

---

## Documents

### Upload Document

**POST** `/documents`

**Permissions**: All authenticated users

**Request**: Multipart form-data

- `file`: PDF or image (max 10MB)
- `document_type`: LEASE, ID_PROOF, etc.
- `tenant_id`: (optional, for tenant documents)
- `expiration_date`: (optional, for expiring documents)

**Response** (201 Created):

```json
{
  "id": "uuid",
  "document_type": "LEASE",
  "file_url": "https://s3.amazonaws.com/meroghar/documents/uuid.pdf",
  "file_name": "lease_agreement.pdf",
  "file_size": 1048576,
  "expiration_date": "2026-01-31",
  "uploaded_by": "uuid",
  "uploaded_at": "2025-01-15T10:00:00Z"
}
```

---

### Download Document

**GET** `/documents/{document_id}/download`

**Permissions**: OWNER, document uploader, assigned TENANT

**Response** (200 OK):

- Content-Type: application/pdf or image/\*
- Content-Disposition: attachment; filename="lease_agreement.pdf"

Binary file download

---

### List Documents

**GET** `/documents`

**Permissions**: OWNER sees all, TENANT sees own

**Query Parameters**:

- `document_type` (string, optional)
- `tenant_id` (uuid, optional)
- `expiring_soon` (boolean, optional) - documents expiring in next 30 days
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 15,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "document_type": "LEASE",
      "file_name": "lease_agreement.pdf",
      "expiration_date": "2026-01-31",
      "days_until_expiry": 365,
      "uploaded_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

## Messages

### Send Bulk Message

**POST** `/messages/bulk`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "tenant_ids": ["uuid-1", "uuid-2", "uuid-3"],
  "message_type": "SMS",
  "template_id": "payment_reminder",
  "variables": {
    "amount": "15000",
    "due_date": "2025-02-01"
  }
}
```

**Response** (200 OK):

```json
{
  "message_batch_id": "uuid",
  "total_recipients": 3,
  "messages": [
    {
      "id": "uuid",
      "tenant_id": "uuid-1",
      "status": "SENT",
      "sent_at": "2025-01-25T10:00:00Z"
    }
  ]
}
```

---

### Schedule Message

**POST** `/messages/schedule`

**Permissions**: OWNER, INTERMEDIARY

**Request Body**:

```json
{
  "tenant_ids": ["uuid-1", "uuid-2"],
  "message_type": "WHATSAPP",
  "template_id": "rent_reminder",
  "schedule_date": "2025-01-30T09:00:00Z",
  "recurrence": "MONTHLY"
}
```

**Response** (201 Created):

```json
{
  "schedule_id": "uuid",
  "next_send_date": "2025-01-30T09:00:00Z",
  "recurrence": "MONTHLY",
  "is_active": true
}
```

---

### Message History

**GET** `/messages`

**Permissions**: OWNER, INTERMEDIARY

**Query Parameters**:

- `tenant_id` (uuid, optional)
- `message_type` (string, optional)
- `status` (string, optional)
- `start_date` (date, optional)
- `end_date` (date, optional)
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "tenant_name": "Alice Johnson",
      "message_type": "SMS",
      "content": "Your rent of NPR 15000 is due...",
      "status": "DELIVERED",
      "sent_at": "2025-01-25T10:00:00Z"
    }
  ]
}
```

---

## Notifications

### Create Notification

**POST** `/notifications`

**Permissions**: System or OWNER

**Request Body**:

```json
{
  "user_id": "uuid",
  "title": "Payment Received",
  "body": "Alice Johnson paid NPR 15000",
  "notification_type": "PAYMENT",
  "data": {
    "payment_id": "uuid",
    "amount": 15000
  }
}
```

**Response** (201 Created):

```json
{
  "id": "uuid",
  "title": "Payment Received",
  "body": "Alice Johnson paid NPR 15000",
  "notification_type": "PAYMENT",
  "is_read": false,
  "created_at": "2025-01-05T14:30:00Z"
}
```

---

### List Notifications

**GET** `/notifications`

**Permissions**: All authenticated users (own notifications only)

**Query Parameters**:

- `is_read` (boolean, optional)
- `notification_type` (string, optional)
- `page` (integer, default: 1)
- `page_size` (integer, default: 20)

**Response** (200 OK):

```json
{
  "total": 50,
  "unread_count": 5,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "title": "Payment Received",
      "body": "Alice Johnson paid NPR 15000",
      "notification_type": "PAYMENT",
      "is_read": false,
      "created_at": "2025-01-05T14:30:00Z"
    }
  ]
}
```

---

### Mark Notification as Read

**PATCH** `/notifications/{notification_id}/read`

**Permissions**: All authenticated users (own notifications only)

**Response** (200 OK):

```json
{
  "notification_id": "uuid",
  "is_read": true,
  "read_at": "2025-01-05T15:00:00Z"
}
```

---

## Reports

### Annual Income Statement

**GET** `/reports/tax/income`

**Permissions**: OWNER only

**Query Parameters**:

- `year` (integer, required) - e.g., 2025

**Response** (200 OK):

```json
{
  "year": 2025,
  "total_rental_income": 180000.0,
  "breakdown_by_property": [
    {
      "property_id": "uuid",
      "property_name": "Green Valley Apartments",
      "total_income": 180000.0,
      "by_month": {
        "1": 15000.0,
        "2": 15000.0
      }
    }
  ],
  "by_payment_method": {
    "CASH": 90000.0,
    "KHALTI": 90000.0
  },
  "currency": "NPR"
}
```

---

### Tax Deductible Expenses

**GET** `/reports/tax/deductions`

**Permissions**: OWNER only

**Query Parameters**:

- `year` (integer, required)

**Response** (200 OK):

```json
{
  "year": 2025,
  "total_deductible": 45000.0,
  "total_non_deductible": 5000.0,
  "by_category": {
    "MAINTENANCE": 20000.0,
    "REPAIRS": 15000.0,
    "INSURANCE": 10000.0
  },
  "by_property": [
    {
      "property_id": "uuid",
      "property_name": "Green Valley Apartments",
      "deductible_amount": 45000.0
    }
  ]
}
```

---

### GST/VAT Report

**GET** `/reports/tax/gst`

**Permissions**: OWNER only

**Query Parameters**:

- `year` (integer, required)
- `quarter` (integer, required) - 1, 2, 3, or 4

**Response** (200 OK):

```json
{
  "year": 2025,
  "quarter": 1,
  "period_start": "2025-01-01",
  "period_end": "2025-03-31",
  "gst_rate": 0.13,
  "taxable_income": 45000.0,
  "output_gst": 5850.0,
  "taxable_expenses": 10000.0,
  "input_gst": 1300.0,
  "net_gst_payable": 4550.0,
  "currency": "NPR"
}
```

---

### Profit & Loss Statement

**GET** `/reports/financial/pnl`

**Permissions**: OWNER only

**Query Parameters**:

- `start_date` (date, required)
- `end_date` (date, required)

**Response** (200 OK):

```json
{
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "revenue": {
    "rental_income": 180000.0,
    "utility_reimbursements": 15000.0,
    "other_income": 5000.0,
    "total_revenue": 200000.0
  },
  "expenses": {
    "maintenance": 20000.0,
    "repairs": 15000.0,
    "insurance": 10000.0,
    "total_expenses": 45000.0
  },
  "profit": {
    "gross_profit": 200000.0,
    "operating_profit": 155000.0,
    "net_profit": 155000.0,
    "profit_margin": 0.775
  },
  "currency": "NPR"
}
```

---

### Cash Flow Report

**GET** `/reports/financial/cashflow`

**Permissions**: OWNER only

**Query Parameters**:

- `start_date` (date, required)
- `end_date` (date, required)

**Response** (200 OK):

```json
{
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "inflows": {
    "from_operations": 180000.0,
    "security_deposits": 30000.0,
    "total_inflows": 210000.0
  },
  "outflows": {
    "operating_expenses": 45000.0,
    "administrative": 5000.0,
    "total_outflows": 50000.0
  },
  "net_cash_flow": 160000.0,
  "currency": "NPR"
}
```

---

### Schedule Report

**POST** `/reports/schedule`

**Permissions**: OWNER only

**Request Body**:

```json
{
  "report_type": "TAX_INCOME",
  "frequency": "ANNUAL",
  "email_to": "owner@example.com",
  "parameters": {
    "year": 2025
  }
}
```

**Response** (201 Created):

```json
{
  "schedule_id": "uuid",
  "report_type": "TAX_INCOME",
  "frequency": "ANNUAL",
  "next_generation_date": "2026-01-01",
  "is_active": true
}
```

---

### Create Share Link for Report

**POST** `/reports/{report_id}/share`

**Permissions**: OWNER (report creator)

**Request Body**:

```json
{
  "expires_in_days": 7
}
```

**Response** (200 OK):

```json
{
  "report_id": "uuid",
  "share_token": "a3f7c8d9e2b1f5g4h6j8k9m0n1p2q3r4",
  "share_url": "https://api.meroghar.com/api/v1/reports/shared/a3f7c8d9e2b1f5g4h6j8k9m0n1p2q3r4",
  "expires_at": "2025-02-05T00:00:00Z"
}
```

---

### Access Shared Report (No Auth Required)

**GET** `/reports/shared/{token}`

**Permissions**: None (public with valid token)

**Response** (200 OK):

```json
{
  "report_id": "uuid",
  "report_type": "TAX_INCOME",
  "generated_at": "2025-01-29T10:00:00Z",
  "data": {
    "year": 2025,
    "total_rental_income": 180000.0
  }
}
```

**Errors**:

- `404 Not Found`: Invalid or expired token
- `410 Gone`: Report deleted

---

### Revoke Share Link

**DELETE** `/reports/{report_id}/share`

**Permissions**: OWNER (report creator)

**Response** (204 No Content)

---

## Analytics

### Rent Collection Trends

**GET** `/analytics/rent-trends`

**Permissions**: OWNER only

**Query Parameters**:

- `start_date` (date, optional, default: 12 months ago)
- `end_date` (date, optional, default: today)
- `property_id` (uuid, optional)

**Response** (200 OK):

```json
{
  "period_start": "2024-01-01",
  "period_end": "2025-01-31",
  "data_points": [
    {
      "month": "2024-01",
      "total_collected": 150000.0,
      "total_due": 180000.0,
      "collection_rate": 0.833
    },
    {
      "month": "2024-02",
      "total_collected": 180000.0,
      "total_due": 180000.0,
      "collection_rate": 1.0
    }
  ]
}
```

---

### Payment Status Overview

**GET** `/analytics/payment-status`

**Permissions**: OWNER only

**Query Parameters**:

- `property_id` (uuid, optional)

**Response** (200 OK):

```json
{
  "current_month": "2025-01",
  "total_tenants": 10,
  "paid": 7,
  "overdue": 2,
  "pending": 1,
  "collection_rate": 0.7,
  "total_collected": 105000.0,
  "total_expected": 150000.0
}
```

---

### Expense Breakdown

**GET** `/analytics/expense-breakdown`

**Permissions**: OWNER only

**Query Parameters**:

- `start_date` (date, required)
- `end_date` (date, required)
- `property_id` (uuid, optional)

**Response** (200 OK):

```json
{
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "total_expenses": 45000.0,
  "by_category": [
    {
      "category": "MAINTENANCE",
      "amount": 20000.0,
      "percentage": 0.444
    },
    {
      "category": "REPAIRS",
      "amount": 15000.0,
      "percentage": 0.333
    }
  ]
}
```

---

### Revenue vs Expenses

**GET** `/analytics/revenue-expenses`

**Permissions**: OWNER only

**Query Parameters**:

- `start_date` (date, required)
- `end_date` (date, required)
- `property_id` (uuid, optional)

**Response** (200 OK):

```json
{
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "data_points": [
    {
      "month": "2025-01",
      "revenue": 180000.0,
      "expenses": 45000.0,
      "net_income": 135000.0
    }
  ],
  "totals": {
    "total_revenue": 180000.0,
    "total_expenses": 45000.0,
    "net_income": 135000.0,
    "profit_margin": 0.75
  }
}
```

---

### Property Performance

**GET** `/analytics/property-performance`

**Permissions**: OWNER only

**Response** (200 OK):

```json
{
  "properties": [
    {
      "property_id": "uuid",
      "property_name": "Green Valley Apartments",
      "total_units": 10,
      "occupied_units": 7,
      "occupancy_rate": 0.7,
      "monthly_revenue": 105000.0,
      "monthly_expenses": 30000.0,
      "net_income": 75000.0,
      "collection_rate": 0.85
    }
  ]
}
```

---

### Export Analytics Data

**POST** `/analytics/export`

**Permissions**: OWNER only

**Request Body**:

```json
{
  "report_type": "RENT_TRENDS",
  "start_date": "2024-01-01",
  "end_date": "2025-01-31",
  "format": "EXCEL"
}
```

**Response** (200 OK):

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

Binary Excel file download

---

## Sync

### Bulk Sync

**POST** `/sync`

**Permissions**: All authenticated users

**Request Body**:

```json
{
  "device_id": "DEVICE-UUID",
  "operations": [
    {
      "operation_type": "CREATE",
      "entity_type": "PAYMENT",
      "entity_id": "local-uuid-1",
      "timestamp": "2025-01-05T14:30:00Z",
      "data": {
        "tenant_id": "uuid",
        "amount": 15000.0,
        "payment_method": "CASH"
      }
    },
    {
      "operation_type": "UPDATE",
      "entity_type": "TENANT",
      "entity_id": "uuid",
      "timestamp": "2025-01-05T14:35:00Z",
      "data": {
        "phone": "+977-9841234567"
      }
    }
  ]
}
```

**Response** (200 OK):

```json
{
  "sync_id": "uuid",
  "processed": 2,
  "succeeded": 2,
  "failed": 0,
  "conflicts": 0,
  "results": [
    {
      "local_id": "local-uuid-1",
      "server_id": "uuid",
      "status": "SUCCESS"
    }
  ]
}
```

---

### Sync Status

**GET** `/sync/status`

**Permissions**: All authenticated users

**Query Parameters**:

- `device_id` (string, required)

**Response** (200 OK):

```json
{
  "device_id": "DEVICE-UUID",
  "last_sync": "2025-01-05T14:30:00Z",
  "pending_operations": 0,
  "sync_status": "UP_TO_DATE"
}
```

---

### Get Conflicts

**GET** `/sync/conflicts`

**Permissions**: All authenticated users

**Query Parameters**:

- `device_id` (string, required)

**Response** (200 OK):

```json
{
  "conflicts": [
    {
      "conflict_id": "uuid",
      "entity_type": "TENANT",
      "entity_id": "uuid",
      "local_version": {
        "phone": "+977-9841234567",
        "updated_at": "2025-01-05T14:30:00Z"
      },
      "server_version": {
        "phone": "+977-9801234567",
        "updated_at": "2025-01-05T14:35:00Z"
      }
    }
  ]
}
```

---

## Webhooks

### Khalti Payment Webhook

**POST** `/webhooks/khalti`

**Authentication**: Khalti signature verification

**Request Body**:

```json
{
  "idx": "KHALTI-TXN-123",
  "amount": 1500000,
  "mobile": "9841234567",
  "product_identity": "payment-uuid",
  "product_name": "Rent Payment",
  "status": "Completed"
}
```

**Response** (200 OK):

```json
{
  "status": "SUCCESS",
  "payment_id": "uuid"
}
```

---

### eSewa Payment Webhook

**POST** `/webhooks/esewa`

**Authentication**: eSewa signature verification

**Request Body**:

```json
{
  "transaction_code": "ESEWA-123",
  "status": "Success",
  "total_amount": "15000",
  "transaction_uuid": "payment-uuid",
  "product_code": "RENT",
  "signed_field_names": "...",
  "signature": "..."
}
```

**Response** (200 OK):

```json
{
  "status": "SUCCESS",
  "payment_id": "uuid"
}
```

---

### IME Pay Webhook

**POST** `/webhooks/imepay`

**Authentication**: IME Pay signature verification

**Request Body**:

```json
{
  "TransactionId": "IMEPAY-123",
  "RefId": "payment-uuid",
  "Amount": "15000",
  "ResponseCode": "0",
  "ResponseDescription": "Success"
}
```

**Response** (200 OK):

```json
{
  "status": "SUCCESS",
  "payment_id": "uuid"
}
```

---

## Error Handling

All API errors follow a consistent format:

**Error Response Structure**:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "req-uuid",
    "timestamp": "2025-01-05T14:30:00Z"
  }
}
```

### HTTP Status Codes

- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **204 No Content**: Successful request with no response body
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: User lacks permission for this action
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate email)
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### Common Error Codes

- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: Invalid or expired token
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `PAYMENT_GATEWAY_ERROR`: Payment gateway failure
- `SYNC_CONFLICT`: Data synchronization conflict

---

## Rate Limiting

API requests are rate-limited to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute per IP
- **General endpoints**: 100 requests per minute per user
- **Payment endpoints**: 20 requests per minute per user
- **Webhook endpoints**: No rate limiting (verified by signature)

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

When rate limit is exceeded:

**Response** (429 Too Many Requests):

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after": 60
  }
}
```

---

## Pagination

List endpoints support pagination using query parameters:

**Query Parameters**:

- `page` (integer, default: 1) - Page number
- `page_size` (integer, default: 20, max: 100) - Items per page

**Response Structure**:

```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "has_next": true,
  "has_previous": false,
  "items": [...]
}
```

---

## Filtering and Sorting

List endpoints support filtering and sorting:

**Query Parameters**:

- `sort_by` (string) - Field to sort by
- `order` (string: asc, desc) - Sort direction

**Example**:

```http
GET /api/v1/payments?start_date=2025-01-01&end_date=2025-01-31&sort_by=payment_date&order=desc
```

---

## Webhooks Security

All webhook endpoints verify request authenticity using:

1. **Signature Verification**: HMAC-SHA256 signature verification
2. **IP Whitelisting**: Only accept requests from gateway IPs
3. **Replay Protection**: Timestamp validation to prevent replay attacks

---

## API Versioning

The API uses URL versioning:

- Current version: `/api/v1`
- Future versions: `/api/v2`, `/api/v3`, etc.

Version deprecation policy:

- Minimum 6 months notice before deprecation
- 12 months support after new version release

---

## Support

For API support:

- Email: api-support@meroghar.com
- Documentation: https://docs.meroghar.com
- Status Page: https://status.meroghar.com

---

**Last Updated**: January 29, 2025
**API Version**: 1.0.0
