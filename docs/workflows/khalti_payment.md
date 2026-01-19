# Workflow: Khalti Payment

**Description**: End-to-end flow for paying an Invoice using the Khalti ePayment Gateway (v2).

## Part 1: Initiation

**Endpoint**: `POST /payments/initiate/<invoice_id>/`

**Parameters**:
- `invoice_id` (Path Parameter): UUID of the invoice being paid.

**Logic**:
1.  Tenant clicks "Pay with Khalti" on Invoice Detail page.
2.  System retrieves Invoice and calculates remaining balance.
3.  System creates `Payment` record with status `INITIATED`.
4.  System calls Khalti API `/epayment/initiate/` with:
    - `return_url`: `.../payments/verify/`
    - `amount`: Amount in paisa
    - `purchase_order_id`: Payment UUID
5.  Khalti returns `payment_url`.
6.  System redirects User to `payment_url`.

**Return Type**: `HTTP 302` Redirect to Khalti.

---

## Part 2: Verification

**Endpoint**: `GET /payments/verify/`

**Parameters (Query Params from Khalti)**:
- `pidx`: Unique payment ID from Khalti.
- `status`: Payment status (e.g., "Completed").
- `purchase_order_id`: Our Payment UUID.

**Logic**:
1.  Khalti redirects user back to this endpoint after transaction.
2.  System finds local `Payment` record by `pidx` (or lookup ID).
3.  System calls Khalti API `/epayment/lookup/` with `pidx` to verify server-to-server.
4.  If status is `Completed`:
    - Update `Payment` status to `SUCCESS`.
    - Update `Invoice` paid amount.
    - If Invoice is fully paid, update `Invoice` status to `PAID`.
5.  Redirect user to Invoice Detail page with Success message.

**Return Type**: `HTTP 302` Redirect to Invoice Detail.
