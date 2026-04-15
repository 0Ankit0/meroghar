import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/lease/data/models/lease_agreement.dart';

void main() {
  test('lease agreement normalizes tenant signature state and links', () {
    final agreement = LeaseAgreement.fromJson(const {
      'agreement': {
        'id': 'lease_hash_01',
        'booking_id': 'booking_hash_01',
        'status': 'pending_tenant_signature',
        'template': {
          'id': 'tmpl_hash_01',
          'name': 'Residential Lease',
        },
        'rendered_content': 'Lease preview',
        'customer_sign_url': 'https://example.com/sign',
        'rendered_document_url': 'https://example.com/lease-draft.pdf',
      },
    });

    expect(agreement.id, 'lease_hash_01');
    expect(agreement.bookingId, 'booking_hash_01');
    expect(agreement.status, 'PENDING_CUSTOMER_SIGNATURE');
    expect(agreement.customerSignUrl, 'https://example.com/sign');
    expect(agreement.primaryDocumentUrl, 'https://example.com/lease-draft.pdf');
    expect(agreement.needsCustomerSignature, isTrue);
  });
}
