# Domain Model

## Overview
The domain model shows the key business entities and their relationships in MeroGhar. The model covers house, flat, and apartment rentals — including long-term tenancies and short-term stays — for property types such as Apartments, Houses, Rooms, Studios, Villas, and Commercial Spaces.

---

## Complete Domain Model

```mermaid
erDiagram
    USER ||--o{ PROPERTY : owns
    USER ||--o{ RENTAL_APPLICATION : places
    USER ||--o{ LEASE_AGREEMENT : party_to
    USER ||--o{ PAYMENT : makes
    USER ||--o{ REVIEW : writes
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ DOCUMENT : uploads

    PROPERTY_TYPE ||--o{ PROPERTY : classifies
    PROPERTY_TYPE ||--o{ PROPERTY_FEATURE : defines

    PROPERTY ||--o{ PRICING_RULE : has
    PROPERTY ||--o{ AVAILABILITY_BLOCK : has
    PROPERTY ||--o{ RENTAL_APPLICATION : receives
    PROPERTY ||--o{ PROPERTY_PHOTO : has
    PROPERTY ||--o{ DOCUMENT : has
    PROPERTY ||--o{ MAINTENANCE_REQUEST : subject_of
    PROPERTY ||--o{ REVIEW : receives
    PROPERTY ||--o{ PROPERTY_FEATURE_VALUE : has

    RENTAL_APPLICATION ||--o{ PAYMENT : paid_by
    RENTAL_APPLICATION ||--|| LEASE_AGREEMENT : has
    RENTAL_APPLICATION ||--|| SECURITY_DEPOSIT : has
    RENTAL_APPLICATION ||--o{ PROPERTY_INSPECTION : has
    RENTAL_APPLICATION ||--o{ ADDITIONAL_CHARGE : incurs
    RENTAL_APPLICATION ||--o{ INVOICE : generates
    RENTAL_APPLICATION ||--o{ APPLICATION_EVENT : emits

    LEASE_AGREEMENT ||--o{ DOCUMENT : generates
    LEASE_AGREEMENT ||--o{ LEASE_AMENDMENT : has

    SECURITY_DEPOSIT ||--o{ DEPOSIT_DEDUCTION : has

    PROPERTY_INSPECTION ||--o{ INSPECTION_ITEM : contains
    PROPERTY_INSPECTION ||--o{ INSPECTION_PHOTO : has

    INVOICE ||--o{ PAYMENT : paid_by

    MAINTENANCE_REQUEST ||--o{ REQUEST_EVENT : emits
    MAINTENANCE_REQUEST ||--o{ MAINTENANCE_PHOTO : has
    MAINTENANCE_REQUEST ||--|| MAINTENANCE_COST : has

    LANDLORD_PAYOUT ||--o{ RENTAL_APPLICATION : settles
```

---

## User Domain

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String phone
        +String fullName
        +String passwordHash
        +UserRole role
        +UserStatus status
        +Boolean emailVerified
        +Boolean phoneVerified
        +DateTime createdAt
        +DateTime lastLoginAt
        +register()
        +login()
        +updateProfile()
        +resetPassword()
    }

    class LandlordProfile {
        +UUID id
        +UUID userId
        +String businessName
        +String tradingName
        +LandlordVerificationStatus verificationStatus
        +Decimal commissionRate
        +String bankAccountDetails
        +DateTime verifiedAt
        +getProperties()
        +getRentalApplications()
        +getPortfolioSummary()
    }

    class TenantProfile {
        +UUID id
        +UUID userId
        +TenantVerificationStatus idVerificationStatus
        +String citizenshipNumber
        +String passportNumber
        +String employmentStatus
        +Decimal monthlyIncome
        +Decimal outstandingBalance
        +getActiveApplications()
        +getPaymentHistory()
    }

    class PropertyManagerProfile {
        +UUID id
        +UUID userId
        +UUID landlordUserId
        +String specialisation
        +Boolean isAvailable
        +getAssignedTasks()
        +setAvailability()
    }

    class Notification {
        +UUID id
        +UUID userId
        +String eventType
        +String title
        +String body
        +Boolean isRead
        +JSON payload
        +DateTime createdAt
    }

    User "1" --> "0..1" LandlordProfile
    User "1" --> "0..1" TenantProfile
    User "1" --> "0..1" PropertyManagerProfile
    User "1" --> "*" Notification
```

---

## Property Domain

```mermaid
classDiagram
    class PropertyType {
        +UUID id
        +String name
        +String slug
        +String description
        +String iconUrl
        +UUID parentTypeId
        +Boolean isActive
        +getFeatures()
        +getProperties()
    }

    class PropertyFeature {
        +UUID id
        +UUID propertyTypeId
        +String name
        +String slug
        +AttributeType type
        +Boolean isRequired
        +Boolean isFilterable
        +JSON options
        +Integer displayOrder
    }

    class Property {
        +UUID id
        +UUID ownerUserId
        +UUID propertyTypeId
        +String name
        +String description
        +PropertyStatus status
        +Boolean isPublished
        +String locationAddress
        +Decimal locationLat
        +Decimal locationLng
        +Decimal depositAmount
        +Integer bedrooms
        +Integer bathrooms
        +Decimal floorAreaSqft
        +String furnishingStatus
        +Boolean hasParking
        +Boolean hasBalcony
        +Integer minRentalDurationDays
        +Integer maxRentalDurationDays
        +Integer applicationLeadTimeDays
        +Decimal averageRating
        +Integer reviewCount
        +DateTime createdAt
        +publish()
        +unpublish()
        +checkAvailability(start, end)
        +calculateRent(start, end)
    }

    class PropertyFeatureValue {
        +UUID id
        +UUID propertyId
        +UUID featureId
        +String value
    }

    class PropertyPhoto {
        +UUID id
        +UUID propertyId
        +String url
        +String thumbnailUrl
        +Integer position
        +Boolean isCover
        +String caption
    }

    class PricingRule {
        +UUID id
        +UUID propertyId
        +RateType rateType
        +Decimal rateAmount
        +String currency
        +Boolean isPeakRate
        +Date peakStartDate
        +Date peakEndDate
        +DayOfWeek[] peakDaysOfWeek
        +Decimal discountPercentage
        +Integer minUnitsForDiscount
        +isApplicable(period) Boolean
        +calculateCost(units) Decimal
    }

    class AvailabilityBlock {
        +UUID id
        +UUID propertyId
        +AvailabilityBlockType type
        +DateTime startAt
        +DateTime endAt
        +String reason
        +UUID rentalApplicationId
        +UUID maintenanceRequestId
        +create()
        +release()
    }

    PropertyType "1" --> "*" PropertyType : parentOf
    PropertyType "1" --> "*" PropertyFeature
    PropertyType "1" --> "*" Property
    Property "1" --> "*" PropertyFeatureValue
    Property "1" --> "*" PropertyPhoto
    Property "1" --> "*" PricingRule
    Property "1" --> "*" AvailabilityBlock
```

---

## Rental Application Domain

```mermaid
classDiagram
    class RentalApplication {
        +UUID id
        +String applicationNumber
        +UUID propertyId
        +UUID tenantUserId
        +UUID landlordUserId
        +ApplicationStatus status
        +DateTime moveInDate
        +DateTime moveOutDate
        +DateTime actualMoveOutDate
        +Decimal monthlyRent
        +Decimal serviceFee
        +Decimal taxAmount
        +Decimal totalFee
        +Decimal depositAmount
        +String cancellationReason
        +DateTime cancelledAt
        +DateTime createdAt
        +confirm()
        +cancel(reason)
        +modify(newMoveIn, newMoveOut)
        +initiateMoveOut()
        +close()
    }

    class ApplicationEvent {
        +UUID id
        +UUID applicationId
        +String eventType
        +String message
        +UUID actorUserId
        +JSON metadata
        +DateTime createdAt
    }

    class SecurityDeposit {
        +UUID id
        +UUID applicationId
        +Decimal amount
        +DepositStatus status
        +String gatewayRef
        +Decimal deductionTotal
        +Decimal refundAmount
        +DateTime collectedAt
        +DateTime settledAt
        +addDeduction(reason, amount, evidence)
        +processRefund()
        +getTotalDeductions()
    }

    class DepositDeduction {
        +UUID id
        +UUID depositId
        +String reason
        +Decimal amount
        +String evidenceUrl
        +DateTime createdAt
    }

    class LeaseAgreement {
        +UUID id
        +UUID applicationId
        +UUID templateId
        +AgreementStatus status
        +String eSignRequestId
        +String signedDocumentUrl
        +DateTime sentAt
        +DateTime tenantSignedAt
        +String tenantSignatureIp
        +DateTime landlordSignedAt
        +String landlordSignatureIp
        +Integer version
        +send()
        +tenantSign(ip)
        +landlordSign(ip)
        +amend(changes)
    }

    class LeaseAmendment {
        +UUID id
        +UUID agreementId
        +String reason
        +String amendedDocumentUrl
        +AgreementStatus status
        +DateTime createdAt
        +DateTime signedAt
    }

    RentalApplication "1" --> "*" ApplicationEvent
    RentalApplication "1" --> "1" SecurityDeposit
    RentalApplication "1" --> "1" LeaseAgreement
    SecurityDeposit "1" --> "*" DepositDeduction
    LeaseAgreement "1" --> "*" LeaseAmendment
```

---

## Invoice & Payment Domain

```mermaid
classDiagram
    class Invoice {
        +UUID id
        +String invoiceNumber
        +UUID applicationId
        +UUID tenantUserId
        +UUID landlordUserId
        +InvoiceType type
        +Decimal subtotal
        +Decimal taxAmount
        +Decimal totalAmount
        +Decimal paidAmount
        +InvoiceStatus status
        +Date dueDate
        +DateTime createdAt
        +DateTime paidAt
        +addLineItem(description, amount)
        +recordPayment(paymentId)
        +generateReceipt()
        +getOutstandingAmount()
    }

    class InvoiceLineItem {
        +UUID id
        +UUID invoiceId
        +String description
        +LineItemType type
        +Decimal amount
        +Decimal taxRate
    }

    class AdditionalCharge {
        +UUID id
        +UUID applicationId
        +AdditionalChargeType type
        +String description
        +Decimal amount
        +String evidenceUrl
        +ChargeStatus status
        +String disputeReason
        +DateTime createdAt
        +DateTime resolvedAt
        +dispute(reason)
        +approve()
        +waive()
    }

    class Payment {
        +UUID id
        +String referenceType
        +UUID referenceId
        +UUID payerUserId
        +PaymentMethod method
        +PaymentStatus status
        +Decimal amount
        +String currency
        +String gatewayRef
        +JSON gatewayResponse
        +Boolean isOffline
        +DateTime createdAt
        +DateTime confirmedAt
        +process()
        +refund()
    }

    class LandlordPayout {
        +UUID id
        +UUID landlordUserId
        +Decimal grossAmount
        +Decimal commissionAmount
        +Decimal netAmount
        +PayoutStatus status
        +String bankRef
        +String batchId
        +DateTime periodStart
        +DateTime periodEnd
        +DateTime processedAt
        +calculate()
        +process()
    }

    Invoice "1" --> "*" InvoiceLineItem
    Invoice "1" --> "*" Payment
    RentalApplication "1" --> "*" AdditionalCharge
```

---

## Property Inspection Domain

```mermaid
classDiagram
    class PropertyInspection {
        +UUID id
        +UUID applicationId
        +UUID propertyId
        +UUID conductedByUserId
        +InspectionType type
        +InspectionStatus status
        +String notes
        +String reportUrl
        +DateTime scheduledAt
        +DateTime conductedAt
        +DateTime tenantSignedAt
        +String tenantSignatureIp
        +conduct(checklist, photos)
        +generateReport()
        +compareWithMoveIn()
    }

    class InspectionItem {
        +UUID id
        +UUID inspectionId
        +String area
        +String description
        +ItemCondition condition
        +Boolean hasDamage
        +String damageDescription
    }

    class InspectionPhoto {
        +UUID id
        +UUID inspectionId
        +UUID inspectionItemId
        +String url
        +String caption
        +DateTime uploadedAt
    }

    PropertyInspection "1" --> "*" InspectionItem
    PropertyInspection "1" --> "*" InspectionPhoto
```

---

## Maintenance Domain

```mermaid
classDiagram
    class MaintenanceRequest {
        +UUID id
        +String requestNumber
        +UUID propertyId
        +UUID landlordUserId
        +UUID assignedToUserId
        +RequestPriority priority
        +RequestStatus status
        +String title
        +String description
        +String resolutionNotes
        +DateTime createdAt
        +DateTime assignedAt
        +DateTime startedAt
        +DateTime completedAt
        +DateTime closedAt
        +assign(staffUserId)
        +start()
        +complete(notes, photos)
        +approve()
        +reopen(reason)
        +getTotalCost()
    }

    class MaintenanceCost {
        +UUID id
        +UUID requestId
        +CostCategory category
        +String description
        +Decimal amount
        +DateTime recordedAt
    }

    class PreventiveService {
        +UUID id
        +UUID propertyId
        +UUID assignedToUserId
        +String title
        +String description
        +ServiceRecurrence recurrence
        +Integer intervalDays
        +Date nextDueDate
        +TaskStatus status
        +schedule()
        +complete(notes)
        +generateNext()
    }

    MaintenanceRequest "1" --> "0..1" MaintenanceCost
```

---

## Enumeration Types

```mermaid
classDiagram
    class UserRole {
        <<enumeration>>
        LANDLORD
        TENANT
        PROPERTY_MANAGER
        ADMIN
    }

    class PropertyStatus {
        <<enumeration>>
        DRAFT
        AVAILABLE
        RENTED
        UNDER_MAINTENANCE
        RETIRED
    }

    class ApplicationStatus {
        <<enumeration>>
        PENDING
        CONFIRMED
        ACTIVE
        PENDING_CLOSURE
        CLOSED
        CANCELLED
        DECLINED
    }

    class AgreementStatus {
        <<enumeration>>
        DRAFT
        PENDING_TENANT_SIGNATURE
        PENDING_LANDLORD_SIGNATURE
        SIGNED
        AMENDED
        TERMINATED
    }

    class InvoiceStatus {
        <<enumeration>>
        DRAFT
        SENT
        PARTIALLY_PAID
        PAID
        OVERDUE
        WAIVED
    }

    class RequestStatus {
        <<enumeration>>
        OPEN
        ASSIGNED
        IN_PROGRESS
        COMPLETED
        CLOSED
        REOPENED
        CANCELLED
    }

    class RateType {
        <<enumeration>>
        DAILY
        WEEKLY
        MONTHLY
    }

    class InspectionType {
        <<enumeration>>
        MOVE_IN
        MOVE_OUT
        ROUTINE
    }

    class AdditionalChargeType {
        <<enumeration>>
        DAMAGE
        LATE_VACATION
        CLEANING_FEE
        UNPAID_UTILITIES
        OTHER
    }
```
