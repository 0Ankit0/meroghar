import '../../../../core/utils/json_parsing.dart';
import 'payment.dart';

String _normalizeBillingToken(String value) {
  return value
      .trim()
      .toLowerCase()
      .replaceAll(RegExp(r'[.\s-]+'), '_')
      .replaceAll(RegExp(r'_+'), '_');
}

String _readId(Map<String, dynamic> json, Iterable<String> keys) {
  final stringValue = readString(json, keys);
  if (stringValue != null) return stringValue;
  final intValue = readInt(json, keys);
  return intValue?.toString() ?? '';
}

String? _readOptionalId(Map<String, dynamic> json, Iterable<String> keys) {
  final value = _readId(json, keys);
  return value.isEmpty ? null : value;
}

Map<String, dynamic> _readMetadata(dynamic value) {
  return asJsonMap(value);
}

enum InvoiceType {
  rent,
  additionalCharge,
  utilityBillShare,
  other;

  static InvoiceType fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'rent':
        return InvoiceType.rent;
      case 'additional_charge':
        return InvoiceType.additionalCharge;
      case 'utility_bill_share':
        return InvoiceType.utilityBillShare;
      default:
        return InvoiceType.other;
    }
  }

  String get displayName {
    switch (this) {
      case InvoiceType.rent:
        return 'Rent';
      case InvoiceType.additionalCharge:
        return 'Additional charge';
      case InvoiceType.utilityBillShare:
        return 'Utility bill share';
      case InvoiceType.other:
        return 'Invoice';
    }
  }
}

enum InvoiceStatus {
  draft,
  sent,
  partiallyPaid,
  paid,
  overdue,
  waived;

  static InvoiceStatus fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'draft':
        return InvoiceStatus.draft;
      case 'sent':
        return InvoiceStatus.sent;
      case 'partially_paid':
        return InvoiceStatus.partiallyPaid;
      case 'paid':
        return InvoiceStatus.paid;
      case 'overdue':
        return InvoiceStatus.overdue;
      case 'waived':
        return InvoiceStatus.waived;
      default:
        return InvoiceStatus.sent;
    }
  }

  String get displayName {
    switch (this) {
      case InvoiceStatus.draft:
        return 'Draft';
      case InvoiceStatus.sent:
        return 'Sent';
      case InvoiceStatus.partiallyPaid:
        return 'Partially paid';
      case InvoiceStatus.paid:
        return 'Paid';
      case InvoiceStatus.overdue:
        return 'Overdue';
      case InvoiceStatus.waived:
        return 'Waived';
    }
  }
}

class InvoiceLineItem {
  final String id;
  final String invoiceId;
  final String lineItemType;
  final String description;
  final double amount;
  final double taxRate;
  final double taxAmount;
  final Map<String, dynamic> metadata;

  const InvoiceLineItem({
    required this.id,
    required this.invoiceId,
    required this.lineItemType,
    required this.description,
    required this.amount,
    required this.taxRate,
    required this.taxAmount,
    this.metadata = const <String, dynamic>{},
  });

  factory InvoiceLineItem.fromJson(Map<String, dynamic> json) {
    return InvoiceLineItem(
      id: _readId(json, const ['id']),
      invoiceId: _readId(json, const ['invoice_id', 'invoiceId']),
      lineItemType:
          readString(json, const ['line_item_type', 'lineItemType']) ??
              'charge',
      description: readString(json, const ['description']) ?? 'Charge',
      amount: readDouble(json, const ['amount']) ?? 0,
      taxRate: readDouble(json, const ['tax_rate', 'taxRate']) ?? 0,
      taxAmount: readDouble(json, const ['tax_amount', 'taxAmount']) ?? 0,
      metadata:
          _readMetadata(readValue(json, const ['metadata_json', 'metadata'])),
    );
  }
}

class InvoicePaymentRecord {
  final String id;
  final String referenceId;
  final String payerUserId;
  final PaymentProvider paymentMethod;
  final PaymentStatus status;
  final double amount;
  final String currency;
  final String gatewayRef;
  final Map<String, dynamic> gatewayResponse;
  final bool isOffline;
  final DateTime? createdAt;
  final DateTime? confirmedAt;

  const InvoicePaymentRecord({
    required this.id,
    required this.referenceId,
    required this.payerUserId,
    required this.paymentMethod,
    required this.status,
    required this.amount,
    required this.currency,
    required this.gatewayRef,
    this.gatewayResponse = const <String, dynamic>{},
    required this.isOffline,
    this.createdAt,
    this.confirmedAt,
  });

  factory InvoicePaymentRecord.fromJson(Map<String, dynamic> json) {
    return InvoicePaymentRecord(
      id: _readId(json, const ['id']),
      referenceId: _readId(json, const ['reference_id', 'referenceId']),
      payerUserId: _readId(json, const ['payer_user_id', 'payerUserId']),
      paymentMethod: PaymentProvider.fromString(
        readString(
                json, const ['payment_method', 'paymentMethod', 'provider']) ??
            'khalti',
      ),
      status: PaymentStatus.fromString(
        readString(json, const ['status']) ?? 'pending',
      ),
      amount: readDouble(json, const ['amount']) ?? 0,
      currency: readString(json, const ['currency']) ?? 'NPR',
      gatewayRef: readString(json, const ['gateway_ref', 'gatewayRef']) ?? '',
      gatewayResponse: _readMetadata(
        readValue(json, const ['gateway_response_json', 'gatewayResponse']),
      ),
      isOffline: readBool(json, const ['is_offline', 'isOffline']) ?? false,
      createdAt: readDateTime(json, const ['created_at', 'createdAt']),
      confirmedAt: readDateTime(json, const ['confirmed_at', 'confirmedAt']),
    );
  }
}

class InvoiceSummary {
  final String id;
  final String invoiceNumber;
  final String? bookingId;
  final String tenantUserId;
  final String ownerUserId;
  final InvoiceType invoiceType;
  final String currency;
  final double subtotal;
  final double taxAmount;
  final double totalAmount;
  final double paidAmount;
  final double outstandingAmount;
  final InvoiceStatus status;
  final DateTime? dueDate;
  final DateTime? periodStart;
  final DateTime? periodEnd;
  final Map<String, dynamic> metadata;
  final List<InvoiceLineItem> lineItems;
  final List<InvoicePaymentRecord> payments;
  final DateTime? createdAt;
  final DateTime? paidAt;

  const InvoiceSummary({
    required this.id,
    required this.invoiceNumber,
    this.bookingId,
    required this.tenantUserId,
    required this.ownerUserId,
    required this.invoiceType,
    required this.currency,
    required this.subtotal,
    required this.taxAmount,
    required this.totalAmount,
    required this.paidAmount,
    required this.outstandingAmount,
    required this.status,
    this.dueDate,
    this.periodStart,
    this.periodEnd,
    this.metadata = const <String, dynamic>{},
    this.lineItems = const <InvoiceLineItem>[],
    this.payments = const <InvoicePaymentRecord>[],
    this.createdAt,
    this.paidAt,
  });

  factory InvoiceSummary.fromJson(Map<String, dynamic> json) {
    return InvoiceSummary(
      id: _readId(json, const ['id']),
      invoiceNumber:
          readString(json, const ['invoice_number', 'invoiceNumber']) ?? '',
      bookingId: _readOptionalId(json, const ['booking_id', 'bookingId']),
      tenantUserId: _readId(json, const ['tenant_user_id', 'tenantUserId']),
      ownerUserId: _readId(json, const ['owner_user_id', 'ownerUserId']),
      invoiceType: InvoiceType.fromString(
        readString(json, const ['invoice_type', 'invoiceType']),
      ),
      currency: readString(json, const ['currency']) ?? 'NPR',
      subtotal: readDouble(json, const ['subtotal']) ?? 0,
      taxAmount: readDouble(json, const ['tax_amount', 'taxAmount']) ?? 0,
      totalAmount: readDouble(json, const ['total_amount', 'totalAmount']) ?? 0,
      paidAmount: readDouble(json, const ['paid_amount', 'paidAmount']) ?? 0,
      outstandingAmount:
          readDouble(json, const ['outstanding_amount', 'outstandingAmount']) ??
              0,
      status: InvoiceStatus.fromString(readString(json, const ['status'])),
      dueDate: readDateTime(json, const ['due_date', 'dueDate']),
      periodStart: readDateTime(json, const ['period_start', 'periodStart']),
      periodEnd: readDateTime(json, const ['period_end', 'periodEnd']),
      metadata:
          _readMetadata(readValue(json, const ['metadata_json', 'metadata'])),
      lineItems: readList(json, const ['line_items', 'lineItems'])
          .map((item) => InvoiceLineItem.fromJson(asJsonMap(item)))
          .toList(),
      payments: readList(json, const ['payments'])
          .map((item) => InvoicePaymentRecord.fromJson(asJsonMap(item)))
          .toList(),
      createdAt: readDateTime(json, const ['created_at', 'createdAt']),
      paidAt: readDateTime(json, const ['paid_at', 'paidAt']),
    );
  }

  bool get canPay =>
      outstandingAmount > 0.01 &&
      status != InvoiceStatus.paid &&
      status != InvoiceStatus.waived;

  bool get canPartialPay => canPay && outstandingAmount > 0.01;

  bool get canShowReceipt => paidAmount > 0.01;

  String get displayTitle =>
      invoiceNumber.isNotEmpty ? 'Invoice $invoiceNumber' : 'Invoice';
}

class InvoiceListResponse {
  final List<InvoiceSummary> items;
  final int total;
  final int page;
  final int perPage;
  final bool hasMore;

  const InvoiceListResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.perPage,
    required this.hasMore,
  });

  factory InvoiceListResponse.fromJson(Map<String, dynamic> json) {
    return InvoiceListResponse(
      items: readList(json, const ['items'])
          .map((item) => InvoiceSummary.fromJson(asJsonMap(item)))
          .toList(),
      total: readInt(json, const ['total']) ?? 0,
      page: readInt(json, const ['page']) ?? 1,
      perPage: readInt(json, const ['per_page', 'perPage']) ?? 20,
      hasMore: readBool(json, const ['has_more', 'hasMore']) ?? false,
    );
  }
}

class BillingPaymentRequest {
  final PaymentProvider provider;
  final double? amount;
  final String returnUrl;
  final String websiteUrl;
  final String? customerName;
  final String? customerEmail;
  final String? customerPhone;

  const BillingPaymentRequest({
    required this.provider,
    this.amount,
    required this.returnUrl,
    required this.websiteUrl,
    this.customerName,
    this.customerEmail,
    this.customerPhone,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'provider': provider.name,
      'return_url': returnUrl,
      'website_url': websiteUrl,
    };
    if (amount != null) map['amount'] = amount;
    if (customerName != null) map['customer_name'] = customerName;
    if (customerEmail != null) map['customer_email'] = customerEmail;
    if (customerPhone != null) map['customer_phone'] = customerPhone;
    return map;
  }
}

class AdditionalChargeSummary {
  final String id;
  final String description;
  final double amount;
  final String status;
  final String disputeReason;
  final String resolutionNotes;
  final DateTime? createdAt;
  final DateTime? resolvedAt;

  const AdditionalChargeSummary({
    required this.id,
    required this.description,
    required this.amount,
    required this.status,
    required this.disputeReason,
    required this.resolutionNotes,
    this.createdAt,
    this.resolvedAt,
  });

  factory AdditionalChargeSummary.fromJson(Map<String, dynamic> json) {
    return AdditionalChargeSummary(
      id: _readId(json, const ['id']),
      description:
          readString(json, const ['description']) ?? 'Additional charge',
      amount: readDouble(json, const ['amount']) ?? 0,
      status: readString(json, const ['status']) ?? 'raised',
      disputeReason:
          readString(json, const ['dispute_reason', 'disputeReason']) ?? '',
      resolutionNotes: readString(
            json,
            const ['resolution_notes', 'resolutionNotes'],
          ) ??
          '',
      createdAt: readDateTime(json, const ['created_at', 'createdAt']),
      resolvedAt: readDateTime(json, const ['resolved_at', 'resolvedAt']),
    );
  }

  String get displayStatus => titleFromKey(status);
}

class RentLedgerEntry {
  final DateTime? periodStart;
  final DateTime? periodEnd;
  final double amountDue;
  final String? invoiceId;
  final InvoiceStatus? invoiceStatus;
  final DateTime? dueDate;
  final double paidAmount;
  final double outstandingAmount;

  const RentLedgerEntry({
    this.periodStart,
    this.periodEnd,
    required this.amountDue,
    this.invoiceId,
    this.invoiceStatus,
    this.dueDate,
    required this.paidAmount,
    required this.outstandingAmount,
  });

  factory RentLedgerEntry.fromJson(Map<String, dynamic> json) {
    final statusValue =
        readString(json, const ['invoice_status', 'invoiceStatus']);
    return RentLedgerEntry(
      periodStart: readDateTime(json, const ['period_start', 'periodStart']),
      periodEnd: readDateTime(json, const ['period_end', 'periodEnd']),
      amountDue: readDouble(json, const ['amount_due', 'amountDue']) ?? 0,
      invoiceId: _readOptionalId(json, const ['invoice_id', 'invoiceId']),
      invoiceStatus:
          statusValue == null ? null : InvoiceStatus.fromString(statusValue),
      dueDate: readDateTime(json, const ['due_date', 'dueDate']),
      paidAmount: readDouble(json, const ['paid_amount', 'paidAmount']) ?? 0,
      outstandingAmount:
          readDouble(json, const ['outstanding_amount', 'outstandingAmount']) ??
              0,
    );
  }
}

class RentLedger {
  final String bookingId;
  final String currency;
  final List<RentLedgerEntry> entries;
  final List<AdditionalChargeSummary> additionalCharges;
  final double totalAmount;
  final double paidAmount;
  final double outstandingAmount;

  const RentLedger({
    required this.bookingId,
    required this.currency,
    required this.entries,
    this.additionalCharges = const <AdditionalChargeSummary>[],
    required this.totalAmount,
    required this.paidAmount,
    required this.outstandingAmount,
  });

  factory RentLedger.fromJson(Map<String, dynamic> json) {
    return RentLedger(
      bookingId: _readId(json, const ['booking_id', 'bookingId']),
      currency: readString(json, const ['currency']) ?? 'NPR',
      entries: readList(json, const ['entries'])
          .map((item) => RentLedgerEntry.fromJson(asJsonMap(item)))
          .toList(),
      additionalCharges: readList(
        json,
        const ['additional_charges', 'additionalCharges'],
      )
          .map((item) => AdditionalChargeSummary.fromJson(asJsonMap(item)))
          .toList(),
      totalAmount: readDouble(json, const ['total_amount', 'totalAmount']) ?? 0,
      paidAmount: readDouble(json, const ['paid_amount', 'paidAmount']) ?? 0,
      outstandingAmount:
          readDouble(json, const ['outstanding_amount', 'outstandingAmount']) ??
              0,
    );
  }
}

enum UtilityBillType {
  electricity,
  water,
  internet,
  gas,
  other;

  static UtilityBillType fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'electricity':
        return UtilityBillType.electricity;
      case 'water':
        return UtilityBillType.water;
      case 'internet':
        return UtilityBillType.internet;
      case 'gas':
        return UtilityBillType.gas;
      default:
        return UtilityBillType.other;
    }
  }

  String get displayName {
    switch (this) {
      case UtilityBillType.electricity:
        return 'Electricity';
      case UtilityBillType.water:
        return 'Water';
      case UtilityBillType.internet:
        return 'Internet';
      case UtilityBillType.gas:
        return 'Gas';
      case UtilityBillType.other:
        return 'Other utility';
    }
  }
}

enum UtilityBillStatus {
  draft,
  published,
  partiallyPaid,
  settled;

  static UtilityBillStatus fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'draft':
        return UtilityBillStatus.draft;
      case 'published':
        return UtilityBillStatus.published;
      case 'partially_paid':
        return UtilityBillStatus.partiallyPaid;
      case 'settled':
        return UtilityBillStatus.settled;
      default:
        return UtilityBillStatus.published;
    }
  }

  String get displayName {
    switch (this) {
      case UtilityBillStatus.draft:
        return 'Draft';
      case UtilityBillStatus.published:
        return 'Published';
      case UtilityBillStatus.partiallyPaid:
        return 'Partially paid';
      case UtilityBillStatus.settled:
        return 'Settled';
    }
  }
}

enum UtilityBillSplitMethod {
  single,
  equal,
  percentage,
  fixed,
  other;

  static UtilityBillSplitMethod fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'single':
        return UtilityBillSplitMethod.single;
      case 'equal':
        return UtilityBillSplitMethod.equal;
      case 'percentage':
        return UtilityBillSplitMethod.percentage;
      case 'fixed':
        return UtilityBillSplitMethod.fixed;
      default:
        return UtilityBillSplitMethod.other;
    }
  }

  String get displayName {
    switch (this) {
      case UtilityBillSplitMethod.single:
        return 'Single tenant';
      case UtilityBillSplitMethod.equal:
        return 'Equal split';
      case UtilityBillSplitMethod.percentage:
        return 'Percentage split';
      case UtilityBillSplitMethod.fixed:
        return 'Fixed split';
      case UtilityBillSplitMethod.other:
        return 'Split';
    }
  }
}

enum UtilityBillSplitStatus {
  pending,
  partiallyPaid,
  paid,
  disputed,
  waived;

  static UtilityBillSplitStatus fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'pending':
        return UtilityBillSplitStatus.pending;
      case 'partially_paid':
        return UtilityBillSplitStatus.partiallyPaid;
      case 'paid':
        return UtilityBillSplitStatus.paid;
      case 'disputed':
        return UtilityBillSplitStatus.disputed;
      case 'waived':
        return UtilityBillSplitStatus.waived;
      default:
        return UtilityBillSplitStatus.pending;
    }
  }

  String get displayName {
    switch (this) {
      case UtilityBillSplitStatus.pending:
        return 'Pending';
      case UtilityBillSplitStatus.partiallyPaid:
        return 'Partially paid';
      case UtilityBillSplitStatus.paid:
        return 'Paid';
      case UtilityBillSplitStatus.disputed:
        return 'Disputed';
      case UtilityBillSplitStatus.waived:
        return 'Waived';
    }
  }
}

enum UtilityBillDisputeStatus {
  open,
  resolved,
  rejected,
  waived;

  static UtilityBillDisputeStatus fromString(String? value) {
    switch (_normalizeBillingToken(value ?? '')) {
      case 'open':
        return UtilityBillDisputeStatus.open;
      case 'resolved':
        return UtilityBillDisputeStatus.resolved;
      case 'rejected':
        return UtilityBillDisputeStatus.rejected;
      case 'waived':
        return UtilityBillDisputeStatus.waived;
      default:
        return UtilityBillDisputeStatus.open;
    }
  }

  String get displayName {
    switch (this) {
      case UtilityBillDisputeStatus.open:
        return 'Open';
      case UtilityBillDisputeStatus.resolved:
        return 'Resolved';
      case UtilityBillDisputeStatus.rejected:
        return 'Rejected';
      case UtilityBillDisputeStatus.waived:
        return 'Waived';
    }
  }
}

class UtilityBillAttachment {
  final String id;
  final String utilityBillId;
  final String fileUrl;
  final String fileType;
  final String checksum;
  final DateTime? uploadedAt;

  const UtilityBillAttachment({
    required this.id,
    required this.utilityBillId,
    required this.fileUrl,
    required this.fileType,
    required this.checksum,
    this.uploadedAt,
  });

  factory UtilityBillAttachment.fromJson(Map<String, dynamic> json) {
    return UtilityBillAttachment(
      id: _readId(json, const ['id']),
      utilityBillId: _readId(json, const ['utility_bill_id', 'utilityBillId']),
      fileUrl: readString(json, const ['file_url', 'fileUrl']) ?? '',
      fileType: readString(json, const ['file_type', 'fileType']) ?? '',
      checksum: readString(json, const ['checksum']) ?? '',
      uploadedAt: readDateTime(json, const ['uploaded_at', 'uploadedAt']),
    );
  }
}

class UtilityBillSplit {
  final String id;
  final String utilityBillId;
  final String tenantUserId;
  final String? invoiceId;
  final UtilityBillSplitMethod splitMethod;
  final double? splitPercent;
  final double assignedAmount;
  final double paidAmount;
  final double outstandingAmount;
  final UtilityBillSplitStatus status;
  final DateTime? dueAt;
  final DateTime? paidAt;

  const UtilityBillSplit({
    required this.id,
    required this.utilityBillId,
    required this.tenantUserId,
    this.invoiceId,
    required this.splitMethod,
    this.splitPercent,
    required this.assignedAmount,
    required this.paidAmount,
    required this.outstandingAmount,
    required this.status,
    this.dueAt,
    this.paidAt,
  });

  factory UtilityBillSplit.fromJson(Map<String, dynamic> json) {
    return UtilityBillSplit(
      id: _readId(json, const ['id']),
      utilityBillId: _readId(json, const ['utility_bill_id', 'utilityBillId']),
      tenantUserId: _readId(json, const ['tenant_user_id', 'tenantUserId']),
      invoiceId: _readOptionalId(json, const ['invoice_id', 'invoiceId']),
      splitMethod: UtilityBillSplitMethod.fromString(
        readString(json, const ['split_method', 'splitMethod']),
      ),
      splitPercent: readDouble(json, const ['split_percent', 'splitPercent']),
      assignedAmount:
          readDouble(json, const ['assigned_amount', 'assignedAmount']) ?? 0,
      paidAmount: readDouble(json, const ['paid_amount', 'paidAmount']) ?? 0,
      outstandingAmount:
          readDouble(json, const ['outstanding_amount', 'outstandingAmount']) ??
              0,
      status:
          UtilityBillSplitStatus.fromString(readString(json, const ['status'])),
      dueAt: readDateTime(json, const ['due_at', 'dueAt']),
      paidAt: readDateTime(json, const ['paid_at', 'paidAt']),
    );
  }
}

class UtilityBillDispute {
  final String id;
  final String utilityBillSplitId;
  final String openedByUserId;
  final UtilityBillDisputeStatus status;
  final String reason;
  final String resolutionNotes;
  final DateTime? openedAt;
  final DateTime? resolvedAt;

  const UtilityBillDispute({
    required this.id,
    required this.utilityBillSplitId,
    required this.openedByUserId,
    required this.status,
    required this.reason,
    required this.resolutionNotes,
    this.openedAt,
    this.resolvedAt,
  });

  factory UtilityBillDispute.fromJson(Map<String, dynamic> json) {
    return UtilityBillDispute(
      id: _readId(json, const ['id']),
      utilityBillSplitId:
          _readId(json, const ['utility_bill_split_id', 'utilityBillSplitId']),
      openedByUserId:
          _readId(json, const ['opened_by_user_id', 'openedByUserId']),
      status: UtilityBillDisputeStatus.fromString(
        readString(json, const ['status']),
      ),
      reason: readString(json, const ['reason']) ?? '',
      resolutionNotes: readString(
            json,
            const ['resolution_notes', 'resolutionNotes'],
          ) ??
          '',
      openedAt: readDateTime(json, const ['opened_at', 'openedAt']),
      resolvedAt: readDateTime(json, const ['resolved_at', 'resolvedAt']),
    );
  }

  bool get isOpen => status == UtilityBillDisputeStatus.open;
}

class UtilityBill {
  final String id;
  final String propertyId;
  final String createdByUserId;
  final UtilityBillType billType;
  final String billingPeriodLabel;
  final DateTime? periodStart;
  final DateTime? periodEnd;
  final DateTime? dueDate;
  final double totalAmount;
  final double ownerSubsidyAmount;
  final double payableAmount;
  final UtilityBillStatus status;
  final String notes;
  final List<UtilityBillAttachment> attachments;
  final List<UtilityBillSplit> splits;
  final DateTime? createdAt;
  final DateTime? publishedAt;

  const UtilityBill({
    required this.id,
    required this.propertyId,
    required this.createdByUserId,
    required this.billType,
    required this.billingPeriodLabel,
    this.periodStart,
    this.periodEnd,
    this.dueDate,
    required this.totalAmount,
    required this.ownerSubsidyAmount,
    required this.payableAmount,
    required this.status,
    required this.notes,
    this.attachments = const <UtilityBillAttachment>[],
    this.splits = const <UtilityBillSplit>[],
    this.createdAt,
    this.publishedAt,
  });

  factory UtilityBill.fromJson(Map<String, dynamic> json) {
    return UtilityBill(
      id: _readId(json, const ['id']),
      propertyId: _readId(json, const ['property_id', 'propertyId']),
      createdByUserId:
          _readId(json, const ['created_by_user_id', 'createdByUserId']),
      billType: UtilityBillType.fromString(
          readString(json, const ['bill_type', 'billType'])),
      billingPeriodLabel: readString(
            json,
            const ['billing_period_label', 'billingPeriodLabel'],
          ) ??
          '',
      periodStart: readDateTime(json, const ['period_start', 'periodStart']),
      periodEnd: readDateTime(json, const ['period_end', 'periodEnd']),
      dueDate: readDateTime(json, const ['due_date', 'dueDate']),
      totalAmount: readDouble(json, const ['total_amount', 'totalAmount']) ?? 0,
      ownerSubsidyAmount: readDouble(
            json,
            const ['owner_subsidy_amount', 'ownerSubsidyAmount'],
          ) ??
          0,
      payableAmount:
          readDouble(json, const ['payable_amount', 'payableAmount']) ?? 0,
      status: UtilityBillStatus.fromString(readString(json, const ['status'])),
      notes: readString(json, const ['notes']) ?? '',
      attachments: readList(json, const ['attachments'])
          .map((item) => UtilityBillAttachment.fromJson(asJsonMap(item)))
          .toList(),
      splits: readList(json, const ['splits'])
          .map((item) => UtilityBillSplit.fromJson(asJsonMap(item)))
          .toList(),
      createdAt: readDateTime(json, const ['created_at', 'createdAt']),
      publishedAt: readDateTime(json, const ['published_at', 'publishedAt']),
    );
  }

  String get displayTitle {
    if (billingPeriodLabel.trim().isEmpty) return billType.displayName;
    return '${billType.displayName} · $billingPeriodLabel';
  }
}

class UtilityBillShare {
  final UtilityBillSplit split;
  final UtilityBill bill;
  final List<UtilityBillDispute> disputes;

  const UtilityBillShare({
    required this.split,
    required this.bill,
    this.disputes = const <UtilityBillDispute>[],
  });

  factory UtilityBillShare.fromJson(Map<String, dynamic> json) {
    return UtilityBillShare(
      split: UtilityBillSplit.fromJson(asJsonMap(json['split'])),
      bill: UtilityBill.fromJson(asJsonMap(json['bill'])),
      disputes: readList(json, const ['disputes'])
          .map((item) => UtilityBillDispute.fromJson(asJsonMap(item)))
          .toList(),
    );
  }

  UtilityBillDispute? get latestDispute =>
      disputes.isEmpty ? null : disputes.last;

  bool get hasOpenDispute => disputes.any((dispute) => dispute.isOpen);

  bool get canPay =>
      split.invoiceId != null &&
      split.outstandingAmount > 0.01 &&
      split.status != UtilityBillSplitStatus.paid &&
      split.status != UtilityBillSplitStatus.waived &&
      !hasOpenDispute;

  bool get canDispute =>
      split.outstandingAmount > 0.01 &&
      split.status != UtilityBillSplitStatus.paid &&
      split.status != UtilityBillSplitStatus.waived &&
      !hasOpenDispute;

  bool get canShowReceipt => split.invoiceId != null && split.paidAmount > 0.01;
}

class UtilityBillShareListResponse {
  final List<UtilityBillShare> items;
  final int total;

  const UtilityBillShareListResponse({
    required this.items,
    required this.total,
  });

  factory UtilityBillShareListResponse.fromJson(Map<String, dynamic> json) {
    return UtilityBillShareListResponse(
      items: readList(json, const ['items'])
          .map((item) => UtilityBillShare.fromJson(asJsonMap(item)))
          .toList(),
      total: readInt(json, const ['total']) ?? 0,
    );
  }
}

class UtilityBillHistoryEntry {
  final String eventType;
  final String message;
  final DateTime? occurredAt;
  final Map<String, dynamic> metadata;

  const UtilityBillHistoryEntry({
    required this.eventType,
    required this.message,
    this.occurredAt,
    this.metadata = const <String, dynamic>{},
  });

  factory UtilityBillHistoryEntry.fromJson(Map<String, dynamic> json) {
    return UtilityBillHistoryEntry(
      eventType: readString(json, const ['event_type', 'eventType']) ?? '',
      message: readString(json, const ['message']) ?? '',
      occurredAt: readDateTime(json, const ['occurred_at', 'occurredAt']),
      metadata:
          _readMetadata(readValue(json, const ['metadata_json', 'metadata'])),
    );
  }

  String get displayTitle {
    final normalized = _normalizeBillingToken(eventType);
    switch (normalized) {
      case 'utility_bill_created':
        return 'Bill created';
      case 'utility_bill_published':
        return 'Bill published';
      case 'utility_bill_attachment_uploaded':
        return 'Attachment added';
      case 'utility_bill_split_configured':
        return 'Tenant share set';
      case 'utility_bill_dispute':
        return 'Dispute opened';
      case 'utility_bill_dispute_resolved':
        return 'Dispute resolved';
      case 'utility_bill_paid':
        return 'Bill share paid';
      default:
        return titleFromKey(normalized);
    }
  }
}

class UtilityBillHistory {
  final String billId;
  final List<UtilityBillHistoryEntry> entries;

  const UtilityBillHistory({
    required this.billId,
    required this.entries,
  });

  factory UtilityBillHistory.fromJson(Map<String, dynamic> json) {
    return UtilityBillHistory(
      billId: _readId(json, const ['bill_id', 'billId']),
      entries: readList(json, const ['entries'])
          .map((item) => UtilityBillHistoryEntry.fromJson(asJsonMap(item)))
          .toList(),
    );
  }
}

class BillShareDisputeRequest {
  final String reason;

  const BillShareDisputeRequest({required this.reason});

  Map<String, dynamic> toJson() => {'reason': reason.trim()};
}
