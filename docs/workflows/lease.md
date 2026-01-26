# Lease Workflows

Workflows related to the `Lease` model.

## 1. List Leases

**Description**: View all active and past leases.

### Endpoint
`GET /leases/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: GET /leases/
    System->>DB: SELECT * FROM leases WHERE organization = active_org
    DB-->>System: Lease List
    System-->>Manager: Render List
```

## 2. Create Lease

**Description**: Formalizing a rental agreement.

### Endpoint
`POST /leases/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /leases/add/ (Tenant, Unit, Dates)
    System->>System: Validate Dates
    System->>DB: Check Unit Availability
    
    alt Available
        System->>DB: INSERT Lease
        System->>DB: UPDATE Unit Status (Occupied)
        DB-->>System: Success
        System-->>Manager: Redirect
    else Occupied
        System-->>Manager: Error
    end
```

## 3. Update Lease

**Description**: Extending dates or changing rent.

### Endpoint
`POST /leases/<id>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /leases/<id>/edit/
    System->>DB: UPDATE Lease
    DB-->>System: Success
    System-->>Manager: Redirect
```

## 4. Terminate/Delete Lease

**Description**: Ending a lease early or deleting record.

### Endpoint
`POST /leases/<id>/delete/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /leases/<id>/delete/
    System->>DB: DELETE Lease
    System->>DB: UPDATE Unit Status (Vacant)
    DB-->>System: Success
    System-->>Manager: Redirect
```
