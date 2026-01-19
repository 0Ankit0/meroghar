# Workflow: Submit Work Order

**Description**: Reporting a maintenance issue for a specific unit.

## Endpoint
`POST /maintenance/requests/add/`

## Access
- **Roles**: Tenant, Admin, Property Manager
- **Authentication**: Required

## Parameters (Form Data)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | String | Yes | Short summary of the issue |
| `description` | String | Yes | Detailed description |
| `unit` | UUID | Yes | Affected Unit |
| `priority` | String | Yes | LOW, MEDIUM, HIGH, EMERGENCY |

## Return Type
- **Success**: Redirect to Work Order List (`HTTP 302` -> `/maintenance/requests/`)
- **Error**: HTML Form with validation errors.

## Logic
1.  User describes the maintenance issue.
2.  System tags the creator as the `requester`.
3.  System creates `WorkOrder` with status `OPEN`.
4.  Admin/Staff is notified (Future implementation).
