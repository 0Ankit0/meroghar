# Billing & Payments

## Overview

The financial module handles invoicing and online rent collection.

## Data Models

### Invoice
Represents a bill sent to a tenant.
- **Reference**: Unique Invoice Number.
- **Status**: PAID, UNPAID, OVERDUE, PARTIALLY_PAID.
- **Relations**: Linked to `Lease` and `Tenant`.

### Payment
Represents a transaction attempting to settle an Invoice.
- **Provider**: Currently supports `KHALTI`.
- **Status**: INITIATED, SUCCESS, FAILED.
- **Transaction ID**: `pidx` from Khalti.

## Khalti Integration Flow

We use the **Khalti ePayment API (v2)**.

1. **Initiate**:
   - User clicks "Pay with Khalti".
   - System calls `https://a.khalti.com/api/v2/epayment/initiate/`.
   - Returns a `payment_url` and `pidx`.
   - User is redirected to `payment_url`.

2. **Verify**:
   - User completes payment on Khalti.
   - Khalti redirects user back to our `return_url`.
   - System receives `pidx` on callback.
   - System calls `https://a.khalti.com/api/v2/epayment/lookup/` to verify status.
   - If `Completed`, Invoice is marked PAID.
