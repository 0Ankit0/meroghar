# API Design

## Overview
REST API design for MeroGhar. All endpoints are versioned under `/api/v1`. Authentication is via Bearer JWT tokens. Landlord, Tenant, Staff, and Admin roles have different permission scopes.

---

## Authentication Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Public | Register a new user (landlord, tenant, or staff) |
| POST | `/auth/login` | Public | Login and receive JWT access + refresh tokens |
| POST | `/auth/refresh` | Public | Refresh access token using refresh token |
| POST | `/auth/logout` | Authenticated | Revoke current session |
| POST | `/auth/verify-otp` | Public | Verify OTP for email/phone |
| POST | `/auth/forgot-password` | Public | Send password reset link |
| POST | `/auth/reset-password` | Public | Reset password using token |

---

## Property Type Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/categories` | Public | List all active property categories |
| GET | `/categories/{categoryId}` | Public | Get category details and attributes |
| POST | `/categories` | Admin | Create a new property type |
| PUT | `/categories/{categoryId}` | Admin | Update a category |
| POST | `/categories/{categoryId}/attributes` | Admin | Add a custom attribute to a category |

---

## Property Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/assets` | Public | Search and list published assets (with filters) |
| GET | `/properties/{propertyId}` | Public | Get full property details, photos, attributes, and pricing |
| POST | `/assets` | Landlord | Create a new property (draft) |
| PUT | `/properties/{propertyId}` | Landlord | Update property details |
| DELETE | `/properties/{propertyId}` | Landlord | Archive an property |
| POST | `/properties/{propertyId}/publish` | Landlord | Publish the property listing |
| POST | `/properties/{propertyId}/unpublish` | Landlord | Unpublish the property listing |
| POST | `/properties/{propertyId}/photos` | Landlord | Upload property photos |
| DELETE | `/properties/{propertyId}/photos/{photoId}` | Landlord | Delete a photo |
| GET | `/properties/{propertyId}/availability` | Public | Get availability calendar for a date range |
| GET | `/properties/{propertyId}/price` | Public | Get pricing breakdown for a given period |

### GET /assets — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category slug |
| `start` | ISO datetime | Rental start time |
| `end` | ISO datetime | Rental end time |
| `location` | string | Location search (city or coordinates) |
| `radius_km` | number | Search radius from location |
| `min_price` | number | Minimum daily rate |
| `max_price` | number | Maximum daily rate |
| `page` | number | Page number |
| `per_page` | number | Results per page (max 50) |

---

## Pricing Rule Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/properties/{propertyId}/pricing-rules` | Landlord | List pricing rules for an property |
| POST | `/properties/{propertyId}/pricing-rules` | Landlord | Create a pricing rule |
| PUT | `/properties/{propertyId}/pricing-rules/{ruleId}` | Landlord | Update a pricing rule |
| DELETE | `/properties/{propertyId}/pricing-rules/{ruleId}` | Landlord | Remove a pricing rule |

---

## Rental Application Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings` | Landlord / Tenant | List bookings (scoped by role) |
| GET | `/bookings/{bookingId}` | Landlord / Tenant | Get rental application details |
| POST | `/bookings` | Tenant | Submit a new rental application request |
| POST | `/bookings/{bookingId}/confirm` | Landlord | Confirm a pending rental application |
| POST | `/bookings/{bookingId}/decline` | Landlord | Decline a pending rental application |
| PUT | `/bookings/{bookingId}` | Tenant / Landlord | Request rental application modification |
| POST | `/bookings/{bookingId}/cancel` | Tenant / Landlord | Cancel a rental application |
| POST | `/bookings/{bookingId}/return` | Tenant | Initiate property return |
| GET | `/bookings/{bookingId}/events` | Landlord / Tenant | Get rental application event timeline |

### POST /bookings — Request Body

```json
{
  "propertyId": "uuid",
  "rentalStartAt": "2025-06-15T10:00:00Z",
  "rentalEndAt": "2025-06-18T10:00:00Z",
  "specialRequests": "Please include a properties seat",
  "paymentMethodId": "pm_stripe_xxx"
}
```

### POST /bookings — Response (201)

```json
{
  "bookingId": "uuid",
  "bookingNumber": "BKG-2025-00123",
  "status": "PENDING",
  "property": { "id": "uuid", "name": "Toyota Camry 2023" },
  "rentalStartAt": "2025-06-15T10:00:00Z",
  "rentalEndAt": "2025-06-18T10:00:00Z",
  "pricing": {
    "baseFee": 180.00,
    "peakSurcharge": 20.00,
    "taxAmount": 20.00,
    "totalFee": 220.00,
    "depositAmount": 500.00
  }
}
```

---

## Lease Agreement Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings/{bookingId}/agreement` | Landlord / Tenant | Get the lease agreement for a rental application |
| POST | `/bookings/{bookingId}/agreement` | Landlord | Generate an agreement from a template |
| POST | `/bookings/{bookingId}/agreement/send` | Landlord | Send agreement to tenant for signature |
| POST | `/bookings/{bookingId}/agreement/countersign` | Landlord | Landlord countersigns the agreement |
| POST | `/webhooks/esign` | Internal | E-signature provider webhook receiver |

---

## Invoice & Payment Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/invoices` | Landlord / Tenant | List invoices (scoped by role) |
| GET | `/invoices/{invoiceId}` | Landlord / Tenant | Get invoice details with line items |
| POST | `/invoices/{invoiceId}/pay` | Tenant | Pay an invoice |
| GET | `/invoices/{invoiceId}/receipt` | Tenant | Download payment receipt |
| POST | `/bookings/{bookingId}/additional-charges` | Landlord | Add a post-rental additional charge |
| POST | `/additional-charges/{chargeId}/dispute` | Tenant | Dispute an additional charge |
| GET | `/payouts` | Landlord | List landlord payouts |
| GET | `/payouts/{payoutId}` | Landlord | Get payout details |
| POST | `/webhooks/payment` | Internal | Payment gateway webhook receiver |

---

## Property Inspection Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/bookings/{bookingId}/assessments` | Landlord / Tenant / Staff | List assessments for a rental application |
| GET | `/assessments/{assessmentId}` | Landlord / Tenant / Staff | Get assessment details |
| POST | `/assessments` | Staff | Create an assessment for a rental application |
| POST | `/assessments/{assessmentId}/items` | Staff | Submit checklist items |
| POST | `/assessments/{assessmentId}/photos` | Staff | Upload assessment photos |
| POST | `/assessments/{assessmentId}/submit` | Staff | Submit the completed assessment |
| POST | `/assessments/{assessmentId}/countersign` | Tenant | Tenant countersigns pre-rental assessment |
| GET | `/assessments/{assessmentId}/report` | Landlord / Tenant | Download assessment PDF report |
| GET | `/bookings/{bookingId}/assessments/comparison` | Landlord | Get pre vs post rental comparison |

---

## Maintenance Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/maintenance-requests` | Landlord / Staff | List maintenance requests |
| GET | `/maintenance-requests/{requestId}` | Landlord / Staff | Get request details |
| POST | `/maintenance-requests` | Landlord | Log a new maintenance request |
| PUT | `/maintenance-requests/{requestId}/assign` | Landlord | Assign to a staff member |
| PUT | `/maintenance-requests/{requestId}/status` | Staff | Update task status |
| POST | `/maintenance-requests/{requestId}/complete` | Staff | Submit completion with notes and photos |
| POST | `/maintenance-requests/{requestId}/approve` | Landlord | Approve completed maintenance |
| POST | `/maintenance-requests/{requestId}/reopen` | Landlord | Reopen the request |
| POST | `/maintenance-requests/{requestId}/cost` | Landlord | Log maintenance cost |
| GET | `/properties/{propertyId}/preventive-services` | Landlord | List preventive service tasks |
| POST | `/properties/{propertyId}/preventive-services` | Landlord | Schedule a preventive service task |

---

## Reporting Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/reports/dashboard` | Landlord / Admin | Financial dashboard summary |
| POST | `/reports/revenue` | Landlord | Generate revenue report |
| POST | `/reports/utilisation` | Landlord | Generate property utilisation report |
| POST | `/reports/tax-summary` | Landlord | Generate tax summary report |
| GET | `/reports/{reportId}/download` | Landlord | Download generated report file |

---

## Standard Response Envelope

```json
{
  "success": true,
  "data": { },
  "meta": {
    "page": 1,
    "perPage": 20,
    "total": 150
  }
}
```

## Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "BOOKING_UNAVAILABLE",
    "message": "The property is not available for the selected dates.",
    "details": null
  },
  "requestId": "req_abc123"
}
```

## Common Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Insufficient role permissions |
| `NOT_FOUND` | 404 | Resource does not exist |
| `VALIDATION_ERROR` | 422 | Request body fails schema validation |
| `BOOKING_UNAVAILABLE` | 409 | Property unavailable for requested dates |
| `PAYMENT_FAILED` | 402 | Payment gateway rejected the transaction |
| `DEPOSIT_REQUIRED` | 402 | Deposit payment must be completed first |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
