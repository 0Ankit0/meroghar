# Unit Workflows

Workflows related to the `Unit` model.

## 1. List Units

**Description**: View all units in the active organization.

### Endpoint
`GET /units/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    User->>System: GET /units/
    System->>DB: SELECT * FROM units JOIN properties ON ... WHERE properties.organization = active_org
    DB-->>System: [Unit 101, Unit 102]
    System-->>User: Render List
```

## 2. Add Unit

**Description**: Adding a unit to a property.

### Endpoint
`POST /units/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    User->>System: POST /units/add/ (Data)
    System->>DB: INSERT Unit
    DB-->>System: Unit Created
    System-->>User: Redirect to Unit List
```

## 3. Update Unit

**Description**: Edit unit details (rent, status, etc.).

### Endpoint
`POST /units/<id>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    User->>System: POST /units/<id>/edit/
    System->>DB: UPDATE Unit
    DB-->>System: Success
    System-->>User: Redirect to List
```

## 4. Delete Unit

**Description**: Remove a unit. Usually restricted if active lease exists.

### Endpoint
`POST /units/<id>/delete/`

### System Diagram

```mermaid
sequenceDiagram
    actor User as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    User->>System: POST /units/<id>/delete/
    System->>DB: DELETE Unit
    DB-->>System: Deleted
    System-->>User: Redirect to List
```
