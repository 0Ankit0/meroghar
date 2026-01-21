# System Sequence Diagram

## Book Property - Black Box Interaction

```mermaid
sequenceDiagram
    actor Tenant
    participant System
    actor Owner
    
    Tenant->>System: searchProperties(criteria)
    System-->>Tenant: propertyList
    
    Tenant->>System: viewPropertyDetails(propertyId)
    System-->>Tenant: propertyDetails
    
    Tenant->>System: checkAvailability(propertyId, dates)
    System-->>Tenant: availabilityStatus
    
    Tenant->>System: createBooking(propertyId, dates, details)
    System-->>Tenant: bookingConfirmation
    System->>Owner: notifyBookingRequest(bookingId)
    
    Owner->>System: reviewBooking(bookingId)
    System-->>Owner: bookingDetails
    
    Owner->>System: approveBooking(bookingId)
    System->>Tenant: notifyApproval(bookingId)
    System-->>Owner: approvalConfirmation
    
    Tenant->>System: processPayment(bookingId, paymentInfo)
    System-->>Tenant: paymentReceipt
    System->>Owner: notifyPaymentReceived(bookingId)
```

## Property Listing Creation

```mermaid
sequenceDiagram
    actor Owner
    participant System
    actor Admin
    
    Owner->>System: login(credentials)
    System-->>Owner: authToken
    
    Owner->>System: createProperty(propertyData)
    System-->>Owner: propertyId
    
    Owner->>System: uploadPhotos(propertyId, photos)
    System-->>Owner: uploadConfirmation
    
    Owner->>System: setPricing(propertyId, priceData)
    System-->>Owner: pricingConfirmation
    
    Owner->>System: submitForReview(propertyId)
    System-->>Owner: submissionConfirmation
    System->>Admin: notifyPendingReview(propertyId)
    
    Admin->>System: reviewProperty(propertyId)
    System-->>Admin: propertyFullDetails
    
    Admin->>System: approveProperty(propertyId)
    System->>Owner: notifyApproval(propertyId)
    System-->>Admin: approvalConfirmation
```

## User Authentication Flow

```mermaid
sequenceDiagram
    actor User
    participant System
    
    User->>System: register(email, password, userType)
    System-->>User: verificationEmail
    
    User->>System: verifyEmail(token)
    System-->>User: accountActivated
    
    User->>System: login(email, password)
    System-->>User: authToken, userProfile
    
    User->>System: updateProfile(profileData)
    System-->>User: updateConfirmation
    
    User->>System: logout()
    System-->>User: logoutConfirmation
```

## Payment Processing Flow

```mermaid
sequenceDiagram
    actor Tenant
    participant System
    participant PaymentGateway
    actor Owner
    
    Tenant->>System: initiatePayment(bookingId)
    System-->>Tenant: paymentForm
    
    Tenant->>System: submitPayment(paymentDetails)
    System->>PaymentGateway: processTransaction(amount, details)
    
    PaymentGateway-->>System: transactionPending
    System-->>Tenant: processingStatus
    
    PaymentGateway->>System: transactionComplete(transactionId, status)
    
    alt Payment Successful
        System->>Tenant: paymentSuccess(receipt)
        System->>Owner: notifyPaymentReceived(amount)
        System->>System: updateBookingStatus(bookingId, "Confirmed")
    else Payment Failed
        System->>Tenant: paymentFailed(error)
        System->>System: logFailedTransaction(transactionId)
    end
```

## Search and Filter Interaction

```mermaid
sequenceDiagram
    actor User
    participant System
    
    User->>System: getSearchPage()
    System-->>User: searchInterface
    
    User->>System: searchProperties(location, priceRange)
    System-->>User: filteredResults
    
    User->>System: applyFilter(propertyType: "Apartment")
    System-->>User: refinedResults
    
    User->>System: sortResults("price_asc")
    System-->>User: sortedResults
    
    User->>System: viewProperty(propertyId)
    System-->>User: propertyDetails
```

## Maintenance Request Sequence

```mermaid
sequenceDiagram
    actor Tenant
    participant System
    actor Owner
    
    Tenant->>System: createMaintenanceRequest(propertyId, issue)
    System-->>Tenant: requestId
    System->>Owner: notifyMaintenanceRequest(requestId)
    
    Owner->>System: viewRequest(requestId)
    System-->>Owner: requestDetails
    
    Owner->>System: acknowledgeRequest(requestId, eta)
    System->>Tenant: notifyAcknowledgment(eta)
    
    Owner->>System: updateStatus(requestId, "In Progress")
    System->>Tenant: notifyStatusUpdate("In Progress")
    
    Owner->>System: completeRequest(requestId, notes)
    System->>Tenant: requestVerification(requestId)
    
    Tenant->>System: verifyCompletion(requestId, approved: true)
    System->>Owner: notifyVerification(requestId)
    System-->>Tenant: requestClosed
```
