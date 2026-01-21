# System Context Diagram

## C4 Context Level

```mermaid
graph TB
    subgraph "External Actors"
        Owner[Property Owner]
        Tenant[Tenant]
        Admin[Administrator]
    end
    
    subgraph "MeroGhar System Boundary"
        MeroGhar[MeroGhar<br/>Rental Platform]
    end
    
    subgraph "External Systems"
        PaymentGW[Payment Gateway<br/>eSewa/Khalti]
        EmailSvc[Email Service<br/>SMTP]
        SMSSvc[SMS Service]
        Maps[Google Maps API]
        Storage[Cloud Storage<br/>Image Hosting]
        Analytics[Analytics Service]
    end
    
    Owner -->|Manage Properties<br/>View Bookings| MeroGhar
    Tenant -->|Search & Book<br/>Make Payments| MeroGhar
    Admin -->|Manage Users<br/>Moderate Content| MeroGhar
    
    MeroGhar -->|Process Payments| PaymentGW
    MeroGhar -->|Send Emails| EmailSvc
    MeroGhar -->|Send SMS Notifications| SMSSvc
    MeroGhar -->|Get Location Data| Maps
    MeroGhar -->|Store Images| Storage
    MeroGhar -->|Track Events| Analytics
    
    PaymentGW -->|Payment Confirmation| MeroGhar
    EmailSvc -->|Delivery Status| MeroGhar
```

## System Boundaries

### Internal (Within System Boundary)
- User Management
- Property Management
- Booking System
- Payment Processing Logic
- Notification Orchestration
- Analytics Dashboard
- Content Moderation

### External (Outside System Boundary)
- Bank Payment Gateways (eSewa, Khalti, etc.)
- Email Service Providers
- SMS Gateway Providers
- Google Maps API
- Cloud Storage (AWS S3, Google Cloud Storage)
- Third-party Analytics Tools

## Data Flows

```mermaid
flowchart LR
    subgraph Users
        U1[Property Owners]
        U2[Tenants]
        U3[Admins]
    end
    
    subgraph "MeroGhar Platform"
        API[API Gateway]
        Auth[Authentication]
        App[Application Logic]
        DB[(Database)]
    end
    
    subgraph "External Services"
        PG[Payment Gateway]
        Email[Email Service]
        SMS[SMS Service]
    end
    
    U1 & U2 & U3 -->|HTTPS| API
    API --> Auth
    Auth --> App
    App <--> DB
    App -->|Payment Request| PG
    PG -->|Payment Status| App
    App -->|Notifications| Email
    App -->|Notifications| SMS
```
