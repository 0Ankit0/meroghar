import { describe, expect, it } from 'vitest';
import {
  agreementStatusTone,
  canCreateBooking,
  hasBookingManagementAccess,
  normalizeBookingListResponse,
  normalizeRentalAgreement,
} from './bookings';

describe('booking helpers', () => {
  it('normalizes paginated booking responses', () => {
    const normalized = normalizeBookingListResponse({
      success: true,
      data: {
        items: [
          {
            id: 'booking_1',
            booking_number: 'BKG-001',
            status: 'pending',
            property: {
              id: 'property_1',
              name: 'Sunrise Residency',
              location_address: 'Lalitpur',
            },
            tenant_user_id: 'tenant_1',
            owner_user_id: 'owner_1',
            rental_start_at: '2026-04-20T10:00:00Z',
            rental_end_at: '2026-05-20T10:00:00Z',
            pricing: {
              currency: 'NPR',
              base_fee: 28000,
              total_fee: 31500,
              deposit_amount: 25000,
              total_due_now: 56500,
            },
            cancellation_policy: {
              name: 'Standard',
              free_cancellation_hours: 72,
              partial_refund_hours: 24,
              partial_refund_percent: 50,
            },
          },
        ],
        total: 3,
        page: 2,
        per_page: 1,
        has_more: true,
      },
    });

    expect(normalized.total).toBe(3);
    expect(normalized.page).toBe(2);
    expect(normalized.per_page).toBe(1);
    expect(normalized.has_more).toBe(true);
    expect(normalized.items[0]?.property.name).toBe('Sunrise Residency');
    expect(normalized.items[0]?.pricing.total_due_now).toBe(56500);
  });

  it('normalizes agreement responses nested in an envelope', () => {
    const agreement = normalizeRentalAgreement({
      success: true,
      data: {
        agreement: {
          id: 'agreement_1',
          booking_id: 'booking_1',
          status: 'pending_owner_signature',
          template: {
            id: 'template_1',
            property_type_id: 'category_1',
            name: 'Residential lease',
            version: 3,
          },
          rendered_content: 'Lease body',
          custom_clauses: ['No smoking', 'Two months notice'],
          rendered_document_url: 'https://example.com/draft.pdf',
          version: 2,
          created_at: '2026-04-16T09:00:00Z',
        },
      },
    });

    expect(agreement.status).toBe('pending_owner_signature');
    expect(agreement.template.name).toBe('Residential lease');
    expect(agreement.custom_clauses).toEqual(['No smoking', 'Two months notice']);
  });

  it('applies booking role helpers and agreement tone helpers', () => {
    expect(canCreateBooking(['tenant'])).toBe(true);
    expect(canCreateBooking(['owner'])).toBe(false);
    expect(hasBookingManagementAccess(['admin'])).toBe(true);
    expect(agreementStatusTone('pending_owner_signature')).toContain('blue');
  });
});
