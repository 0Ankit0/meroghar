# System Edge Cases & Solutions

This document outlines potential edge cases in the MeroGhar system and the strategies to handle them.

## 1. Housing & Leasing

### 1.1. Lease Date Overlaps
*   **Scenario**: A property manager tries to create a new lease for a unit that starts before the current tenant's lease ends.
*   **Impact**: Two valid leases for the same unit at the same time; data integrity issues.
*   **Solution**:
    *   **Validation**: Enforce a DB-level constraint or strict application-level validation checking that `new_start_date > existing_end_date` for all active leases on the unit.
    *   **UI**: Show a clear error message "Unit is occupied until [Date]".

### 1.2. Holdover Tenants
*   **Scenario**: A tenant stays in the unit after their lease expires without renewing.
*   **Impact**: The system marks the unit as "Vacant" (based on lease end), but it is physically occupied.
*   **Solution**:
    *   **Grace Period**: Allow a "Holdover" status for expired leases.
    *   **Manual Trigger**: Do not auto-vacate units; require a "Move-out Inspection" or manual action to change Status to VACANT.

### 1.3. Unit Swaps
*   **Scenario**: A tenant moves from Unit A to Unit B mid-lease due to maintenance issues.
*   **Impact**: Billing confusion (different rents), lease history fragmentation.
*   **Solution**:
    *   **Terminate & Re-lease**: Terminate Lease A early (no penalty) and create Lease B.
    *   **Transfer Feature**: Create a specific "Transfer" workflow that carries over security deposits and generates a prorated invoice for the transition month.

## 2. Finance & Payments

### 2.1. Payment Race Conditions
*   **Scenario**: A tenant clicks "Pay" twice rapidly, or a webhook from Khalti arrives simultaneously with a user refresh.
*   **Impact**: Double payment recorded, or invoice marked "Paid" with excess balance.
*   **Solution**:
    *   **Idempotency**: Use `transaction_id` from the gateway as a unique constraint.
    *   **Locking**: Use database row locking (`select_for_update`) when processing payment callbacks to ensure sequential processing.

### 2.2. Prorated Rent Calculations
*   **Scenario**: A tenant moves in on Feb 14th. How much is the first month's rent?
*   **Impact**: Inaccurate billing; disputes.
*   **Solution**:
    *   **Daily Rate**: Calculate `(Monthly Rent / Days in Month) * Remaining Days`.
    *   **Leap Year**: Ensure date libraries correctly handle Feb 29.

### 2.3. Payment Reversals & Chargebacks
*   **Scenario**: A payment is marked SUCCESS, but the bank reverses it later (fraud/dispute).
*   **Impact**: Financial discrepancy; tenant credited for unpaid money.
*   **Solution**:
    *   **Reversal Workflow**: Allow admin to change Payment Status to `REFUNDED` or `FAILED` which automatically re-opens the Invoice (Status changes back to `SENT` or `OVERDUE`) and adjusts the balance.

## 3. IAM & Multi-tenancy

### 3.1. Cross-Organization Data Leakage
*   **Scenario**: A user manually changes the URL ID to access another organization's resource (`/org/1/` to `/org/2/`).
*   **Impact**: Severe security breach.
*   **Solution**:
    *   **Middleware**: Strict checking of `request.user` membership in `view.kwargs['org_id']`.
    *   **Query Filtering**: Every queryset must filter by `organization=request.active_organization`. Do not rely solely on URL routing.

### 3.2. User Organization Switching
*   **Scenario**: A user has two tabs open for two different organizations. They perform an action in Tab A thinking it's Org A, but their session was switched to Org B in Tab B.
*   **Impact**: Data created in wrong organization.
*   **Solution**:
    *   **URL-based Context**: Do not rely solely on session `active_org_id`. Include `org_id` in the URL scope for all admin actions alongside session validation.

## 4. Operations

### 4.1. Concurrent Work Order Updates
*   **Scenario**: A tenant updates a work order description while a property manager is changing the status.
*   **Impact**: Last write wins; information loss.
*   **Solution**:
    *   **Optimistic Locking**: Use a version number field on the model. If the version in DB is higher than the version the user started editing, reject the save and ask to refresh.
