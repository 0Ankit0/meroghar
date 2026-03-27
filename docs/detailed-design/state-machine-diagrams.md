# State Machine Diagrams

## Overview
State machine diagrams for the key stateful entities in the rental management system.

---

## Rental Application State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING : Tenant submits rental application + pays deposit

    PENDING --> CONFIRMED : Landlord approves (manual mode)
    PENDING --> CONFIRMED : Auto-confirmed (instant rental application mode)
    PENDING --> DECLINED : Landlord declines rental application
    PENDING --> CANCELLED : Tenant cancels before landlord reviews

    CONFIRMED --> ACTIVE : Rental start time reached + pre-rental assessment done
    CONFIRMED --> CANCELLED : Tenant or landlord cancels before rental starts

    ACTIVE --> PENDING_CLOSURE : Tenant initiates return
    ACTIVE --> ACTIVE : Rental Application modified (dates extended with approval)

    PENDING_CLOSURE --> CLOSED : Post-rental assessment completed + final invoice settled
    PENDING_CLOSURE --> ACTIVE : Late return detected - rental continues (fees applied)

    CANCELLED --> [*] : Refund processed per policy
    DECLINED --> [*] : Deposit refunded in full
    CLOSED --> [*] : Rental complete
```

---

## Property State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Landlord creates property

    DRAFT --> AVAILABLE : Landlord publishes listing

    AVAILABLE --> RENTED : Rental Application confirmed for property
    AVAILABLE --> UNDER_MAINTENANCE : Maintenance request logged
    AVAILABLE --> DRAFT : Landlord unpublishes

    RENTED --> ACTIVE_RENTAL : Rental period begins
    RENTED --> AVAILABLE : Rental Application cancelled before rental starts

    ACTIVE_RENTAL --> PENDING_RETURN : Tenant initiates return
    ACTIVE_RENTAL --> ACTIVE_RENTAL : Late return (overdue - stays active)

    PENDING_RETURN --> AVAILABLE : Return completed + assessment done + no maintenance needed
    PENDING_RETURN --> UNDER_MAINTENANCE : Post-rental assessment reveals damage

    UNDER_MAINTENANCE --> AVAILABLE : Maintenance approved and completed
    UNDER_MAINTENANCE --> RETIRED : Property deemed beyond repair

    AVAILABLE --> RETIRED : Landlord manually retires property
    RETIRED --> [*]
```

---

## Lease Agreement State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Landlord generates agreement from template

    DRAFT --> PENDING_CUSTOMER_SIGNATURE : Landlord sends for signature

    PENDING_CUSTOMER_SIGNATURE --> PENDING_OWNER_SIGNATURE : Tenant signs digitally
    PENDING_CUSTOMER_SIGNATURE --> DRAFT : Tenant requests amendment

    PENDING_OWNER_SIGNATURE --> SIGNED : Landlord countersigns
    PENDING_OWNER_SIGNATURE --> PENDING_CUSTOMER_SIGNATURE : Landlord requests amendment

    SIGNED --> AMENDED : Amendment issued and re-signed
    AMENDED --> SIGNED : Amendment fully signed

    SIGNED --> TERMINATED : Rental Application cancelled or rental closed
    AMENDED --> TERMINATED : Rental Application cancelled or rental closed

    TERMINATED --> [*]
```

---

## Security Deposit State Machine

```mermaid
stateDiagram-v2
    [*] --> HELD : Deposit collected on rental application confirmation

    HELD --> FULLY_REFUNDED : No damage, on-time return
    HELD --> PARTIALLY_REFUNDED : Damage deductions applied; remainder refunded
    HELD --> FULLY_DEDUCTED : Deductions equal or exceed deposit amount
    HELD --> DISPUTED : Tenant disputes proposed deductions

    DISPUTED --> PARTIALLY_REFUNDED : Dispute resolved; partial refund agreed
    DISPUTED --> FULLY_REFUNDED : Dispute upheld; all charges waived
    DISPUTED --> FULLY_DEDUCTED : Dispute rejected; full deduction upheld

    FULLY_REFUNDED --> [*]
    PARTIALLY_REFUNDED --> [*]
    FULLY_DEDUCTED --> [*]
```

---

## Maintenance Request State Machine

```mermaid
stateDiagram-v2
    [*] --> OPEN : Landlord or system logs maintenance request
    note right of OPEN : Property calendar blocked

    OPEN --> ASSIGNED : Landlord assigns to staff member

    ASSIGNED --> IN_PROGRESS : Staff accepts and starts work
    ASSIGNED --> OPEN : Staff declines - reassignment needed

    IN_PROGRESS --> COMPLETED : Staff marks task complete

    COMPLETED --> CLOSED : Landlord approves completion
    COMPLETED --> IN_PROGRESS : Landlord reopens with reason (rework needed)

    CLOSED --> [*]
    note right of CLOSED : Property calendar unblocked; cost logged
```

---

## Additional Charge State Machine

```mermaid
stateDiagram-v2
    [*] --> RAISED : Landlord raises additional charge post-rental

    RAISED --> ACCEPTED : Tenant accepts charge
    RAISED --> DISPUTED : Tenant disputes charge
    RAISED --> WAIVED : Landlord waives the charge

    DISPUTED --> ACCEPTED : Dispute rejected by landlord or admin; charge stands
    DISPUTED --> WAIVED : Dispute upheld; charge removed
    DISPUTED --> PARTIALLY_ACCEPTED : Admin mediates; partial charge agreed

    ACCEPTED --> PAID : Tenant pays the charge
    PARTIALLY_ACCEPTED --> PAID : Tenant pays the agreed partial amount

    PAID --> [*]
    WAIVED --> [*]
```

---

## Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Invoice auto-generated

    DRAFT --> SENT : Invoice dispatched to tenant

    SENT --> PARTIALLY_PAID : Partial payment received
    SENT --> PAID : Full payment received
    SENT --> OVERDUE : Due date passed with no payment

    PARTIALLY_PAID --> PAID : Remaining balance paid
    PARTIALLY_PAID --> OVERDUE : Due date passed with balance still outstanding

    OVERDUE --> PAID : Late payment (with late fee applied)

    PAID --> [*]
    SENT --> WAIVED : Landlord waives invoice (e.g., goodwill)
    WAIVED --> [*]
```
