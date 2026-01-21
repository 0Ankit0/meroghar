# Use Case Diagram

## System Use Cases

```mermaid
graph TB
    subgraph "MeroGhar Rental System"
        UC1((Manage Properties))
        UC2((Search Properties))
        UC3((Book Property))
        UC4((Process Payments))
        UC5((Manage Bookings))
        UC6((View Analytics))
        UC7((Manage Users))
        UC8((Send Notifications))
        UC9((Submit Maintenance<br/>Request))
        UC10((Generate Reports))
        UC11((Moderate Content))
        UC12((Rate & Review))
    end
    
    Owner[Property Owner] --> UC1
    Owner --> UC5
    Owner --> UC6
    Owner --> UC9
    
    Tenant[Tenant] --> UC2
    Tenant --> UC3
    Tenant --> UC4
    Tenant --> UC12
    Tenant --> UC9
    
    Admin[Admin] --> UC7
    Admin --> UC10
    Admin --> UC11
    
    System[System] --> UC8
    
    UC3 --> UC4
    UC5 --> UC8
    UC1 --> UC8
```

## Actor Descriptions

### Property Owner
- **Role**: Lists and manages rental properties
- **Goals**: Maximize occupancy, manage tenants efficiently
- **Responsibilities**: Maintain property information, respond to bookings

### Tenant
- **Role**: Searches for and rents properties
- **Goals**: Find suitable accommodation, manage rental payments
- **Responsibilities**: Pay rent on time, maintain property

### Admin
- **Role**: System administrator
- **Goals**: Ensure platform integrity, support users
- **Responsibilities**: Moderate content, manage users, resolve disputes

### System
- **Role**: Automated system processes
- **Goals**: Execute scheduled tasks, send notifications
- **Responsibilities**: Send reminders, process automated payments
