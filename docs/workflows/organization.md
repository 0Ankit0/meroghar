# Organization Workflows

Workflows related to the `Organization` model.

## 1. List Organizations

**Description**: View all organizations the user is a member of.

### Endpoint
`GET /organizations/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as User
    participant System as MeroGhar System
    participant DB as Database

    User->>System: GET /organizations/
    System->>DB: SELECT * FROM organizations JOIN user_organizations ...
    DB-->>System: List of Orgs
    System-->>User: Render List
```

## 2. Switch Organization

**Description**: Change active context.

### Endpoint
`POST /organizations/switch/<org_id>/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as User
    participant System as MeroGhar System
    participant Session as Session

    User->>System: POST /organizations/switch/<id>/
    System->>Session: KEY active_org_id = <id>
    System-->>User: Redirect
```

## 3. Add Organization

**Description**: Create a new organization.

### Endpoint
`POST /organizations/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as User
    participant System as MeroGhar System
    participant DB as Database
    participant Session as Session

    User->>System: POST /organizations/add/
    System->>DB: INSERT Organization
    System->>DB: Link User (Member/Owner)
    System->>Session: Auto-switch (active_org_id = new_id)
    DB-->>System: Created
    System-->>User: Redirect
```

## 4. Edit Organization

**Description**: Update org details.

### Endpoint
`POST /organizations/<id>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Admin
    participant System as MeroGhar System
    participant DB as Database

    User->>System: POST /organizations/<id>/edit/
    System->>DB: UPDATE Organization
    DB-->>System: Updated
    System-->>User: Redirect
```
