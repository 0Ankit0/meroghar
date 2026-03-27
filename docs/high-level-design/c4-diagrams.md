# C4 Diagrams

## Overview
C4 model diagrams for MeroGhar: Context (Level 1) and Container (Level 2). The platform is a house and apartment rental system for Nepal, supporting property types including Apartments, Houses, Rooms, Studios, Villas, and Commercial Spaces.

---

## Level 1 – System Context Diagram

```mermaid
graph TB
    Landlord["Landlord / Property Owner
    [Person]
    Lists and manages rental properties,
    reviews rental applications, oversees
    payments and maintenance"]

    Tenant["Tenant
    [Person]
    Searches properties, submits rental
    applications, signs lease agreements,
    pays rent and invoices, vacates property"]

    Staff["Property Manager / Staff
    [Person]
    Conducts property inspections,
    performs maintenance tasks"]

    Admin["Platform Admin
    [Person]
    Manages users, resolves disputes,
    configures platform"]

    MeroGhar["MeroGhar
    [Software System]
    House and apartment rental management
    platform for Nepal — connecting landlords
    and tenants for long-term and short-term stays"]

    PG["Payment Gateway
    [External System]
    Stripe / PayPal / Bank Transfer"]

    ESign["E-Signature Provider
    [External System]
    DocuSign / Adobe Sign"]

    IDVerify["Identity Verification
    [External System]
    Onfido / Jumio"]

    Notify["Messaging Services
    [External System]
    Email / SMS / Push"]

    Landlord -->|"manage properties, applications, reports, payouts"| MeroGhar
    Tenant -->|"search, apply, pay rent, inspections, vacate, review"| MeroGhar
    Staff -->|"property inspections, maintenance tasks"| MeroGhar
    Admin -->|"platform oversight and configuration"| MeroGhar

    MeroGhar -->|"process payments, deposits, refunds"| PG
    MeroGhar -->|"send and receive signed documents"| ESign
    MeroGhar -->|"verify tenant identity"| IDVerify
    MeroGhar -->|"email, SMS, push notifications"| Notify
```

---

## Level 2 – Container Diagram

```mermaid
graph TB
    LandlordPortal["Landlord Web Portal
    [Web App: Next.js]
    Property management, rental applications,
    reports, maintenance"]

    TenantWeb["Tenant Web App
    [Web App: Next.js]
    Search properties, apply, pay rent,
    lease agreements, inspections, reviews"]

    TenantMobile["Tenant Mobile App
    [Mobile: Flutter / React Native]
    Full tenant experience on mobile"]

    StaffApp["Staff Mobile App
    [Mobile: Flutter / React Native]
    Property inspections,
    maintenance task management"]

    AdminUI["Admin Dashboard
    [Web App: Next.js / React]
    User management, disputes,
    platform configuration"]

    subgraph "MeroGhar"
        API["REST API
        [Container: FastAPI / Node.js]
        Core business logic, auth,
        routing to domain modules"]

        Worker["Async Worker
        [Container: Celery / BullMQ]
        Application reminders, overdue detection,
        payout batching, report generation"]

        WS["WebSocket Server
        [Container]
        Real-time push to connected clients"]

        DB["Primary Database
        [Container: PostgreSQL]
        All persistent rental domain data"]

        Redis["Cache & Task Queue
        [Container: Redis]
        Session cache, availability locks,
        task queue, rate limiting"]

        Storage["Object Storage
        [Container: S3 / GCS]
        Property photos, signed lease agreements,
        inspection reports, export files"]
    end

    PG["Payment Gateway
    [External System]"]

    ESign["E-Signature Provider
    [External System]"]

    IDVerify["Identity Verification
    [External System]"]

    Notify["Messaging Services
    [External System]"]

    LandlordPortal -->|"HTTPS/REST"| API
    TenantWeb -->|"HTTPS/REST"| API
    TenantMobile -->|"HTTPS/REST"| API
    StaffApp -->|"HTTPS/REST"| API
    AdminUI -->|"HTTPS/REST"| API

    TenantWeb -->|"WSS"| WS
    TenantMobile -->|"WSS"| WS
    LandlordPortal -->|"WSS"| WS

    API -->|"read/write"| DB
    API -->|"cache + lock"| Redis
    API -->|"store/retrieve files"| Storage
    API -->|"enqueue async jobs"| Redis

    Worker -->|"read/write"| DB
    Worker -->|"dequeue jobs"| Redis
    Worker -->|"send"| Notify
    Worker -->|"store exports"| Storage

    WS -->|"read notifications"| DB

    API -->|"HTTPS"| PG
    API -->|"HTTPS"| ESign
    API -->|"HTTPS"| IDVerify
    Worker -->|"HTTPS"| Notify
```

---

## Level 2 – Container Responsibilities

| Container | Technology | Role |
|-----------|------------|------|
| REST API | FastAPI / Node.js | Core request handler; all domain modules exposed as REST endpoints |
| Async Worker | Celery / BullMQ | Application reminders, overdue move-out detection, payout batching, report generation |
| WebSocket Server | FastAPI WS / Socket.io | Real-time notifications to browser and mobile app clients |
| Primary Database | PostgreSQL | Source of truth for all rental entities; JSONB for flexible property features and amenities |
| Cache & Queue | Redis | JWT block list, availability locks, rate-limit counters, task queue |
| Object Storage | AWS S3 / GCS | Property photos, signed lease agreement PDFs, inspection reports, financial export files |
