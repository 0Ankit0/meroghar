import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/payments/payment_access.dart';

void main() {
  test('tenant billing stays available on mobile for renter roles', () {
    expect(canViewTenantBilling(const ['tenant']), isTrue);
    expect(canViewTenantBilling(const ['customer']), isTrue);
    expect(shouldUseWebsiteForBillingManagement(const ['tenant']), isFalse);
  });

  test('owner, manager, and admin billing management stay on the website', () {
    expect(canViewTenantBilling(const ['owner']), isFalse);
    expect(canViewTenantBilling(const ['property_manager']), isFalse);
    expect(canViewTenantBilling(const ['admin']), isFalse);
    expect(shouldUseWebsiteForBillingManagement(const ['owner']), isTrue);
    expect(shouldUseWebsiteForBillingManagement(const ['admin']), isTrue);
  });
}
