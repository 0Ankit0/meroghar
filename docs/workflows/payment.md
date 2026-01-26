# Payment Workflows

Workflows related to the `Payment` model.

## 1. Khalti Payment

**Description**: End-to-end flow for paying an Invoice using the Khalti ePayment Gateway (v2).

### Part 1: Initiation

**Endpoint**: `POST /payments/initiate/<invoice_id>/`

1.  Tenant clicks "Pay with Khalti".
2.  System creates `Payment` (INITIATED).
3.  Calls Khalti Initiate API.
4.  Redirects to `payment_url`.

#### Initiation Diagram

```mermaid
sequenceDiagram
    actor User as Tenant
    participant System as MeroGhar System
    participant Khalti as Khalti Gateway

    User->>System: POST /payments/initiate/ (Invoice ID)
    System->>System: Calculate Amount (Total - Paid)
    System->>System: Create Payment (Status: INITIATED)
    
    System->>Khalti: POST /epayment/initiate/
    Khalti-->>System: { "pidx": "...", "payment_url": "..." }
    
    System->>System: Save pidx
    System-->>User: Redirect to payment_url
```

### Part 2: Verification

**Endpoint**: `GET /payments/verify/`

1.  Khalti redirects back with `pidx`.
2.  System calls Khalti Lookup API.
3.  Updates Payment to SUCCESS and Invoice to PAID.

#### Verification Diagram

```mermaid
sequenceDiagram
    actor User as Tenant
    participant System as MeroGhar System
    participant Khalti as Khalti Gateway
    participant DB as Database

    Khalti->>System: GET /payments/verify/ (pidx, status)
    System->>DB: Find Payment by pidx
    
    System->>Khalti: POST /epayment/lookup/ (pidx)
    Khalti-->>System: { "status": "Completed", ... }
    
    alt Payment Verified
        System->>DB: Update Payment (SUCCESS)
        System->>DB: Update Invoice (Paid Amount, Status)
        DB-->>System: Records Updated
        System-->>User: Redirect to Invoice Detail
    else Verification Failed
        System->>DB: Update Payment (FAILED)
        System-->>User: Show Error Message
    end
```
