# Activity Diagrams

## Overview
Activity diagrams for key business processes in MeroGhar. These flows are specific to house, flat, and apartment rentals.

---

## Rental Application Flow

```mermaid
flowchart TD
    A([Tenant Starts Search]) --> B[Enter Property Type and Rental Period]
    B --> C[System Displays Available Listings]
    C --> D[Tenant Selects a Property]
    D --> E[System Shows Pricing Breakdown]
    E --> F{Tenant Confirms?}
    F -- No --> C
    F -- Yes --> G[Tenant Pays Security Deposit]
    G --> H{Payment Successful?}
    H -- No --> I[Tenant Retries Payment]
    I --> G
    H -- Yes --> J[Rental Application Created]
    J --> K{Instant Approval Enabled?}
    K -- Yes --> L[Status = CONFIRMED]
    L --> M[Both Parties Notified]
    M --> N([End - Property Reserved])
    K -- No --> O[Status = PENDING]
    O --> P[Landlord Notified]
    P --> Q{Landlord Reviews}
    Q -- Declined --> R[Deposit Refunded]
    R --> S[Tenant Notified of Decline]
    S --> N
    Q -- Approved --> L
```

---

## Rental Lifecycle Flow

```mermaid
flowchart TD
    A([Rental Application Confirmed]) --> B[Generate Lease Agreement]
    B --> C[Send Agreement to Tenant for Signature]
    C --> D{Tenant Signs?}
    D -- No --> E[Reminder Sent]
    E --> D
    D -- Yes --> F[Landlord Countersigns]
    F --> G[Signed PDF Stored]
    G --> H[Move-In Property Inspection]
    H --> I[Tenant Countersigns Inspection Report]
    I --> J[Keys Handed Over]
    J --> K([Tenancy Period Active])
    K --> L[Tenant Occupies Property]
    L --> M{Tenancy Period Ends or Tenant Vacates Early?}
    M -- Yes --> N[Tenant Initiates Move-Out]
    N --> O[Staff Completes Move-Out Inspection]
    O --> P{Damage or Late Vacation?}
    P -- No --> Q[Full Deposit Refund]
    P -- Yes --> R[Landlord Calculates Additional Charges]
    R --> S[Tenant Notified]
    S --> T{Tenant Pays Additional Charges?}
    T -- Yes --> U[Final Invoice Settled]
    T -- Disputed --> V[Admin Mediates]
    V --> U
    Q --> U
    U --> W[Property Status = AVAILABLE]
    W --> X([Tenancy Closed])
```

---

## Pricing Calculation Flow

```mermaid
flowchart TD
    A([Tenant Selects Rental Period]) --> B[System Retrieves Property Pricing Rules]
    B --> C{Multiple Rate Tiers Available?}
    C -- Yes --> D[Calculate Cost Per Tier: daily, weekly, monthly]
    D --> E[Select Optimal Tier Combination for Duration]
    C -- No --> F[Apply Single Monthly Rate for Duration]
    E --> G{Period Overlaps Peak Window?}
    F --> G
    G -- Yes --> H[Apply Peak Pricing Surcharge]
    H --> I[Apply Applicable Discount if Any]
    G -- No --> I
    I --> J[Calculate Tax per Jurisdiction]
    J --> K[Add Security Deposit Amount]
    K --> L[Generate Price Breakdown]
    L --> M[Display to Tenant]
    M --> N([End])
```

---

## Property Inspection Flow

```mermaid
flowchart TD
    A([Inspection Task Triggered]) --> B{Inspection Type?}
    B -- Move-In --> C[Staff Opens Move-In Inspection Checklist]
    B -- Move-Out --> D[Staff Opens Move-Out Inspection Checklist]

    C --> E[Complete Property-Specific Checklist Items]
    E --> F[Capture Photos for Each Item]
    F --> G[Submit Move-In Inspection]
    G --> H[Send Report to Tenant]
    H --> I{Tenant Countersigns?}
    I -- Yes --> J[Handover Complete - Tenancy Begins]
    I -- Dispute --> K[Tenant Adds Dispute Note]
    K --> L[Landlord Notified for Review]
    L --> J

    D --> M[Complete Move-Out Checklist]
    M --> N[Capture Photos for Each Item]
    N --> O[System Compares Move-In vs Move-Out Condition]
    O --> P{Discrepancies Found?}
    P -- No --> Q[Report Generated - No Damage]
    Q --> R[Full Deposit Release Initiated]
    P -- Yes --> S[Discrepancies Highlighted in Report]
    S --> T[Landlord Prompted to Add Damage Charges]
    T --> U[Tenant Notified of Charges]
    U --> V([End - Awaiting Settlement])
    R --> V
```

---

## Maintenance Request Flow

```mermaid
flowchart TD
    A([Landlord Logs Maintenance Request]) --> B[System Creates Request - OPEN]
    B --> C[Property Availability Calendar Blocked]
    C --> D[Landlord Assigns to Property Manager]
    D --> E[Property Manager Notified]
    E --> F{Property Manager Accepts?}
    F -- No --> G[Property Manager Declines with Reason]
    G --> D
    F -- Yes --> H[Status = ASSIGNED]
    H --> I[Property Manager Works on Property]
    I --> J[Status = IN_PROGRESS]
    J --> K[Property Manager Adds Notes, Photos, Materials]
    K --> L[Property Manager Marks COMPLETED]
    L --> M[Landlord Reviews Completion]
    M --> N{Landlord Approves?}
    N -- No --> O[Landlord Reopens with Reason]
    O --> J
    N -- Yes --> P[Status = CLOSED]
    P --> Q[Landlord Logs Maintenance Cost]
    Q --> R[Property Calendar Unblocked]
    R --> S([Property Available for Rental Applications])
```

---

## Cancellation and Refund Flow

```mermaid
flowchart TD
    A([Cancellation Requested]) --> B{Who Cancels?}
    B -- Tenant --> C[Tenant Submits Cancellation]
    B -- Landlord --> D[Landlord Cancels with Reason]

    C --> E[System Checks Cancellation Policy]
    D --> E

    E --> F{Time Before Tenancy Start?}
    F -- More than Free Cancellation Window --> G[Full Deposit Refund]
    F -- Within Partial Refund Window --> H[Partial Refund per Policy]
    F -- Within No Refund Window --> I[No Refund]

    G --> J[Refund Processed to Tenant]
    H --> J
    I --> K[No Refund Issued]

    J --> L[Property Calendar Unblocked]
    K --> L
    L --> M[Both Parties Notified]
    M --> N([Rental Application Cancelled])
```
