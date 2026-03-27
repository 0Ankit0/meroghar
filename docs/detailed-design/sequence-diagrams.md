# Sequence Diagrams

## Overview
Internal sequence diagrams showing object-level interactions within MeroGhar for key operations.

---

## Rental Application Creation with Availability Lock

```mermaid
sequenceDiagram
    participant Router as API Router
    participant BookingSvc as BookingService
    participant PricingEng as PricingEngine
    participant AvailRepo as AvailabilityRepository
    participant BookingRepo as BookingRepository
    participant PaymentSvc as PaymentService
    participant EventPub as EventPublisher

    Router->>RentalApplicationSvc: createRentalApplication(tenantId, propertyId, start, end)
    BookingSvc->>AvailRepo: isAvailable(propertyId, start, end)
    AvailRepo-->>BookingSvc: true

    BookingSvc->>PricingEng: calculatePrice(propertyId, start, end)
    PricingEng-->>BookingSvc: PriceBreakdown

    BookingSvc->>PaymentSvc: holdDeposit(tenantId, depositAmount)
    PaymentSvc-->>BookingSvc: depositHoldRef

    BookingSvc->>AvailRepo: createBlock(propertyId, start, end, BOOKING_HOLD)
    AvailRepo-->>BookingSvc: availabilityBlockId

    BookingSvc->>BookingRepo: save(rental application)
    BookingRepo-->>BookingSvc: savedBooking

    BookingSvc->>EventPub: publish("rental application.created", { bookingId, ownerId })
    EventPub-->>BookingSvc: acknowledged

    BookingSvc-->>Router: BookingResponse
```

---

## Lease Agreement E-Signature Flow

```mermaid
sequenceDiagram
    participant Router as API Router
    participant AgreeSvc as AgreementService
    participant TemplateRepo as TemplateRepository
    participant ESignClient as ESignatureClient
    participant AgreementRepo as AgreementRepository
    participant StorageSvc as StorageService
    participant EventPub as EventPublisher

    Router->>AgreeSvc: createAndSend(bookingId, templateId)
    AgreeSvc->>TemplateRepo: findById(templateId)
    TemplateRepo-->>AgreeSvc: AgreementTemplate

    AgreeSvc->>AgreeSvc: renderTemplate(template, bookingDetails)

    AgreeSvc->>ESignClient: createSignatureRequest(renderedContent, tenantEmail)
    ESignClient-->>AgreeSvc: eSignRequestId

    AgreeSvc->>AgreementRepository: save({ bookingId, status: PENDING_CUSTOMER_SIGNATURE, eSignRequestId })
    AgreementRepository-->>AgreeSvc: savedAgreement

    AgreeSvc->>EventPub: publish("agreement.sent", { bookingId, tenantId })
    EventPub-->>AgreeSvc: acknowledged
    AgreeSvc-->>Router: AgreementResponse

    note over ESignClient: Tenant signs via e-sign provider

    ESignClient->>Router: Webhook POST /webhooks/esign { event: customerSigned, eSignRequestId }
    Router->>AgreeSvc: handleCustomerSigned(eSignRequestId, timestamp, ip)
    AgreeSvc->>AgreementRepository: update({ status: PENDING_OWNER_SIGNATURE, customerSignedAt, ip })
    AgreeSvc->>EventPub: publish("agreement.customerSigned", { bookingId, ownerId })
    EventPub-->>AgreeSvc: acknowledged

    note over ESignClient: Landlord countersigns

    ESignClient->>Router: Webhook POST /webhooks/esign { event: ownerSigned, documentUrl }
    Router->>AgreeSvc: handleOwnerSigned(eSignRequestId, documentUrl, ip)
    AgreeSvc->>StorageSvc: storeSignedPDF(documentUrl)
    StorageSvc-->>AgreeSvc: stableStorageUrl
    AgreeSvc->>AgreementRepository: update({ status: SIGNED, ownerSignedAt, signedDocumentUrl })
    AgreeSvc->>EventPub: publish("agreement.signed", { bookingId, tenantId, ownerId })
```

---

## Price Calculation Engine

```mermaid
sequenceDiagram
    participant BookingSvc as BookingService
    participant PricingEng as PricingEngine
    participant RuleRepo as PricingRuleRepository
    participant TaxSvc as TaxService

    BookingSvc->>PricingEng: calculatePrice(propertyId, startAt, endAt)

    PricingEng->>RuleRepo: findByProperty(propertyId)
    RuleRepo-->>PricingEng: PricingRule[]

    PricingEng->>PricingEng: computeDuration(startAt, endAt) → hours
    PricingEng->>PricingEng: selectOptimalRateCombination(hours, rules)
    note over PricingEng: Tries hourly, daily, weekly, monthly combinations<br/>picks lowest total cost

    PricingEng->>PricingEng: applyPeakSurcharges(baseFee, rules, startAt, endAt)
    PricingEng->>PricingEng: applyDiscounts(baseFee, rules, hours)

    PricingEng->>TaxSvc: calculateTax(subtotal, propertyTypeId, jurisdiction)
    TaxSvc-->>PricingEng: taxAmount

    PricingEng-->>BookingSvc: PriceBreakdown { baseFee, peakSurcharge, discount, tax, total }
```

---

## Post-Rental Assessment and Damage Charge

```mermaid
sequenceDiagram
    participant Router as API Router
    participant AssessSvc as AssessmentService
    participant AssessRepo as AssessmentRepository
    participant StorageSvc as StorageService
    participant ChargeSvc as ChargeService
    participant EventPub as EventPublisher

    Router->>AssessSvc: submitPostRentalAssessment(bookingId, items, photos)

    AssessSvc->>AssessRepo: findPreRentalAssessment(bookingId)
    AssessRepo-->>AssessSvc: preAssessment

    AssessSvc->>AssessSvc: compareAssessments(pre, post)
    AssessSvc->>StorageSvc: storePhotos(photos)
    StorageSvc-->>AssessSvc: photoUrls[]

    AssessSvc->>AssessRepo: save(postAssessment)
    AssessRepo-->>AssessSvc: savedAssessment

    AssessSvc->>AssessSvc: generateComparisonReport(pre, post)
    AssessSvc->>StorageSvc: storeReport(report)
    StorageSvc-->>AssessSvc: reportUrl

    alt Discrepancies Found
        AssessSvc->>EventPub: publish("assessment.damageFound", { bookingId, ownerId, findings })
        EventPub-->>AssessSvc: acknowledged
        note over Router: Landlord adds damage charges
        Router->>ChargeSvc: addAdditionalCharge(bookingId, type, amount, evidenceUrl)
        ChargeSvc->>EventPub: publish("charge.raised", { bookingId, tenantId, amount })
    else No Discrepancies
        AssessSvc->>EventPub: publish("assessment.clean", { bookingId })
        EventPub-->>AssessSvc: acknowledged
        note over Router: Deposit refund triggered automatically
    end

    AssessSvc-->>Router: AssessmentResponse
```

---

## Overdue Return Detection (Async Worker)

```mermaid
sequenceDiagram
    participant Scheduler as Job Scheduler
    participant Worker as Async Worker
    participant BookingRepo as BookingRepository
    participant ChargeSvc as ChargeService
    participant InvoiceSvc as InvoiceService
    participant EventPub as EventPublisher

    Scheduler->>Worker: triggerOverdueCheck()

    Worker->>BookingRepo: findActiveBookingsPastEndTime(currentTime)
    BookingRepo-->>Worker: overdueBookings[]

    loop For each overdue rental application
        Worker->>Worker: calculateOverdueHours(rental application.rentalEndAt, currentTime)
        Worker->>ChargeSvc: calculateLateReturnFee(propertyId, overdueHours)
        ChargeSvc-->>Worker: lateReturnFee

        Worker->>InvoiceSvc: addLateReturnLineItem(bookingId, lateReturnFee)
        InvoiceSvc-->>Worker: updated invoice

        Worker->>EventPub: publish("rental application.lateReturn", { bookingId, tenantId, ownerId, fee })
        EventPub-->>Worker: acknowledged
    end
```
