import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/applications/application_access.dart';

void main() {
  test('tenant roles can view, submit, and sign lease workflows on mobile', () {
    expect(canViewApplications(const ['tenant']), isTrue);
    expect(canSubmitApplications(const ['tenant']), isTrue);
    expect(canSignLeaseAgreement(const ['tenant']), isTrue);
    expect(canManageApplications(const ['tenant']), isFalse);
    expect(canManageAgreements(const ['tenant']), isFalse);
  });

  test('owner and admin application workflows stay on the website', () {
    expect(canViewApplications(const ['owner']), isFalse);
    expect(canViewApplications(const ['admin']), isFalse);
    expect(canManageApplications(const ['owner']), isFalse);
    expect(canManageAgreements(const ['admin']), isFalse);
  });
}
