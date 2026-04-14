import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/listings/data/models/listing_detail.dart';
import 'package:mobile/features/listings/data/models/listing_search.dart';
import 'package:mobile/features/listings/data/models/pricing_quote.dart';

void main() {
  test('listing search filters serialize search params', () {
    final filters = ListingSearchFilters(
      categoryId: 'cat_hashid_01',
      categorySlug: 'apartment',
      location: 'Lalitpur',
      minPrice: 15000,
      maxPrice: 35000,
      radiusKm: 5,
      period: ListingDateRange(
        start: DateTime(2025, 1, 10),
        end: DateTime(2025, 1, 20),
      ),
    );

    final params = filters.toQueryParameters();

    expect(params['category'], 'apartment');
    expect(params['location'], 'Lalitpur');
    expect(params['min_price'], 15000);
    expect(params['max_price'], 35000);
    expect(params['radius_km'], 5);
    expect(params['start'], contains('2025-01-10'));
    expect(params['end'], contains('2025-01-20'));
  });

  test('listing detail keeps string hashid ids and pricing overview', () {
    final detail = ListingDetail.fromJson(const {
      'id': 'prop_xYz123',
      'name': 'Sunrise Apartments',
      'description': 'Bright and airy apartment in Jhamsikhel',
      'location_address': 'Jhamsikhel, Lalitpur',
      'property_type': {
        'id': 'cat_hash_01',
        'name': 'Apartment',
        'slug': 'apartment',
      },
      'photos': [
        {
          'id': 'photo_hash_01',
          'url': 'https://example.com/property-1.jpg',
          'is_cover': true,
        },
      ],
      'features': {
        'bedrooms': 2,
        'bathrooms': 1,
        'furnishing_status': 'Furnished',
      },
      'amenities': ['Parking', 'Balcony'],
      'pricing': {
        'currency': 'NPR',
        'monthly_rate': 25000,
        'deposit_amount': 50000,
      },
    });

    expect(detail.id, 'prop_xYz123');
    expect(detail.category?.id, 'cat_hash_01');
    expect(detail.category?.slug, 'apartment');
    expect(detail.photos.first.id, 'photo_hash_01');
    expect(detail.pricingOverview.monthlyRate, 25000);
    expect(detail.depositAmount, 50000);
    expect(detail.amenities, ['Parking', 'Balcony']);
  });

  test('pricing quote parses flexible pricing fields', () {
    final quote = PricingQuote.fromJson(
      const {
        'property_id': 'prop_hashid_09',
        'monthly_rent': 30000,
        'service_fee': 1200,
        'tax': 3900,
        'security_deposit': 60000,
        'total': 35100,
        'currency': 'NPR',
      },
      requestedPeriod: ListingDateRange(
        start: DateTime(2025, 2, 1),
        end: DateTime(2025, 7, 31),
      ),
    );

    expect(quote.propertyId, 'prop_hashid_09');
    expect(quote.baseFee, 30000);
    expect(quote.serviceFee, 1200);
    expect(quote.taxAmount, 3900);
    expect(quote.depositAmount, 60000);
    expect(quote.totalFee, 35100);
    expect(quote.lineItems.length, 4);
  });
}
