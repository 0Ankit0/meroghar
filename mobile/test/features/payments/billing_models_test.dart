import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/payments/data/models/billing.dart';
import 'package:mobile/features/payments/data/models/payment.dart';

void main() {
  test('invoice models parse encoded ids and payment details', () {
    final invoice = InvoiceSummary.fromJson({
      'id': 'inv_a1',
      'invoice_number': 'INV-2024-09',
      'booking_id': 'book_7',
      'tenant_user_id': 'user_tenant',
      'owner_user_id': 'user_owner',
      'invoice_type': 'rent',
      'currency': 'NPR',
      'subtotal': 20000.0,
      'tax_amount': 0.0,
      'total_amount': 20000.0,
      'paid_amount': 5000.0,
      'outstanding_amount': 15000.0,
      'status': 'partially_paid',
      'due_date': '2024-09-05',
      'period_start': '2024-09-01',
      'period_end': '2024-09-30',
      'line_items': [
        {
          'id': 'line_1',
          'invoice_id': 'inv_a1',
          'line_item_type': 'rent',
          'description': 'September rent',
          'amount': 20000.0,
          'tax_rate': 0.0,
          'tax_amount': 0.0,
        },
      ],
      'payments': [
        {
          'id': 'pay_1',
          'reference_id': 'inv_a1',
          'payer_user_id': 'user_tenant',
          'payment_method': 'khalti',
          'status': 'completed',
          'amount': 5000.0,
          'currency': 'NPR',
          'gateway_ref': 'gw_1',
          'created_at': '2024-09-02T10:00:00',
        },
      ],
    });

    expect(invoice.id, 'inv_a1');
    expect(invoice.bookingId, 'book_7');
    expect(invoice.invoiceType, InvoiceType.rent);
    expect(invoice.status, InvoiceStatus.partiallyPaid);
    expect(invoice.canPay, isTrue);
    expect(invoice.canPartialPay, isTrue);
    expect(invoice.lineItems.single.description, 'September rent');
    expect(invoice.payments.single.paymentMethod, PaymentProvider.khalti);
  });

  test('utility bill share models capture disputes, attachments, and receipts',
      () {
    final share = UtilityBillShare.fromJson({
      'split': {
        'id': 'share_1',
        'utility_bill_id': 'bill_1',
        'tenant_user_id': 'user_tenant',
        'invoice_id': 'inv_bill_1',
        'split_method': 'equal',
        'assigned_amount': 1500.0,
        'paid_amount': 0.0,
        'outstanding_amount': 1500.0,
        'status': 'pending',
      },
      'bill': {
        'id': 'bill_1',
        'property_id': 'prop_1',
        'created_by_user_id': 'user_owner',
        'bill_type': 'electricity',
        'billing_period_label': 'Aug 2024',
        'due_date': '2024-09-10',
        'total_amount': 3000.0,
        'owner_subsidy_amount': 0.0,
        'payable_amount': 3000.0,
        'status': 'published',
        'notes': 'Meter photo attached',
        'attachments': [
          {
            'id': 'att_1',
            'utility_bill_id': 'bill_1',
            'file_url': 'https://example.com/bill.pdf',
            'file_type': 'application/pdf',
            'checksum': 'abc',
          },
        ],
      },
      'disputes': [
        {
          'id': 'disp_1',
          'utility_bill_split_id': 'share_1',
          'opened_by_user_id': 'user_tenant',
          'status': 'resolved',
          'reason': 'Reading seems too high',
          'resolution_notes': 'Verified with owner',
        },
      ],
    });

    expect(share.bill.billType, UtilityBillType.electricity);
    expect(share.bill.attachments.single.fileType, 'application/pdf');
    expect(share.latestDispute?.status, UtilityBillDisputeStatus.resolved);
    expect(share.canPay, isTrue);
    expect(share.canDispute, isTrue);
    expect(share.canShowReceipt, isFalse);
  });
}
