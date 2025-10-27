"""
Demo Data Seeding Script for MeroGhar

This script populates the database with realistic demo data for testing and demonstration purposes.

Usage:
    python -m backend.scripts.seed_demo_data

Features:
- Creates sample owners, intermediaries, and tenants
- Generates properties with multiple units
- Creates payment history with various statuses
- Generates utility bills and allocations
- Creates expenses with categories
- Adds documents and messages
- Generates notifications

WARNING: This script will DELETE ALL EXISTING DATA before seeding.
Only run this in development/demo environments!
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from src.core.database import engine, SessionLocal
from src.core.security import get_password_hash
from src.models.user import User, UserRole
from src.models.property import Property, PropertyType, PropertyAssignment
from src.models.tenant import Tenant, TenantStatus
from src.models.payment import Payment, PaymentMethod, PaymentStatus, Transaction
from src.models.bill import Bill, BillType, BillStatus, BillAllocation, RecurringBill
from src.models.expense import Expense, ExpenseCategory, ExpenseStatus
from src.models.document import Document, DocumentType
from src.models.message import Message, MessageType, MessageStatus
from src.models.notification import Notification, NotificationType


# Demo data configuration
DEMO_PASSWORD = "Demo123!"  # Same password for all demo users

# Sample names
OWNER_NAMES = [
    "Rajesh Sharma",
    "Priya Thapa",
    "Anil Kumar",
]

INTERMEDIARY_NAMES = [
    "Sanjay Rai",
    "Sunita Gurung",
]

TENANT_NAMES = [
    "Amit Pandey", "Binita Shrestha", "Deepak Maharjan", "Isha Karki",
    "Kiran Tamang", "Laxmi Adhikari", "Manoj Bista", "Nisha Regmi",
    "Prakash Joshi", "Radha Poudel", "Suman Thapa", "Tara Magar",
]

PROPERTY_NAMES = [
    "Green Valley Apartments",
    "Sunrise Residency",
    "Himalaya Heights",
    "Peace Plaza",
]

ADDRESSES = [
    "Baneshwor, Kathmandu",
    "Thamel, Kathmandu",
    "Lazimpat, Kathmandu",
    "Patan Dhoka, Lalitpur",
]


def clear_all_data(db: Session):
    """Delete all data from all tables"""
    print("🗑️  Clearing existing data...")
    
    # Delete in correct order to respect foreign key constraints
    db.query(Notification).delete()
    db.query(Message).delete()
    db.query(Document).delete()
    db.query(Expense).delete()
    db.query(BillAllocation).delete()
    db.query(RecurringBill).delete()
    db.query(Bill).delete()
    db.query(Transaction).delete()
    db.query(Payment).delete()
    db.query(Tenant).delete()
    db.query(PropertyAssignment).delete()
    db.query(Property).delete()
    db.query(User).delete()
    
    db.commit()
    print("✅ All data cleared")


def create_users(db: Session) -> dict:
    """Create demo users (owners, intermediaries, tenants)"""
    print("\n👥 Creating users...")
    
    users = {
        "owners": [],
        "intermediaries": [],
        "tenants": [],
    }
    
    # Create owners
    for i, name in enumerate(OWNER_NAMES):
        email = f"owner{i+1}@meroghar.demo"
        user = User(
            email=email,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name=name,
            phone=f"+977-98{41000000 + i}",
            role=UserRole.OWNER,
            is_active=True,
            language_preference="en"
        )
        db.add(user)
        users["owners"].append(user)
        print(f"  ✓ Owner: {name} ({email})")
    
    # Create intermediaries
    for i, name in enumerate(INTERMEDIARY_NAMES):
        email = f"intermediary{i+1}@meroghar.demo"
        user = User(
            email=email,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name=name,
            phone=f"+977-98{42000000 + i}",
            role=UserRole.INTERMEDIARY,
            is_active=True,
            language_preference="en"
        )
        db.add(user)
        users["intermediaries"].append(user)
        print(f"  ✓ Intermediary: {name} ({email})")
    
    # Create tenants
    for i, name in enumerate(TENANT_NAMES):
        email = f"tenant{i+1}@meroghar.demo"
        user = User(
            email=email,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            full_name=name,
            phone=f"+977-98{43000000 + i}",
            role=UserRole.TENANT,
            is_active=True,
            language_preference="en"
        )
        db.add(user)
        users["tenants"].append(user)
        print(f"  ✓ Tenant: {name} ({email})")
    
    db.commit()
    
    # Refresh to get IDs
    for user in users["owners"] + users["intermediaries"] + users["tenants"]:
        db.refresh(user)
    
    return users


def create_properties(db: Session, users: dict) -> List[Property]:
    """Create demo properties"""
    print("\n🏢 Creating properties...")
    
    properties = []
    
    for i, (name, address) in enumerate(zip(PROPERTY_NAMES, ADDRESSES)):
        owner = users["owners"][i % len(users["owners"])]
        
        property = Property(
            name=name,
            address=address,
            total_units=random.randint(6, 12),
            property_type=random.choice([PropertyType.APARTMENT, PropertyType.HOUSE, PropertyType.COMMERCIAL]),
            description=f"Modern {name.lower()} in prime location with excellent amenities.",
            owner_id=owner.id
        )
        db.add(property)
        properties.append(property)
        print(f"  ✓ Property: {name} ({address}) - Owner: {owner.full_name}")
    
    db.commit()
    
    # Refresh to get IDs
    for property in properties:
        db.refresh(property)
    
    # Assign intermediaries to properties
    print("\n🔑 Assigning intermediaries to properties...")
    for i, property in enumerate(properties):
        intermediary = users["intermediaries"][i % len(users["intermediaries"])]
        
        assignment = PropertyAssignment(
            property_id=property.id,
            user_id=intermediary.id,
            role="INTERMEDIARY",
            permissions=["VIEW", "CREATE_TENANT", "RECORD_PAYMENT", "MANAGE_BILLS"]
        )
        db.add(assignment)
        print(f"  ✓ {intermediary.full_name} → {property.name}")
    
    db.commit()
    
    return properties


def create_tenants(db: Session, properties: List[Property], users: dict) -> List[Tenant]:
    """Create demo tenants"""
    print("\n🏠 Creating tenants...")
    
    tenants = []
    tenant_users = users["tenants"].copy()
    random.shuffle(tenant_users)
    
    tenant_idx = 0
    
    for property in properties:
        # Create 60-80% occupancy
        num_tenants = int(property.total_units * random.uniform(0.6, 0.8))
        
        for unit_num in range(1, num_tenants + 1):
            if tenant_idx >= len(tenant_users):
                break
            
            tenant_user = tenant_users[tenant_idx]
            tenant_idx += 1
            
            # Random move-in date in past 6 months
            move_in_date = datetime.now() - timedelta(days=random.randint(30, 180))
            monthly_rent = Decimal(random.choice([10000, 12000, 15000, 18000, 20000, 25000]))
            
            tenant = Tenant(
                property_id=property.id,
                user_id=tenant_user.id,
                unit_number=f"A-{unit_num:03d}",
                full_name=tenant_user.full_name,
                email=tenant_user.email,
                phone=tenant_user.phone,
                move_in_date=move_in_date.date(),
                monthly_rent=monthly_rent,
                security_deposit=monthly_rent * 2,
                billing_day=1,
                status=TenantStatus.ACTIVE,
                rent_increment_policy={
                    "increment_percentage": 5.0,
                    "increment_frequency_months": 24,
                    "notify_days_before": 30
                },
                rent_history=[
                    {
                        "effective_date": move_in_date.date().isoformat(),
                        "monthly_rent": float(monthly_rent),
                        "change_reason": "Initial rent"
                    }
                ]
            )
            db.add(tenant)
            tenants.append(tenant)
            print(f"  ✓ {tenant.full_name} - {property.name} ({tenant.unit_number}) - NPR {monthly_rent:,}/month")
    
    db.commit()
    
    # Refresh to get IDs
    for tenant in tenants:
        db.refresh(tenant)
    
    return tenants


def create_payments(db: Session, tenants: List[Tenant]):
    """Create demo payment history"""
    print("\n💰 Creating payments...")
    
    total_payments = 0
    
    for tenant in tenants:
        # Calculate months since move-in
        months_since_move_in = (datetime.now().date() - tenant.move_in_date).days // 30
        
        # Create payments for most months (90% payment rate)
        for month_offset in range(months_since_move_in, 0, -1):
            if random.random() < 0.9:  # 90% payment rate
                payment_date = datetime.now() - timedelta(days=month_offset * 30)
                
                # Vary payment method
                payment_method = random.choice([
                    PaymentMethod.CASH,
                    PaymentMethod.CASH,
                    PaymentMethod.BANK_TRANSFER,
                    PaymentMethod.KHALTI,
                    PaymentMethod.ESEWA,
                ])
                
                payment = Payment(
                    tenant_id=tenant.id,
                    amount=tenant.monthly_rent,
                    payment_method=payment_method,
                    payment_date=payment_date.date(),
                    status=PaymentStatus.COMPLETED,
                    notes=f"Rent payment for {payment_date.strftime('%B %Y')}",
                    receipt_number=f"REC-{payment_date.strftime('%Y%m')}-{tenant.id[:8]}"
                )
                db.add(payment)
                total_payments += 1
                
                # Create transaction for online payments
                if payment_method in [PaymentMethod.KHALTI, PaymentMethod.ESEWA, PaymentMethod.IMEPAY]:
                    db.flush()  # Get payment ID
                    transaction = Transaction(
                        payment_id=payment.id,
                        gateway=payment_method.value,
                        gateway_transaction_id=f"{payment_method.value.upper()}-{random.randint(100000, 999999)}",
                        amount=tenant.monthly_rent,
                        status="SUCCESS",
                        gateway_response={"status": "success", "message": "Payment completed"}
                    )
                    db.add(transaction)
    
    db.commit()
    print(f"  ✓ Created {total_payments} payments")


def create_bills(db: Session, properties: List[Property], tenants: List[Tenant]):
    """Create demo utility bills"""
    print("\n📄 Creating utility bills...")
    
    total_bills = 0
    
    for property in properties:
        property_tenants = [t for t in tenants if t.property_id == property.id]
        
        if not property_tenants:
            continue
        
        # Create bills for past 3 months
        for month_offset in range(3):
            bill_date = datetime.now() - timedelta(days=month_offset * 30)
            
            # Create electricity bill
            electricity_bill = Bill(
                property_id=property.id,
                bill_type=BillType.ELECTRICITY,
                total_amount=Decimal(random.randint(8000, 15000)),
                billing_period_start=(bill_date - timedelta(days=30)).date(),
                billing_period_end=bill_date.date(),
                due_date=(bill_date + timedelta(days=5)).date(),
                status=BillStatus.ALLOCATED,
                notes=f"Electricity bill for {bill_date.strftime('%B %Y')}"
            )
            db.add(electricity_bill)
            db.flush()
            
            # Allocate to tenants (equal split)
            allocation_percentage = Decimal(100) / len(property_tenants)
            for tenant in property_tenants:
                allocation_amount = (electricity_bill.total_amount * allocation_percentage / 100).quantize(Decimal('0.01'))
                
                allocation = BillAllocation(
                    bill_id=electricity_bill.id,
                    tenant_id=tenant.id,
                    percentage=allocation_percentage,
                    amount=allocation_amount,
                    status="PAID" if month_offset > 0 else "UNPAID"
                )
                db.add(allocation)
            
            total_bills += 1
            
            # Create water bill
            water_bill = Bill(
                property_id=property.id,
                bill_type=BillType.WATER,
                total_amount=Decimal(random.randint(2000, 4000)),
                billing_period_start=(bill_date - timedelta(days=30)).date(),
                billing_period_end=bill_date.date(),
                due_date=(bill_date + timedelta(days=5)).date(),
                status=BillStatus.ALLOCATED,
                notes=f"Water bill for {bill_date.strftime('%B %Y')}"
            )
            db.add(water_bill)
            db.flush()
            
            # Allocate to tenants
            for tenant in property_tenants:
                allocation_amount = (water_bill.total_amount * allocation_percentage / 100).quantize(Decimal('0.01'))
                allocation = BillAllocation(
                    bill_id=water_bill.id,
                    tenant_id=tenant.id,
                    percentage=allocation_percentage,
                    amount=allocation_amount,
                    status="PAID" if month_offset > 0 else "UNPAID"
                )
                db.add(allocation)
            
            total_bills += 1
    
    db.commit()
    print(f"  ✓ Created {total_bills} utility bills")


def create_expenses(db: Session, properties: List[Property], users: dict):
    """Create demo expenses"""
    print("\n💸 Creating expenses...")
    
    total_expenses = 0
    
    for property in properties:
        # Create 5-10 expenses per property
        num_expenses = random.randint(5, 10)
        
        for _ in range(num_expenses):
            expense_date = datetime.now() - timedelta(days=random.randint(1, 90))
            
            category = random.choice([
                ExpenseCategory.MAINTENANCE,
                ExpenseCategory.REPAIRS,
                ExpenseCategory.INSURANCE,
                ExpenseCategory.PROPERTY_TAX,
                ExpenseCategory.UTILITIES,
                ExpenseCategory.CLEANING,
            ])
            
            amount = Decimal(random.randint(1000, 10000))
            
            expense = Expense(
                property_id=property.id,
                category=category,
                amount=amount,
                expense_date=expense_date.date(),
                description=f"{category.value} expense for {property.name}",
                receipt_url=f"https://s3.example.com/receipts/{expense_date.strftime('%Y%m%d')}.pdf",
                paid_by="OWNER",
                created_by=property.owner_id,
                status=ExpenseStatus.APPROVED if random.random() < 0.8 else ExpenseStatus.PENDING_APPROVAL
            )
            db.add(expense)
            total_expenses += 1
    
    db.commit()
    print(f"  ✓ Created {total_expenses} expenses")


def create_documents(db: Session, tenants: List[Tenant]):
    """Create demo documents"""
    print("\n📎 Creating documents...")
    
    total_documents = 0
    
    for tenant in tenants:
        # Lease agreement
        lease_expiry = tenant.move_in_date + timedelta(days=365)
        lease_doc = Document(
            tenant_id=tenant.id,
            property_id=tenant.property_id,
            document_type=DocumentType.LEASE,
            file_url=f"https://s3.example.com/documents/lease_{tenant.id}.pdf",
            file_name=f"lease_agreement_{tenant.full_name.replace(' ', '_')}.pdf",
            file_size=1048576,
            expiration_date=lease_expiry,
            uploaded_by=tenant.user_id
        )
        db.add(lease_doc)
        total_documents += 1
        
        # ID proof (50% of tenants)
        if random.random() < 0.5:
            id_doc = Document(
                tenant_id=tenant.id,
                property_id=tenant.property_id,
                document_type=DocumentType.ID_PROOF,
                file_url=f"https://s3.example.com/documents/id_{tenant.id}.pdf",
                file_name=f"citizenship_{tenant.full_name.replace(' ', '_')}.pdf",
                file_size=524288,
                uploaded_by=tenant.user_id
            )
            db.add(id_doc)
            total_documents += 1
    
    db.commit()
    print(f"  ✓ Created {total_documents} documents")


def create_messages(db: Session, tenants: List[Tenant], users: dict):
    """Create demo messages"""
    print("\n💬 Creating messages...")
    
    total_messages = 0
    
    # Select random tenants for reminders
    reminder_tenants = random.sample(tenants, min(5, len(tenants)))
    
    for tenant in reminder_tenants:
        # Get property owner
        owner_id = None
        for owner in users["owners"]:
            # Find if this owner owns the tenant's property
            # (simplified - in real scenario, would query through property)
            owner_id = owner.id
            break
        
        message = Message(
            tenant_id=tenant.id,
            sent_by=owner_id,
            message_type=MessageType.SMS,
            content=f"Reminder: Your rent of NPR {tenant.monthly_rent:,} is due on the 1st of next month. Please ensure timely payment. Thank you!",
            status=MessageStatus.SENT,
            sent_at=datetime.now() - timedelta(days=random.randint(1, 10))
        )
        db.add(message)
        total_messages += 1
    
    db.commit()
    print(f"  ✓ Created {total_messages} messages")


def create_notifications(db: Session, users: dict, tenants: List[Tenant]):
    """Create demo notifications"""
    print("\n🔔 Creating notifications...")
    
    total_notifications = 0
    
    # Payment notifications for owners
    for owner in users["owners"]:
        notification = Notification(
            user_id=owner.id,
            title="Payment Received",
            body=f"Tenant {random.choice(tenants).full_name} has paid rent of NPR 15,000",
            notification_type=NotificationType.PAYMENT,
            is_read=random.choice([True, False]),
            data={"amount": 15000}
        )
        db.add(notification)
        total_notifications += 1
    
    # Bill notifications for tenants
    for tenant in random.sample(tenants, min(3, len(tenants))):
        notification = Notification(
            user_id=tenant.user_id,
            title="New Bill Allocation",
            body=f"Your electricity bill share is NPR 800. Due date: {(datetime.now() + timedelta(days=5)).strftime('%b %d')}",
            notification_type=NotificationType.BILL,
            is_read=False,
            data={"amount": 800, "bill_type": "ELECTRICITY"}
        )
        db.add(notification)
        total_notifications += 1
    
    # Document expiration notifications
    for tenant in random.sample(tenants, min(2, len(tenants))):
        notification = Notification(
            user_id=tenant.user_id,
            title="Document Expiring Soon",
            body=f"Your lease agreement will expire in 30 days. Please contact your landlord.",
            notification_type=NotificationType.DOCUMENT,
            is_read=False,
            data={"document_type": "LEASE"}
        )
        db.add(notification)
        total_notifications += 1
    
    db.commit()
    print(f"  ✓ Created {total_notifications} notifications")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 MeroGhar Demo Data Seeding Script")
    print("=" * 60)
    print(f"\n⚠️  WARNING: This will DELETE ALL existing data!")
    print(f"Demo password for all users: {DEMO_PASSWORD}")
    
    # Confirm before proceeding
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Seeding cancelled")
        return
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_all_data(db)
        
        # Seed data
        users = create_users(db)
        properties = create_properties(db, users)
        tenants = create_tenants(db, properties, users)
        create_payments(db, tenants)
        create_bills(db, properties, tenants)
        create_expenses(db, properties, users)
        create_documents(db, tenants)
        create_messages(db, tenants, users)
        create_notifications(db, users, tenants)
        
        print("\n" + "=" * 60)
        print("✅ Demo data seeding completed successfully!")
        print("=" * 60)
        
        print("\n📊 Summary:")
        print(f"  • Owners: {len(users['owners'])}")
        print(f"  • Intermediaries: {len(users['intermediaries'])}")
        print(f"  • Tenants: {len(users['tenants'])}")
        print(f"  • Properties: {len(properties)}")
        print(f"  • Active tenant leases: {len(tenants)}")
        
        print("\n🔑 Demo Login Credentials:")
        print(f"  Password for all accounts: {DEMO_PASSWORD}")
        print("\n  Owners:")
        for i, owner in enumerate(users['owners']):
            print(f"    • {owner.email}")
        print("\n  Intermediaries:")
        for inter in users['intermediaries']:
            print(f"    • {inter.email}")
        print("\n  Tenants:")
        for tenant in users['tenants'][:3]:  # Show first 3
            print(f"    • {tenant.email}")
        print(f"    ... and {len(users['tenants']) - 3} more tenants")
        
        print("\n💡 Next Steps:")
        print("  1. Start the API server: uvicorn src.main:app --reload")
        print("  2. Login with any of the demo accounts above")
        print("  3. Explore the MeroGhar features!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
