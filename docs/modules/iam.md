# Identity and Access Management (IAM)

The **IAM** module handles user authentication, organization management (multi-tenancy), and access control via groups and permissions.

## Core Models

### 1. User
Custom user model extending `AbstractUser`.
- **Fields**: Standard Django auth fields.
- **Relationships**:
    - `organizations`: Many-to-Many relationship with `Organization`. A user can belong to multiple organizations.
    - `organization_groups`: Many-to-Many relationship with `OrganizationGroup`.

### 2. Organization
Represents a tenant or a property management entity.
- **Fields**: `name`, `slug`, `address`.
- **Usage**: Data in other modules (Housing, Finance, Operations) is scoped to an `Organization`.

### 3. OrganizationGroup
Represents a group of users with specific permissions, scoped to one or more organizations.
- **Fields**: `name`, `description`.
- **Relationships**:
    - `organizations`: The organizations where this group's permissions apply.
    - `members`: Users who belong to this group.
    - `permissions`: Django `Permission` objects granted to members.

## Feature: Organization Switching

MeroGhar supports a "GitHub-style" organization switcher, allowing users to be members of multiple organizations but act within the context of **one** active organization at a time.

### Middleware: `OrganizationMiddleware`
Located in `apps.core.middleware.py`.
- **Function**:
    1. Checks `request.session['active_org_id']`.
    2. Verifies the user is a member of that organization.
    3. Sets `request.active_organization`.
    4. If no active organization is set in session, defaults to the user's first organization.
- **Context**: All views should access `request.active_organization` instead of `request.user` for filtering data.

### View Logic
- **Filtering**: `get_queryset` methods filter by `organization=request.active_organization`.
- **Creation**: New objects (Tenants, Properties, etc.) are automatically assigned to `request.active_organization`.
- **Organization Management**: Users can create new organizations and switch between them via the Sidebar dropdown.

## Feature: Organization Groups

Admin users can manage Cross-Organization Groups.

- **Use Case**: A "Regional Manager" group can be created and assigned to "Organization A" and "Organization B". Any user in this group gets the assigned permissions for *both* organizations.
- **Management UI**: Located in `Groups` section in Sidebar (visible to Staff/Superusers).

## Mobile Token Auth & Organization Context API

Mobile clients can authenticate using DRF token auth and drive organization context explicitly without depending on server-rendered session UX.

### Authentication

Base prefix: `/api/iam/`

#### `POST /api/iam/auth/login/`
- **Request**
  ```json
  {
    "username": "api_user",
    "password": "password"
  }
  ```
- **Response 200**
  ```json
  {
    "token": "<drf_token>",
    "user": {
      "id": "<uuid>",
      "username": "api_user",
      "email": "",
      "first_name": "",
      "last_name": "",
      "role": "ADMIN",
      "memberships": [
        {
          "id": "<org_uuid>",
          "name": "Org A",
          "slug": "org-a",
          "is_active": true
        }
      ],
      "active_organization": {
        "id": "<org_uuid>",
        "name": "Org A",
        "slug": "org-a",
        "is_active": true
      }
    }
  }
  ```

#### `POST /api/iam/auth/refresh/`
- Rotates DRF token for the authenticated user.
- **Headers**: `Authorization: Token <drf_token>`
- **Response 200**
  ```json
  {
    "token": "<new_drf_token>"
  }
  ```

#### `POST /api/iam/auth/logout/`
- Revokes token for the authenticated user.
- **Headers**: `Authorization: Token <drf_token>`
- **Response**: `204 No Content`

#### `GET /api/iam/auth/profile/`
- Returns authenticated user profile, memberships, active org, and role.
- **Headers**: `Authorization: Token <drf_token>`

### Organization Membership / Context

#### `GET /api/iam/memberships/`
- Lists all organizations where user is a member.
- Each item includes `is_active` marker.

#### `POST /api/iam/switch-organization/`
- **Request**
  ```json
  {
    "organization_id": "<org_uuid>"
  }
  ```
- **Response 200**
  ```json
  {
    "active_organization": {
      "id": "<org_uuid>",
      "name": "Org A",
      "slug": "org-a",
      "is_active": true
    }
  }
  ```
- **Response 403** when the user is not a member of that organization.

### Organization Header Support

Authenticated API requests can send `X-Organization-ID: <org_uuid>`.

- If the user belongs to that organization, it becomes the active organization context.
- If the user does **not** belong to the provided org (or sends an invalid org ID), API requests return `403 Forbidden` with:
  ```json
  {
    "detail": "You are not a member of the organization provided in X-Organization-ID."
  }
  ```
- If no header is provided, session-based fallback remains enabled for web flows and session-auth API clients.

### Role behavior

User `role` is returned in profile/login payloads for mobile feature gating. Authorization rules remain endpoint-specific (e.g., user management endpoints require admin/staff permissions).
