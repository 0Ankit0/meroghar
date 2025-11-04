# Complete Directory Structure Setup for Meroghar Mobile App

This document lists all directories that need to be created for the mobile app. Run the commands below based on your operating system.

## Windows (Command Prompt)

Run these commands in Command Prompt (cmd):

```cmd
cd D:\Projects\python\meroghar\mobile\lib

mkdir screens\dashboard
mkdir screens\properties
mkdir screens\tenants  
mkdir screens\payments
mkdir screens\bills
mkdir screens\expenses
mkdir screens\documents
mkdir screens\messages
mkdir screens\reports
mkdir screens\analytics
mkdir screens\sync
mkdir screens\users
mkdir screens\exports

mkdir widgets\common
mkdir widgets\charts
mkdir widgets\forms

mkdir utils\helpers
mkdir utils\validators
mkdir utils\formatters

mkdir models\property
mkdir models\tenant
mkdir models\payment
mkdir models\bill
mkdir models\expense
mkdir models\document
mkdir models\message
mkdir models\notification

mkdir providers\property
mkdir providers\tenant
mkdir providers\payment
mkdir providers\bill
mkdir providers\expense

mkdir services\local
mkdir services\sync
mkdir services\payment_gateway

echo Directory structure created successfully!
```

## macOS / Linux (Terminal)

Run these commands in Terminal:

```bash
cd ~/Projects/python/meroghar/mobile/lib

mkdir -p screens/{dashboard,properties,tenants,payments,bills,expenses,documents,messages,reports,analytics,sync,users,exports}
mkdir -p widgets/{common,charts,forms}
mkdir -p utils/{helpers,validators,formatters}
mkdir -p models/{property,tenant,payment,bill,expense,document,message,notification}
mkdir -p providers/{property,tenant,payment,bill,expense}
mkdir -p services/{local,sync,payment_gateway}

echo "Directory structure created successfully!"
```

## PowerShell (Windows)

Run these commands in PowerShell:

```powershell
cd D:\Projects\python\meroghar\mobile\lib

$directories = @(
    "screens\dashboard",
    "screens\properties",
    "screens\tenants",
    "screens\payments",
    "screens\bills",
    "screens\expenses",
    "screens\documents",
    "screens\messages",
    "screens\reports",
    "screens\analytics",
    "screens\sync",
    "screens\users",
    "screens\exports",
    "widgets\common",
    "widgets\charts",
    "widgets\forms",
    "utils\helpers",
    "utils\validators",
    "utils\formatters",
    "models\property",
    "models\tenant",
    "models\payment",
    "models\bill",
    "models\expense",
    "models\document",
    "models\message",
    "models\notification",
    "providers\property",
    "providers\tenant",
    "providers\payment",
    "providers\bill",
    "providers\expense",
    "services\local",
    "services\sync",
    "services\payment_gateway"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Write-Host "Created: $dir"
}

Write-Host "`nDirectory structure created successfully!" -ForegroundColor Green
```

## Verify Directory Structure

After creating directories, verify with:

**Windows:**
```cmd
tree /F lib
```

**macOS/Linux:**
```bash
tree lib
```

**PowerShell:**
```powershell
Get-ChildItem -Path lib -Recurse -Directory | Select-Object FullName
```

## Expected Directory Structure

```
lib/
├── config/
│   ├── constants.dart        ✅ Created
│   ├── env.dart              ✅ Created
│   └── env.example.dart      ✅ Exists
│
├── models/
│   ├── property/             🆕 Create
│   ├── tenant/               🆕 Create
│   ├── payment/              🆕 Create
│   ├── bill/                 🆕 Create
│   ├── expense/              🆕 Create
│   ├── document/             🆕 Create
│   ├── message/              🆕 Create
│   └── notification/         🆕 Create
│
├── providers/
│   ├── auth_provider.dart    ✅ Exists
│   ├── language_provider.dart ✅ Exists
│   ├── property/             🆕 Create
│   ├── tenant/               🆕 Create
│   ├── payment/              🆕 Create
│   ├── bill/                 🆕 Create
│   └── expense/              🆕 Create
│
├── screens/
│   ├── auth/                 ✅ Exists
│   ├── dashboard/            🆕 Create
│   ├── properties/           🆕 Create
│   ├── tenants/              🆕 Create
│   ├── payments/             🆕 Create
│   ├── bills/                🆕 Create
│   ├── expenses/             🆕 Create
│   ├── documents/            🆕 Create
│   ├── messages/             🆕 Create
│   ├── notifications/        ✅ Exists
│   ├── reports/              🆕 Create
│   ├── analytics/            🆕 Create
│   ├── settings/             ✅ Exists
│   ├── sync/                 🆕 Create
│   ├── users/                🆕 Create
│   ├── exports/              🆕 Create
│   └── home_screen.dart      ✅ Updated
│
├── services/
│   ├── api_service.dart      ✅ Exists
│   ├── secure_storage_service.dart ✅ Exists
│   ├── local/                🆕 Create
│   ├── sync/                 🆕 Create
│   └── payment_gateway/      🆕 Create
│
├── utils/
│   ├── helpers/              🆕 Create
│   ├── validators/           🆕 Create
│   └── formatters/           🆕 Create
│
├── widgets/
│   ├── common/               🆕 Create
│   ├── charts/               🆕 Create
│   └── forms/                🆕 Create
│
└── main.dart                 ✅ Exists
```

## Screen Files to Create

After creating directories, create these placeholder files:

### Properties Module
- `screens/properties/property_list_screen.dart`
- `screens/properties/property_detail_screen.dart`
- `screens/properties/property_form_screen.dart`

### Tenants Module
- `screens/tenants/tenant_list_screen.dart`
- `screens/tenants/tenant_detail_screen.dart`
- `screens/tenants/tenant_form_screen.dart`

### Payments Module
- `screens/payments/payment_list_screen.dart`
- `screens/payments/payment_form_screen.dart`
- `screens/payments/payment_receipt_screen.dart`

### Bills Module
- `screens/bills/bill_list_screen.dart`
- `screens/bills/bill_form_screen.dart`
- `screens/bills/bill_allocation_screen.dart`

### Expenses Module
- `screens/expenses/expense_list_screen.dart`
- `screens/expenses/expense_form_screen.dart`
- `screens/expenses/expense_detail_screen.dart`

### Documents Module
- `screens/documents/document_list_screen.dart`
- `screens/documents/document_upload_screen.dart`
- `screens/documents/document_viewer_screen.dart`

### Messages Module
- `screens/messages/message_list_screen.dart`
- `screens/messages/message_compose_screen.dart`
- `screens/messages/message_bulk_screen.dart`

### Reports Module
- `screens/reports/report_list_screen.dart`
- `screens/reports/report_generate_screen.dart`
- `screens/reports/report_view_screen.dart`

### Analytics Module
- `screens/analytics/analytics_dashboard_screen.dart`
- `screens/analytics/revenue_analytics_screen.dart`
- `screens/analytics/expense_analytics_screen.dart`

### Settings Module
- `screens/settings/settings_screen.dart` (already exists)
- `screens/settings/profile_settings_screen.dart`
- `screens/settings/notification_settings_screen.dart`
- `screens/settings/language_settings_screen.dart`
- `screens/settings/theme_settings_screen.dart`
- `screens/settings/sync_settings_screen.dart`
- `screens/settings/about_screen.dart`

## Quick Create All Screens Script

Save this as `create_screens.bat` (Windows) and run it:

```batch
@echo off
cd /d D:\Projects\python\meroghar\mobile\lib\screens

REM Properties
echo // TODO: Implement PropertyListScreen > properties\property_list_screen.dart
echo // TODO: Implement PropertyDetailScreen > properties\property_detail_screen.dart
echo // TODO: Implement PropertyFormScreen > properties\property_form_screen.dart

REM Tenants
echo // TODO: Implement TenantListScreen > tenants\tenant_list_screen.dart
echo // TODO: Implement TenantDetailScreen > tenants\tenant_detail_screen.dart
echo // TODO: Implement TenantFormScreen > tenants\tenant_form_screen.dart

REM Payments
echo // TODO: Implement PaymentListScreen > payments\payment_list_screen.dart
echo // TODO: Implement PaymentFormScreen > payments\payment_form_screen.dart
echo // TODO: Implement PaymentReceiptScreen > payments\payment_receipt_screen.dart

REM Bills
echo // TODO: Implement BillListScreen > bills\bill_list_screen.dart
echo // TODO: Implement BillFormScreen > bills\bill_form_screen.dart
echo // TODO: Implement BillAllocationScreen > bills\bill_allocation_screen.dart

echo Placeholder files created!
pause
```

## Next Steps

1. ✅ Run the directory creation commands above
2. ✅ Verify all directories exist
3. 🔄 Create placeholder screen files
4. 🔄 Implement each screen progressively
5. 🔄 Add navigation between screens
6. 🔄 Connect to backend API
7. 🔄 Add state management
8. 🔄 Implement offline sync

## Notes

- All constants are centralized in `lib/config/constants.dart`
- Environment configuration is in `lib/config/env.dart`
- API endpoints follow RESTful conventions
- Backend runs in Docker on `http://localhost:8000`
- Use `http://10.0.2.2:8000` for Android emulator
- Use `http://localhost:8000` for iOS simulator
