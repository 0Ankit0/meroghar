# System Sequence Diagrams

## Overview
Black-box system sequence diagrams showing interactions between actors and MeroGhar for the primary use cases of the house and apartment rental platform.

---

## Tenant Searches and Applies for a Property

```mermaid
sequenceDiagram
    actor Tenant
    participant Platform as MeroGhar
    participant PG as Payment Gateway
    actor Landlord

    Tenant->>Platform: GET /properties?type=apartment&city=...&bedrooms=...
    Platform-->>Tenant: Available properties with rent preview

    Tenant->>Platform: GET /properties/{propertyId}
    Platform-->>Tenant: Property details, photos, features/amenities, availability calendar

    Tenant->>Platform: GET /properties/{propertyId}/rent?moveIn=...&duration=...
    Platform-->>Tenant: Rent breakdown { monthlyRent, serviceFee, tax, securityDeposit, total }

    Tenant->>Platform: POST /rental-applications { propertyId, moveInDate, leaseDuration }
    Platform->>PG: Hold / charge security deposit
    PG-->>Platform: Deposit confirmed
    Platform-->>Tenant: 201 Rental application created { applicationId, status: PENDING }
    Platform--)Landlord: Notification: new rental application received
```

---

## Landlord Reviews Application and Sends Lease Agreement

```mermaid
sequenceDiagram
    actor Landlord
    participant Platform as MeroGhar
    participant ESign as E-Signature Provider
    actor Tenant

    Landlord->>Platform: GET /rental-applications/{applicationId}
    Platform-->>Landlord: Application details + tenant profile

    Landlord->>Platform: POST /rental-applications/{applicationId}/confirm
    Platform-->>Landlord: 200 { status: CONFIRMED }
    Platform--)Tenant: Notification: rental application confirmed

    Landlord->>Platform: POST /rental-applications/{applicationId}/lease { templateId }
    Platform-->>Landlord: 201 Lease agreement draft generated

    Landlord->>Platform: POST /rental-applications/{applicationId}/lease/send
    Platform->>ESign: Send lease agreement to tenant for signature
    ESign-->>Platform: eSignRequestId
    Platform-->>Landlord: 200 { status: PENDING_TENANT_SIGNATURE }
    Platform--)Tenant: Email: sign your lease agreement

    Tenant->>ESign: Review and sign lease agreement
    ESign->>Platform: Webhook: tenantSigned { timestamp, ip }
    Platform--)Landlord: Notification: tenant signed, please countersign

    Landlord->>Platform: POST /rental-applications/{applicationId}/lease/countersign
    Platform->>ESign: Record landlord signature
    ESign-->>Platform: Final signed PDF URL
    Platform-->>Landlord: 200 Lease agreement fully signed
    Platform--)Tenant: Email: signed lease agreement PDF
```

---

## Move-In Property Inspection

```mermaid
sequenceDiagram
    actor Staff
    participant Platform as MeroGhar
    actor Tenant

    Platform--)Staff: Task assigned: move-in inspection for application {applicationId}

    Staff->>Platform: GET /inspections/{inspectionId}
    Platform-->>Staff: Inspection task with property checklist

    Staff->>Platform: POST /inspections/{inspectionId}/items { items[] }
    Platform-->>Staff: 200 Items saved

    Staff->>Platform: POST /inspections/{inspectionId}/photos { photos[] }
    Platform-->>Staff: 200 Photos uploaded

    Staff->>Platform: POST /inspections/{inspectionId}/submit
    Platform-->>Staff: 200 Inspection submitted
    Platform--)Tenant: Notification: review and sign move-in inspection report

    Tenant->>Platform: GET /inspections/{inspectionId}
    Platform-->>Tenant: Inspection report with photos

    Tenant->>Platform: POST /inspections/{inspectionId}/countersign
    Platform-->>Tenant: 200 Countersigned; move-in complete
    Platform--)Staff: Notification: move-in confirmed
```

---

## Tenant Pays Invoice

```mermaid
sequenceDiagram
    actor Tenant
    participant Platform as MeroGhar
    participant PG as Payment Gateway
    actor Landlord

    Platform--)Tenant: Notification: invoice due { amount, dueDate }

    Tenant->>Platform: GET /invoices/{invoiceId}
    Platform-->>Tenant: Invoice details { lineItems, total, dueDate }

    Tenant->>Platform: POST /invoices/{invoiceId}/pay { paymentMethod }
    Platform->>PG: Initiate payment { amount, method }
    PG-->>Platform: Payment session / redirect URL
    Platform-->>Tenant: 200 { paymentUrl }

    Tenant->>PG: Complete payment
    PG->>Platform: Webhook: paymentConfirmed { gatewayRef, amount }
    Platform-->>Platform: Mark invoice PAID; update ledger
    Platform--)Tenant: Email: payment receipt
    Platform--)Landlord: Notification: rent payment received
```

---

## Owner Uploads Utility Bill and Publishes Tenant Splits

```mermaid
sequenceDiagram
    actor Manager as Owner/Property Manager
    participant Platform as MeroGhar
    actor TenantA as Tenant A
    actor TenantB as Tenant B

    Manager->>Platform: POST /properties/{propertyId}/utility-bills { period, dueDate, totalAmount }
    Platform-->>Manager: 201 { billId, status: DRAFT }

    Manager->>Platform: POST /utility-bills/{billId}/attachments { image/pdf }
    Platform-->>Manager: 201 Attachment stored

    alt Single tenant occupancy
        Manager->>Platform: POST /utility-bills/{billId}/splits { tenantA: 100% }
    else Multiple tenants
        Manager->>Platform: POST /utility-bills/{billId}/splits { tenantA: 60%, tenantB: 40% }
    end
    Platform->>Platform: Validate allocation total equals payable amount
    Platform-->>Manager: 200 Split validated

    Manager->>Platform: POST /utility-bills/{billId}/publish
    Platform--)TenantA: Notification: bill-share payable created
    Platform--)TenantB: Notification: bill-share payable created

    TenantA->>Platform: POST /bill-shares/{id}/pay
    TenantB->>Platform: POST /bill-shares/{id}/pay
    Platform->>Platform: Update bill settlement status and ledger
    Platform--)Manager: Notification: bill settlement progress updated
```

---

## Move-Out and Security Deposit Settlement

```mermaid
sequenceDiagram
    actor Tenant
    participant Platform as MeroGhar
    actor Staff
    participant PG as Payment Gateway
    actor Landlord

    Tenant->>Platform: POST /rental-applications/{applicationId}/move-out { actualMoveOutDate }
    Platform-->>Tenant: 200 Move-out initiated
    Platform--)Staff: Notification: perform move-out inspection

    Staff->>Platform: POST /inspections { applicationId, type: MOVE_OUT }
    Staff->>Platform: PUT /inspections/{id}/submit { items[], photos[] }
    Platform-->>Staff: 200 Inspection submitted

    Platform->>Platform: Compare move-in vs move-out inspection

    alt No Damage
        Platform->>PG: Initiate full deposit refund
        PG-->>Platform: Refund confirmed
        Platform--)Tenant: Notification: security deposit refunded
    else Damage Found
        Platform--)Landlord: Notification: review move-out inspection
        Landlord->>Platform: POST /rental-applications/{applicationId}/additional-charges { charges[] }
        Platform-->>Landlord: 200 Charges recorded
        Platform--)Tenant: Notification: additional charges applied
        Tenant->>Platform: POST /invoices/{finalInvoiceId}/pay
        Platform->>PG: Charge additional fees
        PG-->>Platform: Confirmed
    end

    Platform->>Platform: Close tenancy; update property availability
    Platform--)Landlord: Notification: tenancy closed
```

---

## Maintenance Request Lifecycle

```mermaid
sequenceDiagram
    actor Landlord
    participant Platform as MeroGhar
    actor Staff

    Landlord->>Platform: POST /maintenance-requests { propertyId, title, description, priority }
    Platform-->>Landlord: 201 { requestId, status: OPEN }
    Platform->>Platform: Block property availability calendar

    Landlord->>Platform: PUT /maintenance-requests/{id}/assign { staffUserId }
    Platform-->>Landlord: 200 Assigned
    Platform--)Staff: Notification: new maintenance task

    Staff->>Platform: PUT /maintenance-requests/{id}/status { status: IN_PROGRESS }
    Platform-->>Staff: 200 Updated

    Staff->>Platform: PUT /maintenance-requests/{id}/complete { notes, photos, materials }
    Platform-->>Staff: 200 Marked completed
    Platform--)Landlord: Notification: work completed - review needed

    Landlord->>Platform: PUT /maintenance-requests/{id}/approve
    Platform-->>Landlord: 200 Approved and closed
    Landlord->>Platform: POST /maintenance-requests/{id}/cost { amount, category }
    Platform-->>Landlord: 200 Cost logged
    Platform->>Platform: Unblock property availability calendar
```
