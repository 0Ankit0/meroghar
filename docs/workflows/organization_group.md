# Organization Group Workflows

Workflows related to the `OrganizationGroup` model.

## 1. List Groups

**Description**: View all groups.

### Endpoint
`GET /iam/groups/`

### System Diagram

```mermaid
sequenceDiagram
    actor Admin as Admin
    participant System as MeroGhar System
    participant DB as Database

    Admin->>System: GET /iam/groups/
    System->>DB: SELECT * FROM groups WHERE organization IN user.active_orgs (conceptually)
    DB-->>System: Group List
    System-->>Admin: Render List
```

## 2. Manage/Add Group

**Description**: Create a group.

### Endpoint
`POST /iam/groups/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor Admin as Admin
    participant System as MeroGhar System
    participant DB as Database

    Admin->>System: POST /iam/groups/add/ (Name, Orgs, Users)
    System->>DB: INSERT OrganizationGroup
    System->>DB: Link M2M (Orgs, Users)
    DB-->>System: Success
    System-->>Admin: Redirect
```

## 3. Edit Group

**Description**: Modify members or permissions.

### Endpoint
`POST /iam/groups/<id>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor Admin as Admin
    participant System as MeroGhar System
    participant DB as Database

    Admin->>System: POST /iam/groups/<id>/edit/
    System->>DB: UPDATE OrganizationGroup
    System->>DB: Sync M2M Relations
    DB-->>System: Success
    System-->>Admin: Redirect
```

## 4. Delete Group

**Description**: Remove a group.

### Endpoint
`POST /iam/groups/<id>/delete/`

### System Diagram

```mermaid
sequenceDiagram
    actor Admin as Admin
    participant System as MeroGhar System
    participant DB as Database

    Admin->>System: POST /iam/groups/<id>/delete/
    System->>DB: DELETE OrganizationGroup
    DB-->>System: Deleted
    System-->>Admin: Redirect
```
