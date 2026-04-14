import { describe, expect, it } from 'vitest';

import {
  normalizeCategoryAttributeOptions,
  normalizeProperty,
  normalizePropertyAvailabilityResponse,
  normalizePropertyListResponse,
  normalizePropertyPriceQuote,
} from './properties';

describe('property helpers', () => {
  it('normalizes paginated property responses and nested previews', () => {
    const normalized = normalizePropertyListResponse({
      success: true,
      data: [
        {
          id: 'prop_1',
          name: 'Sunset Heights',
          category: { id: 'cat_apartment', name: 'Apartment', slug: 'apartment' },
          is_published: true,
          property_photos: [{ id: 'photo_1', url: 'https://example.com/photo.jpg', is_cover: true }],
          feature_values: [{ attribute_id: 'bedrooms', attribute_name: 'Bedrooms', value: 3 }],
          pricing_preview: { baseFee: 25000, totalDue: 31500, currency: 'NPR' },
        },
      ],
      meta: { page: 2, perPage: 1, total: 3 },
    });

    expect(normalized.page).toBe(2);
    expect(normalized.per_page).toBe(1);
    expect(normalized.total).toBe(3);
    expect(normalized.items[0]?.category?.slug).toBe('apartment');
    expect(normalized.items[0]?.photos?.[0]?.url).toBe('https://example.com/photo.jpg');
    expect(normalized.items[0]?.pricing_preview?.total_due).toBe(31500);
  });

  it('normalizes raw availability arrays into a predictable response', () => {
    const normalized = normalizePropertyAvailabilityResponse(
      [
        {
          id: 'block_1',
          block_type: 'manual',
          start_at: '2026-02-01T00:00:00Z',
          end_at: '2026-02-10T00:00:00Z',
          reason: 'Owner stay',
        },
      ],
      'prop_9'
    );

    expect(normalized.property_id).toBe('prop_9');
    expect(normalized.blocks).toHaveLength(1);
    expect(normalized.blocks[0]?.block_type).toBe('manual');
    expect(normalized.blocks[0]?.reason).toBe('Owner stay');
  });

  it('normalizes conflict-based availability responses and search item fallbacks', () => {
    const availability = normalizePropertyAvailabilityResponse({
      property_id: 'prop_2',
      is_available: false,
      conflicts: [
        {
          id: 'block_conflict',
          block_type: 'maintenance',
          start_at: '2026-03-01T00:00:00Z',
          end_at: '2026-03-02T00:00:00Z',
        },
      ],
    });
    const property = normalizeProperty({
      id: 'prop_public',
      property_type_id: 'cat_apartment',
      property_type_name: 'Apartment',
      property_type_slug: 'apartment',
      cover_photo_url: 'https://example.com/cover.jpg',
      starting_price: 35000,
      currency: 'NPR',
    });

    expect(availability.blocks[0]?.block_type).toBe('maintenance');
    expect(property.category?.name).toBe('Apartment');
    expect(property.photos?.[0]?.is_cover).toBe(true);
    expect(property.is_published).toBe(true);
    expect(property.pricing_preview?.total_due).toBe(35000);
  });

  it('normalizes pricing quotes and category attribute options', () => {
    const quote = normalizePropertyPriceQuote({
      baseFee: 10000,
      peakSurcharge: 500,
      discountAmount: 1000,
      taxAmount: 1200,
      depositAmount: 25000,
      totalDue: 35700,
      rateType: 'monthly',
    });
    const options = normalizeCategoryAttributeOptions([
      'furnished',
      { value: 'semi_furnished', label: 'Semi furnished' },
    ]);

    expect(quote.total_due).toBe(35700);
    expect(quote.rate_type).toBe('monthly');
    expect(options).toEqual([
      { label: 'Furnished', value: 'furnished' },
      { label: 'Semi furnished', value: 'semi_furnished' },
    ]);
  });

  it('falls back to due-now totals when that is the only quote total returned', () => {
    const quote = normalizePropertyPriceQuote({
      base_fee: 10000,
      total_due_now: 35000,
      deposit_amount: 25000,
      currency: 'NPR',
    });

    expect(quote.total_due).toBe(35000);
    expect(quote.deposit_amount).toBe(25000);
  });
});
