import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/applications/data/models/booking.dart';
import 'package:mobile/features/applications/data/models/create_booking_request.dart';

void main() {
  test('booking models keep hashid ids and parse due-now totals', () {
    final booking = BookingRecord.fromJson(const {
      'id': 'booking_hash_01',
      'booking_number': 'BKG-1001',
      'status': 'confirmed',
      'property': {
        'id': 'prop_hash_01',
        'name': 'Sunrise Residency',
        'location_address': 'Jhamsikhel, Lalitpur',
      },
      'rental_start_at': '2026-05-01T00:00:00Z',
      'rental_end_at': '2026-06-01T00:00:00Z',
      'agreement_status': 'pending_tenant_signature',
      'pricing': {
        'currency': 'NPR',
        'base_fee': 32000,
        'tax_amount': 1600,
        'deposit_amount': 50000,
        'total_fee': 33600,
        'total_due_now': 83600,
      },
    });

    expect(booking.id, 'booking_hash_01');
    expect(booking.property.id, 'prop_hash_01');
    expect(booking.property.name, 'Sunrise Residency');
    expect(booking.pricing.totalFee, 33600);
    expect(booking.pricing.totalDueNow, 83600);
    expect(booking.agreementStatus, 'PENDING_CUSTOMER_SIGNATURE');
    expect(booking.displayReference, 'BKG-1001');
  });

  test('booking events humanize workflow milestones', () {
    final event = BookingEvent.fromJson(const {
      'id': 'evt_hash_01',
      'event_type': 'customer.signed',
      'created_at': '2026-05-03T10:00:00Z',
    });

    expect(event.id, 'evt_hash_01');
    expect(event.title, 'Tenant signed the lease');
  });

  test('create booking request serializes camelCase payload and idempotency header', () {
    final request = CreateBookingRequest(
      propertyId: 'prop_hash_02',
      rentalStartAt: DateTime.utc(2026, 7, 1),
      rentalEndAt: DateTime.utc(2026, 7, 31),
      specialRequests: 'Need furnished option',
      paymentMethodId: 'khalti',
      idempotencyKey: 'mobile-12345',
    );

    expect(request.toJson()['propertyId'], 'prop_hash_02');
    expect(request.toJson()['paymentMethodId'], 'khalti');
    expect(request.toJson()['specialRequests'], 'Need furnished option');
    expect(request.toHeaders()['Idempotency-Key'], 'mobile-12345');
  });
}
