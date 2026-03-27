# High-Level Architecture Diagram

## Overview
The MeroGhar platform is designed as a modular API application. Each domain module (properties, rental applications, lease agreements, payments, maintenance) is independently testable and can be extracted to a separate service if scale demands it.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        LandlordWeb[Landlord Web Portal]
        TenantWeb[Tenant Web App]
        TenantMobile[Tenant Mobile App]
        StaffApp[Staff Mobile App]
        AdminApp[Admin Dashboard]
    end

    subgraph "Edge"
        CDN[CDN]
        WAF[WAF]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[REST API Application]

        subgraph "Backend Modules"
            IAM[IAM & Auth]
            PropertyMgmt[Property & Listing Management]
            ApplicationMgmt[Rental Application & Reservation]
            AgreementMgmt[Lease Agreements]
            PricingEngine[Pricing Engine]
            PaymentMgmt[Payments & Invoices]
            DepositMgmt[Deposit & Charges]
            InspectionMgmt[Property Inspections]
            MaintMgmt[Maintenance & Servicing]
            Reporting[Reports & Analytics]
            Notify[Notifications & WebSocket]
        end
    end

    subgraph "Data"
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[(Object Storage)]
    end

    subgraph "External Services"
        PaymentGW[Payment Providers<br>Stripe / PayPal / Bank]
        ESign[E-Signature Provider<br>DocuSign / Adobe Sign]
        IDVerify[Identity Verification<br>Onfido / Jumio]
        Maps[Maps Provider]
        Messaging[Email / SMS / Push]
    end

    LandlordWeb --> CDN
    TenantWeb --> CDN
    TenantMobile --> CDN
    StaffApp --> CDN
    AdminApp --> CDN

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> PropertyMgmt
    API --> ApplicationMgmt
    API --> AgreementMgmt
    API --> PricingEngine
    API --> PaymentMgmt
    API --> DepositMgmt
    API --> InspectionMgmt
    API --> MaintMgmt
    API --> Reporting
    API --> Notify

    IAM --> DB
    PropertyMgmt --> DB
    ApplicationMgmt --> DB
    AgreementMgmt --> DB
    PricingEngine --> DB
    PaymentMgmt --> DB
    DepositMgmt --> DB
    InspectionMgmt --> DB
    MaintMgmt --> DB
    Reporting --> DB
    Notify --> DB

    IAM --> Redis
    ApplicationMgmt --> Redis
    PricingEngine --> Redis

    PropertyMgmt --> Storage
    AgreementMgmt --> Storage
    InspectionMgmt --> Storage
    Reporting --> Storage

    PaymentMgmt --> PaymentGW
    DepositMgmt --> PaymentGW
    AgreementMgmt --> ESign
    IAM --> IDVerify
    PropertyMgmt --> Maps
    Notify --> Messaging
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[API Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Redis[(Redis)]

    Domain --> Event[Domain Event / Notification Record]
    Event --> Notify[Notification Dispatcher]
    Notify --> WS[WebSocket Manager]
    Notify --> Msg[Email / SMS / Push]

    Domain --> External[Payment / E-Sign / IDVerify / Maps]
    Domain --> Storage[Object Storage]
    Worker[Async Worker] --> Domain
    Worker --> Notify
```

---

## Key Backend Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, OTP, RBAC, ID verification integration, audit log |
| Property & Listing | Property CRUD, custom property type features, photo storage, availability calendar, publish/unpublish |
| Rental Application & Reservation | Application creation, availability locking, instant vs manual confirmation, modification, cancellation |
| Lease Agreements | Template rendering, e-signature dispatch, signing webhooks, PDF storage, versioning |
| Pricing Engine | Monthly rent calculation, short-term daily/weekly rates, peak pricing, discounts, tax rules |
| Payments & Invoices | Invoice generation, payment gateway integration, receipt generation, late fees, payout processing |
| Deposit & Charges | Security deposit hold/release, damage deductions, dispute handling, settlement |
| Property Inspections | Move-in/move-out checklists, photo capture, comparison reports, tenant countersignature |
| Maintenance | Request lifecycle, staff assignment, cost logging, preventive scheduling, calendar blocking |
| Reports & Analytics | Revenue reports, occupancy reports, tax summaries, payout history |
| Notifications | Persisted notifications, WebSocket fanout, email/SMS/push dispatch |

---

## Async Worker Responsibilities

| Job | Trigger | Action |
|-----|---------|--------|
| Rental application reminder | 24h before move-in date | Send reminder to tenant and landlord |
| Overdue move-out detection | Polling every 15 min | Detect overdue vacations; apply fees; notify parties |
| Payout batch processing | Scheduled (daily/weekly) | Aggregate closed tenancies; process bank transfers |
| Availability expiry | On application timeout | Release availability hold if deposit not paid |
| Preventive service reminders | Scheduled | Alert landlord of upcoming scheduled property service |
| Report generation | On-demand or scheduled | Build and store report exports |
