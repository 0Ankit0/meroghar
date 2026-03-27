# Invoice Workflows

Workflows related to the `Invoice` model.

## 1. List Invoices

**Description**: Accessing billing history.

### Endpoint
`GET /finance/invoices/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: GET /finance/invoices/
    System->>DB: Fetch Invoices (Active Org)
    DB-->>System: List
    System-->>Manager: Render Table
```

## 2. Generate Invoice

**Description**: Creating a new invoice.

### Endpoint
`POST /finance/invoices/add/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /finance/invoices/add/
    System->>DB: Verify Lease
    System->>DB: INSERT Invoice
    DB-->>System: Created
    System-->>Manager: Redirect
```

## 3. Update Invoice

**Description**: Correcting an invoice.

### Endpoint
`POST /finance/invoices/<uuid:pk>/edit/`

### System Diagram

```mermaid
sequenceDiagram
    actor Manager as Property Manager
    participant System as MeroGhar System
    participant DB as Database

    Manager->>System: POST /finance/invoices/<uuid:pk>/edit/
    System->>DB: UPDATE Invoice
    DB-->>System: Success
    System-->>Manager: Redirect
```
