import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/applications/data/models/booking.dart';
import 'package:mobile/features/applications/presentation/providers/booking_provider.dart';
import 'package:mobile/features/auth/data/models/user.dart';
import 'package:mobile/features/auth/presentation/providers/auth_provider.dart';
import 'package:mobile/features/payments/data/models/billing.dart';
import 'package:mobile/features/payments/data/models/payment.dart';
import 'package:mobile/features/payments/presentation/pages/payments_page.dart';
import 'package:mobile/features/payments/presentation/providers/payment_provider.dart';

class _TestAuthNotifier extends AuthNotifier {
  _TestAuthNotifier(this._authState);

  final AuthState _authState;

  @override
  Future<AuthState> build() async => _authState;
}

AuthState _authStateForRoles(List<String> roles, {bool isSuperuser = false}) {
  return AuthState(
    user: User(
      id: 'user_1',
      username: 'billing-user',
      email: 'billing@example.com',
      isConfirmed: true,
      isActive: true,
      isSuperuser: isSuperuser,
      roles: roles,
    ),
    isAuthenticated: true,
  );
}

void main() {
  testWidgets('payments page renders tenant billing sections', (tester) async {
    final invoice = InvoiceSummary(
      id: 'inv_1',
      invoiceNumber: 'INV-2024-09',
      bookingId: 'book_1',
      tenantUserId: 'tenant_1',
      ownerUserId: 'owner_1',
      invoiceType: InvoiceType.rent,
      currency: 'NPR',
      subtotal: 20000,
      taxAmount: 0,
      totalAmount: 20000,
      paidAmount: 0,
      outstandingAmount: 20000,
      status: InvoiceStatus.sent,
      dueDate: DateTime(2024, 9, 5),
      periodStart: DateTime(2024, 9, 1),
      periodEnd: DateTime(2024, 9, 30),
    );

    final share = UtilityBillShare(
      split: const UtilityBillSplit(
        id: 'share_1',
        utilityBillId: 'bill_1',
        tenantUserId: 'tenant_1',
        invoiceId: 'inv_bill_1',
        splitMethod: UtilityBillSplitMethod.equal,
        assignedAmount: 1500,
        paidAmount: 0,
        outstandingAmount: 1500,
        status: UtilityBillSplitStatus.pending,
      ),
      bill: UtilityBill(
        id: 'bill_1',
        propertyId: 'prop_1',
        createdByUserId: 'owner_1',
        billType: UtilityBillType.electricity,
        billingPeriodLabel: 'Aug 2024',
        dueDate: DateTime(2024, 9, 10),
        totalAmount: 3000,
        ownerSubsidyAmount: 0,
        payableAmount: 3000,
        status: UtilityBillStatus.published,
        notes: 'Meter photo attached',
      ),
    );

    const booking = BookingRecord(
      id: 'book_1',
      bookingNumber: 'BK-1001',
      status: 'ACTIVE',
      property: BookingPropertyRef(
        id: 'prop_1',
        name: 'Sunrise Apartments',
        locationAddress: 'Kathmandu',
      ),
      pricing: BookingPricing(
        currency: 'NPR',
        baseFee: 20000,
        peakSurcharge: 0,
        taxAmount: 0,
        totalFee: 20000,
        depositAmount: 0,
        totalDueNow: 20000,
      ),
    );

    const transaction = PaymentTransaction(
      id: 'txn_1',
      provider: PaymentProvider.khalti,
      status: PaymentStatus.completed,
      amount: 2000000,
      currency: 'NPR',
      purchaseOrderId: 'INV-2024-09',
      purchaseOrderName: 'Invoice INV-2024-09',
      returnUrl: 'http://localhost:3000/payment-callback',
      websiteUrl: 'http://localhost:3000',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authNotifierProvider.overrideWith(
            () => _TestAuthNotifier(_authStateForRoles(const ['tenant'])),
          ),
          invoicesProvider.overrideWith((ref) => [invoice]),
          tenantBillSharesProvider.overrideWith((ref) => [share]),
          transactionsProvider.overrideWith((ref) => [transaction]),
          bookingsProvider.overrideWith((ref) => [booking]),
        ],
        child: const MaterialApp(home: PaymentsPage()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Tenant billing'), findsOneWidget);
    expect(find.text('Invoice INV-2024-09'), findsOneWidget);
    expect(find.text('Sunrise Apartments'), findsOneWidget);

    await tester.scrollUntilVisible(find.textContaining('Electricity'), 300);
    expect(find.textContaining('Electricity'), findsOneWidget);

    await tester.scrollUntilVisible(find.text('Transaction history'), 300);
    expect(find.text('Transaction history'), findsOneWidget);
  });

  testWidgets('payments page keeps billing management on the website for non-tenants',
      (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authNotifierProvider.overrideWith(
            () => _TestAuthNotifier(_authStateForRoles(const ['owner'])),
          ),
        ],
        child: const MaterialApp(home: PaymentsPage()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Tenant billing stays on mobile'), findsOneWidget);
    expect(
      find.textContaining('Use the website for owner and admin billing management'),
      findsOneWidget,
    );
  });
}
