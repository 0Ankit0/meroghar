# PowerShell script to create all required directories for Meroghar mobile app
# Run this from the mobile/lib directory

Write-Host "Creating Meroghar Mobile App Directory Structure..." -ForegroundColor Cyan
Write-Host ""

$baseDir = Get-Location

# Define all directories to create
$directories = @(
    # Screens
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
    
    # Widgets
    "widgets\common",
    "widgets\charts",
    "widgets\forms",
    
    # Utils
    "utils\helpers",
    "utils\validators",
    "utils\formatters",
    
    # Models
    "models\property",
    "models\tenant",
    "models\payment",
    "models\bill",
    "models\expense",
    "models\document",
    "models\message",
    "models\notification",
    
    # Providers
    "providers\property",
    "providers\tenant",
    "providers\payment",
    "providers\bill",
    "providers\expense",
    
    # Services
    "services\local",
    "services\sync",
    "services\payment_gateway"
)

$created = 0
$skipped = 0

foreach ($dir in $directories) {
    $fullPath = Join-Path $baseDir $dir
    
    if (Test-Path $fullPath) {
        Write-Host "  [SKIP] $dir (already exists)" -ForegroundColor Yellow
        $skipped++
    } else {
        try {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "  [OK]   $dir" -ForegroundColor Green
            $created++
        } catch {
            Write-Host "  [FAIL] $dir - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Created: $created directories" -ForegroundColor Green
Write-Host "  Skipped: $skipped directories" -ForegroundColor Yellow
Write-Host ""
Write-Host "Directory structure setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review DIRECTORY_SETUP.md for screen files to create"
Write-Host "  2. Review SETUP.md for running the application"
Write-Host "  3. Run 'flutter pub get' to install dependencies"
Write-Host "  4. Start backend with 'docker-compose up -d' from project root"
Write-Host "  5. Run app with 'flutter run'"
Write-Host ""

# Ask to create placeholder files
$createPlaceholders = Read-Host "Do you want to create placeholder screen files? (y/n)"

if ($createPlaceholders -eq 'y' -or $createPlaceholders -eq 'Y') {
    Write-Host ""
    Write-Host "Creating placeholder files..." -ForegroundColor Cyan
    
    $placeholderTemplate = @"
/// TODO: Implement this screen
/// 
/// This is a placeholder file. Replace with actual implementation.
library;

import 'package:flutter/material.dart';

class PlaceholderWidget extends StatelessWidget {
  const PlaceholderWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Text('TODO: Implement this screen'),
      ),
    );
  }
}
"@

    $screenFiles = @{
        "screens\properties\property_list_screen.dart" = "PropertyListScreen"
        "screens\properties\property_detail_screen.dart" = "PropertyDetailScreen"
        "screens\properties\property_form_screen.dart" = "PropertyFormScreen"
        "screens\tenants\tenant_list_screen.dart" = "TenantListScreen"
        "screens\tenants\tenant_detail_screen.dart" = "TenantDetailScreen"
        "screens\tenants\tenant_form_screen.dart" = "TenantFormScreen"
        "screens\payments\payment_list_screen.dart" = "PaymentListScreen"
        "screens\payments\payment_form_screen.dart" = "PaymentFormScreen"
        "screens\payments\payment_receipt_screen.dart" = "PaymentReceiptScreen"
        "screens\bills\bill_list_screen.dart" = "BillListScreen"
        "screens\bills\bill_form_screen.dart" = "BillFormScreen"
        "screens\bills\bill_allocation_screen.dart" = "BillAllocationScreen"
        "screens\expenses\expense_list_screen.dart" = "ExpenseListScreen"
        "screens\expenses\expense_form_screen.dart" = "ExpenseFormScreen"
        "screens\expenses\expense_detail_screen.dart" = "ExpenseDetailScreen"
        "screens\documents\document_list_screen.dart" = "DocumentListScreen"
        "screens\documents\document_upload_screen.dart" = "DocumentUploadScreen"
        "screens\documents\document_viewer_screen.dart" = "DocumentViewerScreen"
        "screens\messages\message_list_screen.dart" = "MessageListScreen"
        "screens\messages\message_compose_screen.dart" = "MessageComposeScreen"
        "screens\reports\report_list_screen.dart" = "ReportListScreen"
        "screens\reports\report_generate_screen.dart" = "ReportGenerateScreen"
        "screens\analytics\analytics_dashboard_screen.dart" = "AnalyticsDashboardScreen"
    }
    
    $filesCreated = 0
    foreach ($file in $screenFiles.Keys) {
        $fullPath = Join-Path $baseDir $file
        if (-not (Test-Path $fullPath)) {
            $content = $placeholderTemplate -replace "PlaceholderWidget", $screenFiles[$file]
            $content | Out-File -FilePath $fullPath -Encoding UTF8
            Write-Host "  [OK]   $file" -ForegroundColor Green
            $filesCreated++
        }
    }
    
    Write-Host ""
    Write-Host "Created $filesCreated placeholder files" -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup complete! Happy coding! 🚀" -ForegroundColor Green
