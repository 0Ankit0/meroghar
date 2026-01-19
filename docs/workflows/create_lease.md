# Workflow: Create Lease

**Description**: Formalizing a rental agreement between a Tenant and a Unit.

## Endpoint
`POST /leases/add/`

## Access
- **Roles**: Admin, Property Manager
- **Authentication**: Required

## Parameters (Form Data)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tenant` | UUID | Yes | Select existing Tenant |
| `unit` | UUID | Yes | Select existing Property Unit |
| `start_date` | Date | Yes | Lease start date (YYYY-MM-DD) |
| `end_date` | Date | Yes | Lease end date (YYYY-MM-DD) |
| `rent_amount` | Decimal | Yes | Monthly rent amount |
| `deposit_amount` | Decimal | Yes | Security deposit amount |

## Return Type
- **Success**: Redirect to Lease List (`HTTP 302` -> `/leases/`)
- **Error**: HTML Form with validation errors.

## Logic
1.  System validates that `end_date` is after `start_date`.
2.  System checks if the selected `Unit` is available (not occupied).
3.  System creates the `Lease` record with `Active` or `Pending` status.
4.  Updates the `Unit` status to 'Occupied'.
