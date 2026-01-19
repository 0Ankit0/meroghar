# Workflow: Add Property

**Description**: Usage of the system to register a new real estate property.

## Endpoint
`POST /properties/add/`

## Access
- **Roles**: Admin, Property Manager
- **Authentication**: Required

## Parameters (Form Data)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | String | Yes | Name of the property (e.g., "Sunrise Apartments") |
| `address` | String | Yes | Street address |
| `city` | String | Yes | City name |
| `state` | String | Yes | State/Province |
| `zip_code` | String | No | Postal code |

## Return Type
- **Success**: Redirect to Property List (`HTTP 302` -> `/properties/`)
- **Error**: HTML Form with validation errors.

## Logic
1.  User navigates to `/properties/add/`.
2.  System renders empty form.
3.  User submits form data.
4.  System validates mandatory fields and address format.
5.  System creates a new `Property` record linked to the logged-in user's Organization.
6.  System redirects to the list view.
