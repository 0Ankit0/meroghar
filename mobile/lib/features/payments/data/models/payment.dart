import '../../../../core/utils/json_parsing.dart';

String _normalizePaymentToken(String value) {
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

Map<String, dynamic>? _readOptionalMap(dynamic value) {
  final map = asJsonMap(value);
  return map.isEmpty ? null : map;
}

enum PaymentProvider {
  khalti,
  esewa,
  stripe,
  paypal;

  static PaymentProvider fromString(String v) {
    final normalized = _normalizePaymentToken(v);
    return PaymentProvider.values.firstWhere(
      (e) => e.name == normalized,
      orElse: () => PaymentProvider.khalti,
    );
  }

  String get displayName {
    switch (this) {
      case PaymentProvider.khalti:
        return 'Khalti';
      case PaymentProvider.esewa:
        return 'eSewa';
      case PaymentProvider.stripe:
        return 'Stripe';
      case PaymentProvider.paypal:
        return 'PayPal';
    }
  }
}

enum PaymentStatus {
  pending,
  initiated,
  completed,
  failed,
  refunded,
  cancelled;

  static PaymentStatus fromString(String v) {
    switch (_normalizePaymentToken(v)) {
      case 'initiated':
      case 'created':
        return PaymentStatus.initiated;
      case 'completed':
      case 'complete':
      case 'approved':
      case 'paid':
        return PaymentStatus.completed;
      case 'failed':
      case 'error':
      case 'expired':
        return PaymentStatus.failed;
      case 'refunded':
      case 'full_refund':
        return PaymentStatus.refunded;
      case 'cancelled':
      case 'canceled':
      case 'user_cancelled':
      case 'user_canceled':
        return PaymentStatus.cancelled;
      case 'pending':
      default:
        return PaymentStatus.pending;
    }
  }
}

class InitiatePaymentRequest {
  final PaymentProvider provider;
  final int amount;
  final String purchaseOrderId;
  final String purchaseOrderName;
  final String returnUrl;
  final String websiteUrl;
  final String? customerName;
  final String? customerEmail;
  final String? customerPhone;

  const InitiatePaymentRequest({
    required this.provider,
    required this.amount,
    required this.purchaseOrderId,
    required this.purchaseOrderName,
    required this.returnUrl,
    required this.websiteUrl,
    this.customerName,
    this.customerEmail,
    this.customerPhone,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'provider': provider.name,
      'amount': amount,
      'purchase_order_id': purchaseOrderId,
      'purchase_order_name': purchaseOrderName,
      'return_url': returnUrl,
      'website_url': websiteUrl,
    };
    if (customerName != null) map['customer_name'] = customerName;
    if (customerEmail != null) map['customer_email'] = customerEmail;
    if (customerPhone != null) map['customer_phone'] = customerPhone;
    return map;
  }
}

class InitiatePaymentResponse {
  final String transactionId;
  final PaymentProvider provider;
  final PaymentStatus status;
  final String? paymentUrl;
  final String? providerPidx;
  final Map<String, dynamic>? extra;

  const InitiatePaymentResponse({
    required this.transactionId,
    required this.provider,
    required this.status,
    this.paymentUrl,
    this.providerPidx,
    this.extra,
  });

  factory InitiatePaymentResponse.fromJson(Map<String, dynamic> json) {
    return InitiatePaymentResponse(
      transactionId: _readId(json, const ['transaction_id', 'transactionId']),
      provider: PaymentProvider.fromString(
          readString(json, const ['provider']) ?? 'khalti'),
      status: PaymentStatus.fromString(
        readString(json, const ['status']) ?? 'pending',
      ),
      paymentUrl: readString(json, const ['payment_url', 'paymentUrl']),
      providerPidx: readString(json, const ['provider_pidx', 'providerPidx']),
      extra: _readOptionalMap(json['extra']),
    );
  }
}

class VerifyPaymentRequest {
  final PaymentProvider provider;
  final String? pidx;
  final String? oid;
  final String? refId;
  final String? data;
  final String? transactionId;

  const VerifyPaymentRequest({
    required this.provider,
    this.pidx,
    this.oid,
    this.refId,
    this.data,
    this.transactionId,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{'provider': provider.name};
    if (pidx != null) map['pidx'] = pidx;
    if (oid != null) map['oid'] = oid;
    if (refId != null) map['refId'] = refId;
    if (data != null) map['data'] = data;
    if (transactionId != null) map['transaction_id'] = transactionId;
    return map;
  }
}

class VerifyPaymentResponse {
  final String transactionId;
  final PaymentProvider provider;
  final PaymentStatus status;
  final int? amount;
  final String? providerTransactionId;
  final Map<String, dynamic>? extra;

  const VerifyPaymentResponse({
    required this.transactionId,
    required this.provider,
    required this.status,
    this.amount,
    this.providerTransactionId,
    this.extra,
  });

  factory VerifyPaymentResponse.fromJson(Map<String, dynamic> json) {
    return VerifyPaymentResponse(
      transactionId: _readId(json, const ['transaction_id', 'transactionId']),
      provider: PaymentProvider.fromString(
          readString(json, const ['provider']) ?? 'khalti'),
      status: PaymentStatus.fromString(
        readString(json, const ['status']) ?? 'pending',
      ),
      amount: readInt(json, const ['amount']),
      providerTransactionId: readString(
        json,
        const ['provider_transaction_id', 'providerTransactionId'],
      ),
      extra: _readOptionalMap(json['extra']),
    );
  }
}

class PaymentTransaction {
  final String id;
  final PaymentProvider provider;
  final PaymentStatus status;
  final int amount;
  final String currency;
  final String purchaseOrderId;
  final String purchaseOrderName;
  final String? providerTransactionId;
  final String? providerPidx;
  final String returnUrl;
  final String websiteUrl;
  final String? failureReason;

  const PaymentTransaction({
    required this.id,
    required this.provider,
    required this.status,
    required this.amount,
    required this.currency,
    required this.purchaseOrderId,
    required this.purchaseOrderName,
    this.providerTransactionId,
    this.providerPidx,
    required this.returnUrl,
    required this.websiteUrl,
    this.failureReason,
  });

  factory PaymentTransaction.fromJson(Map<String, dynamic> json) {
    return PaymentTransaction(
      id: _readId(json, const ['id', 'transaction_id', 'transactionId']),
      provider: PaymentProvider.fromString(
          readString(json, const ['provider']) ?? 'khalti'),
      status: PaymentStatus.fromString(
        readString(json, const ['status']) ?? 'pending',
      ),
      amount: readInt(json, const ['amount']) ?? 0,
      currency: readString(json, const ['currency']) ?? 'NPR',
      purchaseOrderId: readString(
            json,
            const ['purchase_order_id', 'purchaseOrderId'],
          ) ??
          '',
      purchaseOrderName: readString(
            json,
            const ['purchase_order_name', 'purchaseOrderName'],
          ) ??
          '',
      providerTransactionId: readString(
        json,
        const ['provider_transaction_id', 'providerTransactionId'],
      ),
      providerPidx: readString(json, const ['provider_pidx', 'providerPidx']),
      returnUrl: readString(json, const ['return_url', 'returnUrl']) ?? '',
      websiteUrl: readString(json, const ['website_url', 'websiteUrl']) ?? '',
      failureReason: readString(
        json,
        const ['failure_reason', 'failureReason'],
      ),
    );
  }
}
