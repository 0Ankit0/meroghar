# Data Flow Diagram

## Level 0 - Context Diagram

```mermaid
flowchart TB
    subgraph External
        Owner[Property Owner]
        Tenant[Tenant]
        Admin[Admin]
        PayGW[Payment Gateway]
    end
    
    subgraph "MeroGhar System"
        System[MeroGhar<br/>Rental Platform]
    end
    
    Owner -->|Property Data| System
    Tenant -->|Booking Requests| System
    Tenant -->|Payment Info| System
    Admin -->|Management Actions| System
    
    System -->|Property Listings| Tenant
    System -->|Booking Status| Owner
    System -->|Payment Requests| PayGW
    System -->|Reports| Admin
    
    PayGW -->|Payment Confirmations| System
    System -->|Notifications| Owner
    System -->|Confirmations| Tenant
```

## Level 1 - Major Processes

```mermaid
flowchart TB
    Owner[Property Owner]
    Tenant[Tenant]
    Admin[Admin]
    PayGW[Payment Gateway]
    
    subgraph "MeroGhar System"
        P1[1.0<br/>User<br/>Management]
        P2[2.0<br/>Property<br/>Management]
        P3[3.0<br/>Booking<br/>Management]
        P4[4.0<br/>Payment<br/>Processing]
        P5[5.0<br/>Notification<br/>Service]
        
        DB[(Central<br/>Database)]
        
        P1 <--> DB
        P2 <--> DB
        P3 <--> DB
        P4 <--> DB
        P5 <--> DB
    end
    
    Owner -->|Registration| P1
    Tenant -->|Registration| P1
    Owner -->|Property Info| P2
    Tenant -->|Search Criteria| P2
    P2 -->|Property Listings| Tenant
    
    Tenant -->|Booking Request| P3
    P3 -->|Booking Status| Owner
    P3 -->|Payment Invoice| P4
    
    P4 -->|Payment Request| PayGW
    PayGW -->|Payment Status| P4
    P4 -->|Receipt| Tenant
    
    P3 -->|Events| P5
    P5 -->|Notifications| Owner
    P5 -->|Notifications| Tenant
    
    Admin -->|Actions| P1
    Admin -->|Moderation| P2
```

## Level 2 - Detailed Property Management

```mermaid
flowchart TB
    Owner[Property Owner]
    Tenant[Tenant]
    
    subgraph "Property Management Process"
        P2_1[2.1<br/>Create/Update<br/>Property]
        P2_2[2.2<br/>Manage<br/>Photos]
        P2_3[2.3<br/>Set<br/>Pricing]
        P2_4[2.4<br/>Search &<br/>Filter]
        P2_5[2.5<br/>Property<br/>Review]
        
        D1[(Property<br/>Store)]
        D2[(Photo<br/>Store)]
        D3[(Pricing<br/>Store)]
        D4[(Review<br/>Store)]
    end
    
    Owner -->|Property Details| P2_1
    P2_1 -->|Store| D1
    
    Owner -->|Images| P2_2
    P2_2 -->|Store| D2
    
    Owner -->|Price Data| P2_3
    P2_3 -->|Store| D3
    
    Tenant -->|Search Query| P2_4
    P2_4 -->|Read| D1
    P2_4 -->|Read| D2
    P2_4 -->|Read| D3
    P2_4 -->|Results| Tenant
    
    Tenant -->|Review| P2_5
    P2_5 -->|Store| D4
    D1 -->|Property Data| P2_4
    D2 -->|Photos| P2_4
    D3 -->|Prices| P2_4
```

## Level 2 - Detailed Booking Management

```mermaid
flowchart TB
    Tenant[Tenant]
    Owner[Owner]
    
    subgraph "Booking Management Process"
        P3_1[3.1<br/>Check<br/>Availability]
        P3_2[3.2<br/>Create<br/>Booking]
        P3_3[3.3<br/>Review<br/>Booking]
        P3_4[3.4<br/>Update<br/>Status]
        P3_5[3.5<br/>Generate<br/>Contract]
        
        D1[(Booking<br/>Store)]
        D2[(Property<br/>Store)]
        D3[(Calendar<br/>Store)]
        D4[(Contract<br/>Store)]
    end
    
    Tenant -->|Dates| P3_1
    P3_1 -->|Check| D3
    D3 -->|Availability| P3_1
    P3_1 -->|Status| Tenant
    
    Tenant -->|Booking Details| P3_2
    P3_2 -->|Create| D1
    P3_2 -->|Update| D3
    
    D1 -->|Booking Info| P3_3
    Owner -->|Review| P3_3
    P3_3 -->|Decision| P3_4
    
    P3_4 -->|Update| D1
    P3_4 -->|Status| Owner
    P3_4 -->|Status| Tenant
    
    P3_4 -->|Approved Booking| P3_5
    P3_5 -->|Create| D4
    D2 -->|Property Details| P3_5
```

## Level 2 - Payment Processing Flow

```mermaid
flowchart TB
    Tenant[Tenant]
    PayGW[Payment Gateway]
    
    subgraph "Payment Processing"
        P4_1[4.1<br/>Calculate<br/>Amount]
        P4_2[4.2<br/>Initiate<br/>Payment]
        P4_3[4.3<br/>Process<br/>Transaction]
        P4_4[4.4<br/>Verify<br/>Payment]
        P4_5[4.5<br/>Generate<br/>Receipt]
        
        D1[(Booking<br/>Store)]
        D2[(Payment<br/>Store)]
        D3[(Transaction<br/>Log)]
    end
    
    D1 -->|Booking Info| P4_1
    P4_1 -->|Amount| P4_2
    
    Tenant -->|Payment Details| P4_2
    P4_2 -->|Request| P4_3
    
    P4_3 -->|Forward| PayGW
    PayGW -->|Response| P4_3
    
    P4_3 -->|Result| P4_4
    P4_4 -->|Store| D2
    P4_4 -->|Log| D3
    
    P4_4 -->|Success| P4_5
    D2 -->|Payment Info| P4_5
    P4_5 -->|Receipt| Tenant
```

## Data Stores

```mermaid
flowchart LR
    subgraph "Data Stores"
        D1[(User<br/>Database)]
        D2[(Property<br/>Database)]
        D3[(Booking<br/>Database)]
        D4[(Payment<br/>Database)]
        D5[(File<br/>Storage)]
        D6[(Cache<br/>Layer)]
        D7[(Search<br/>Index)]
    end
    
    D1 -.->|Synchronized| D6
    D2 -.->|Synchronized| D6
    D2 -.->|Indexed| D7
    D5 -.->|CDN| D6
```
