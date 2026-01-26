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
