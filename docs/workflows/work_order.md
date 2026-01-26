# Work Order Workflows

Workflows related to the `WorkOrder` model.

## 1. List Work Orders

**Description**: View maintenance queue.

### Endpoint
`GET /maintenance/requests/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Tenant/Manager
    participant System as MeroGhar System
    participant DB as Database

    User->>System: GET /maintenance/requests/
    System->>DB: SELECT * FROM work_orders WHERE organization = active_org
    DB-->>System: List
    System-->>User: Render Queue
```

## 2. Submit Work Order

**Description**: Create new request.

### Endpoint
`POST /maintenance/requests/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Tenant/Manager
    participant System as MeroGhar System
    participant DB as Database

    User->>System: POST /maintenance/requests/add/
    System->>DB: INSERT WorkOrder
    DB-->>System: Created
    System-->>User: Redirect
```

## 3. Update Work Order

**Description**: Update status (e.g. In Progress, Completed).

### Endpoint
`POST /maintenance/requests/<id>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /maintenance/requests/<id>/edit/ (Status: Completed)
    System->>DB: UPDATE WorkOrder
    DB-->>System: Success
    System-->>Manager: Redirect
```
