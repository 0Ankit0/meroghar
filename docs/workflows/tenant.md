# Tenant Workflows

Workflows related to the `Tenant` model.

## 1. List Tenants

**Description**: View all tenants in the active organization.

### Endpoint
`GET /housing/tenants/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: GET /housing/tenants/
    System->>DB: SELECT * FROM tenants WHERE organization = active_org
    DB-->>System: [Tenant A, Tenant B]
    System-->>Manager: Render List
```

## 2. Register Tenant

**Description**: Onboarding a new tenant.

### Endpoint
`POST /housing/tenants/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /housing/tenants/add/ (Details)
    System->>DB: Check Email Uniqueness (Organization Scope)
    
    alt Email Unique
        System->>DB: INSERT Tenant Record
        DB-->>System: Tenant Created
        System-->>Manager: Redirect to Tenant List
    else Duplicate
        System-->>Manager: Show Error
    end
```

## 3. Update Tenant

**Description**: Updating contact or personal info.

### Endpoint
`POST /housing/tenants/<id>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /housing/tenants/<id>/edit/
    System->>DB: UPDATE Tenant
    DB-->>System: Updated
    System-->>Manager: Redirect
```

## 4. View Tenant Details

**Description**: Viewing full profile, leases, and payment history.

### Endpoint
`GET /housing/tenants/<id>/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: GET /housing/tenants/<id>/
    System->>DB: Fetch Tenant
    System->>DB: Fetch Related Leases
    System->>DB: Fetch Related Payments
    DB-->>System: Aggregated Data
    System-->>Manager: Render Dashboard-like View
```
