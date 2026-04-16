import { describe, expect, it } from 'vitest';
import {
  hasBillingManagementAccess,
  hasTenantBillingAccess,
  invoiceStatusTone,
  normalizeInvoiceListResponse,
  normalizeUtilityBillShareListResponse,
} from './finances';

describe('finance helpers', () => {
  it('normalizes invoice list responses nested in an envelope', () => {
    const normalized = normalizeInvoiceListResponse({
      success: true,
      data: {
        items: [
          {
            id: 'invoice_1',
            invoice_number: 'INV-2026-001',
            booking_id: 'booking_1',
            tenant_user_id: 'tenant_1',
            owner_user_id: 'owner_1',
            invoice_type: 'rent',
            currency: 'NPR',
            subtotal: 22000,
            tax_amount: 0,
            total_amount: 22000,
            paid_amount: 5000,
            outstanding_amount: 17000,
            status: 'partially_paid',
            due_date: '2026-05-01',
            line_items: [
              {
                id: 'line_1',
                invoice_id: 'invoice_1',
                line_item_type: 'rent',
                description: 'May rent',
                amount: 22000,
                tax_rate: 0,
                tax_amount: 0,
              },
            ],
            reminders: [
              {
                id: 'reminder_1',
                invoice_id: 'invoice_1',
                reminder_type: 't_minus_3',
                scheduled_for: '2026-04-28T00:00:00Z',
                status: 'scheduled',
              },
            ],
            payments: [
              {
                id: 'payment_1',
                reference_type: 'invoice',
                reference_id: 'invoice_1',
                payer_user_id: 'tenant_1',
                payment_method: 'khalti',
                status: 'completed',
                amount: 5000,
                currency: 'NPR',
                gateway_ref: 'gateway_1',
                is_offline: false,
                created_at: '2026-04-29T08:00:00Z',
              },
            ],
            created_at: '2026-04-20T08:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        has_more: false,
      },
    });

    expect(normalized.total).toBe(1);
    expect(normalized.items[0]?.invoice_number).toBe('INV-2026-001');
    expect(normalized.items[0]?.outstanding_amount).toBe(17000);
    expect(normalized.items[0]?.payments[0]?.payment_method).toBe('khalti');
  });

  it('normalizes utility bill share responses with nested bill metadata', () => {
    const normalized = normalizeUtilityBillShareListResponse({
      success: true,
      data: {
        items: [
          {
            split: {
              id: 'split_1',
              utility_bill_id: 'bill_1',
              tenant_user_id: 'tenant_1',
              invoice_id: 'invoice_2',
              split_method: 'equal',
              assigned_amount: 1800,
              paid_amount: 0,
              outstanding_amount: 1800,
              status: 'pending',
              due_at: '2026-05-05T00:00:00Z',
            },
            bill: {
              id: 'bill_1',
              property_id: 'property_1',
              created_by_user_id: 'owner_1',
              bill_type: 'water',
              billing_period_label: 'April 2026',
              period_start: '2026-04-01',
              period_end: '2026-04-30',
              due_date: '2026-05-05',
              total_amount: 3600,
              owner_subsidy_amount: 0,
              payable_amount: 3600,
              status: 'published',
              notes: 'Shared equally',
              attachments: [
                {
                  id: 'attachment_1',
                  utility_bill_id: 'bill_1',
                  file_url: 'https://example.com/bill.jpg',
                  file_type: 'image/jpeg',
                  checksum: 'checksum_1',
                  uploaded_at: '2026-04-30T11:00:00Z',
                },
              ],
              splits: [],
              created_at: '2026-04-30T10:00:00Z',
            },
            disputes: [
              {
                id: 'dispute_1',
                utility_bill_split_id: 'split_1',
                opened_by_user_id: 'tenant_1',
                status: 'open',
                reason: 'Meter reading mismatch',
                resolution_notes: '',
                opened_at: '2026-05-01T09:00:00Z',
              },
            ],
          },
        ],
        total: 1,
      },
    });

    expect(normalized.total).toBe(1);
    expect(normalized.items[0]?.bill.attachments[0]?.file_type).toBe('image/jpeg');
    expect(normalized.items[0]?.disputes[0]?.reason).toContain('Meter reading');
  });

  it('applies tenant and management billing role helpers', () => {
    expect(hasTenantBillingAccess(['tenant'])).toBe(true);
    expect(hasTenantBillingAccess(['owner'])).toBe(false);
    expect(hasBillingManagementAccess(['owner'])).toBe(true);
    expect(hasBillingManagementAccess(['property_manager'])).toBe(false);
    expect(invoiceStatusTone('overdue')).toContain('red');
  });
});
