# Workflow: Register Tenant

**Description**: Onboarding a new tenant into the system.

## Endpoint
`POST /tenants/add/`

## Access
- **Roles**: Admin, Property Manager
- **Authentication**: Required

## Parameters (Form Data)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `first_name` | String | Yes | Tenant's first name |
| `last_name` | String | Yes | Tenant's last name |
| `email` | Email | Yes | Valid email address for notifications |
| `phone` | String | Yes | Mobile contact number |
| `id_number` | String | No | Citizenship or License ID |
| `emergency_contact_name` | String | No | Name of emergency contact |
| `emergency_contact_phone` | String | No | Phone of emergency contact |

## Return Type
- **Success**: Redirect to Tenant List (`HTTP 302` -> `/tenants/`)
- **Error**: HTML Form with validation errors.

## Logic
1.  Manager fills tenant contact details.
2.  System checks for unique email constraints within the Organization.
3.  System creates a `Tenant` profile.
4.  (Future) System may invite the User to create a login account.
