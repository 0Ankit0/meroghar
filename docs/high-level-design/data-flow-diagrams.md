# Data Flow Diagrams

## Overview
Data flow diagrams (DFDs) showing how data moves through MeroGhar for house and apartment rentals.

---

## Level 0 DFD – Context Diagram

```mermaid
graph LR
    Landlord((Landlord))
    Tenant((Tenant))
    Staff((Staff))
    Admin((Admin))
    PG((Payment Gateway))
    ESign((E-Signature Provider))

    MeroGhar[MeroGhar]

    Landlord -->|property data, pricing rules, application decisions, maintenance actions| MeroGhar
    MeroGhar -->|reports, notifications, signed agreements, payout statements| Landlord

    Tenant -->|search queries, rental applications, payments, move-out initiations| MeroGhar
    MeroGhar -->|property listings, invoices, receipts, lease agreements, inspection reports| Tenant

    Staff -->|inspection results, maintenance updates, cost logs| MeroGhar
    MeroGhar -->|assigned tasks, property details, checklists| Staff

    Admin -->|user actions, platform config, dispute resolutions| MeroGhar
    MeroGhar -->|audit logs, platform metrics, alerts| Admin

    PG -->|payment confirmations, deposit webhooks, refund confirmations| MeroGhar
    MeroGhar -->|payment initiation, deposit hold, refund requests| PG

    ESign -->|signed documents, signature webhooks| MeroGhar
    MeroGhar -->|lease agreement documents for signing| ESign
```

---

## Level 1 DFD – Key Subsystems

```mermaid
graph TD
    subgraph Inputs
        LandlordIn((Landlord))
        TenantIn((Tenant))
        StaffIn((Staff))
        PGIn((Payment GW))
        ESignIn((E-Sign))
    end

    subgraph "Property & Listing"
        DS1[(Property Store)]
        DS2[(Availability Store)]
        ProcProperty[Process: Manage Properties & Listings]
    end

    subgraph "Rental Application & Pricing"
        DS3[(Rental Application Store)]
        DS4[(Pricing Rules)]
        ProcApp[Process: Handle Rental Applications]
        ProcPrice[Process: Calculate Rent]
    end

    subgraph "Lease Agreement Management"
        DS5[(Lease Agreement Store)]
        DS6[(Document Store)]
        ProcAgreement[Process: Manage Lease Agreements]
    end

    subgraph "Payment & Invoice"
        DS7[(Invoice Store)]
        DS8[(Payment Store)]
        DS9[(Deposit Store)]
        ProcPay[Process: Process Payments]
    end

    subgraph "Property Inspections"
        DS10[(Inspection Store)]
        ProcInspect[Process: Conduct Inspections]
    end

    subgraph "Maintenance"
        DS11[(Maintenance Store)]
        ProcMaint[Process: Handle Maintenance]
    end

    subgraph "Notification Engine"
        ProcNotify[Process: Send Notifications]
    end

    LandlordIn -->|property and pricing data| ProcProperty
    ProcProperty --> DS1
    ProcProperty --> DS2
    DS4 --> ProcPrice

    TenantIn -->|search, rental application request| ProcApp
    DS1 --> ProcApp
    DS2 --> ProcApp
    ProcApp --> ProcPrice
    ProcPrice --> DS4
    ProcApp --> DS3
    PGIn -->|deposit webhook| ProcApp

    LandlordIn -->|approve/decline application| ProcApp
    ProcApp -->|confirmed application| ProcAgreement
    LandlordIn -->|lease terms| ProcAgreement
    ESignIn -->|signed document| ProcAgreement
    ProcAgreement --> DS5
    ProcAgreement --> DS6

    DS3 -->|active tenancy triggers invoice| ProcPay
    TenantIn -->|rent payment| ProcPay
    PGIn -->|payment webhook| ProcPay
    ProcPay --> DS7
    ProcPay --> DS8
    ProcPay --> DS9

    StaffIn -->|inspection data| ProcInspect
    DS3 --> ProcInspect
    ProcInspect --> DS10

    LandlordIn -->|maintenance request, assignments| ProcMaint
    StaffIn -->|task updates| ProcMaint
    ProcMaint --> DS11

    ProcApp --> ProcNotify
    ProcAgreement --> ProcNotify
    ProcPay --> ProcNotify
    ProcInspect --> ProcNotify
    ProcMaint --> ProcNotify
```

---

## Level 2 DFD – Rental Application and Pricing Process

```mermaid
graph TD
    PropertyStore[(Property Store)]
    AvailStore[(Availability Store)]
    PricingStore[(Pricing Rules)]
    AppStore[(Rental Application Store)]
    DepositStore[(Deposit Store)]

    Tenant((Tenant)) -->|search criteria| A[Search Process]
    PropertyStore -->|published properties| A
    AvailStore -->|availability windows| A
    A -->|matching listings| Tenant

    Tenant -->|selected property and move-in period| B[Rent Calculation Process]
    PricingStore -->|pricing rules| B
    B -->|rent breakdown| Tenant

    Tenant -->|rental application request| C[Rental Application Process]
    AvailStore -->|lock availability| C
    C -->|create application PENDING| AppStore
    C -->|initiate deposit| D[Deposit Collection Process]
    D -->|deposit confirmed| DepositStore
    C -->|notify landlord| E[Notification Process]

    Landlord((Landlord)) -->|approve/decline| F[Application Confirmation Process]
    AppStore --> F
    F -->|update status CONFIRMED| AppStore
    F -->|trigger lease agreement| G[Lease Agreement Generation Process]
    F --> E
```

---

## Level 2 DFD – Move-Out and Security Deposit Settlement Process

```mermaid
graph TD
    AppStore[(Rental Application Store)]
    InspectStore[(Inspection Store)]
    InvoiceStore[(Invoice Store)]
    DepositStore[(Deposit Store)]
    PaymentStore[(Payment Store)]

    Tenant((Tenant)) -->|initiate move-out| A[Move-Out Process]
    A -->|log actual move-out date| AppStore
    A -->|trigger move-out inspection task| B[Inspection Process]

    Staff((Staff)) -->|move-out checklist and photos| B
    InspectStore -->|move-in data| B
    B -->|move-out inspection| InspectStore
    B -->|comparison report| C[Damage Detection Process]

    C --> D{Damage Found?}
    D -- No --> E[Full Deposit Release Process]
    E --> DepositStore
    E --> PaymentStore

    D -- Yes --> F[Additional Charge Process]
    Landlord((Landlord)) -->|itemise charges| F
    F -->|charge records| InvoiceStore
    F -->|notify tenant| G[Notification Process]

    Tenant -->|pay final invoice| H[Payment Process]
    InvoiceStore --> H
    H -->|record payment| PaymentStore
    H -->|partial deposit deduction| DepositStore
    H --> G

    E --> I[Tenancy Closure Process]
    H --> I
    I -->|set CLOSED| AppStore
    I -->|update property availability| J[(Availability Store)]
    I --> G
```
