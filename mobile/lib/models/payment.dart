/// Payment model for local storage and API communication.
///
/// Implements T065 from tasks.md.
library;

import 'package:flutter/foundation.dart';

/// Payment method enum matching backend PaymentMethod
enum PaymentMethod {
  cash,
  bankTransfer,
  upi,
  cheque,
  card,
  online;

  String toJson() => name;

  static PaymentMethod fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'cash':
        return PaymentMethod.cash;
      case 'bank_transfer':
      case 'banktransfer':
        return PaymentMethod.bankTransfer;
      case 'upi':
        return PaymentMethod.upi;
      case 'cheque':
        return PaymentMethod.cheque;
      case 'card':
        return PaymentMethod.card;
      case 'online':
        return PaymentMethod.online;
      default:
        throw ArgumentError('Invalid payment method: $json');
    }
  }

  String get displayName {
    switch (this) {
      case PaymentMethod.cash:
        return 'Cash';
      case PaymentMethod.bankTransfer:
        return 'Bank Transfer';
      case PaymentMethod.upi:
        return 'UPI';
      case PaymentMethod.cheque:
        return 'Cheque';
      case PaymentMethod.card:
        return 'Card';
      case PaymentMethod.online:
        return 'Online';
    }
  }
}

/// Payment type enum matching backend PaymentType
enum PaymentType {
  rent,
  securityDeposit,
  maintenanceCharge,
  utilityBill,
  other;

  String toJson() => name;

  static PaymentType fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'rent':
        return PaymentType.rent;
      case 'security_deposit':
      case 'securitydeposit':
        return PaymentType.securityDeposit;
      case 'maintenance_charge':
      case 'maintenancecharge':
        return PaymentType.maintenanceCharge;
      case 'utility_bill':
      case 'utilitybill':
        return PaymentType.utilityBill;
      case 'other':
        return PaymentType.other;
      default:
        throw ArgumentError('Invalid payment type: $json');
    }
  }

  String get displayName {
    switch (this) {
      case PaymentType.rent:
        return 'Rent';
      case PaymentType.securityDeposit:
        return 'Security Deposit';
      case PaymentType.maintenanceCharge:
        return 'Maintenance Charge';
      case PaymentType.utilityBill:
        return 'Utility Bill';
      case PaymentType.other:
        return 'Other';
    }
  }
}

/// Payment status enum matching backend PaymentStatus
enum PaymentStatus {
  pending,
  completed,
  failed,
  refunded;

  String toJson() => name;

  static PaymentStatus fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'pending':
        return PaymentStatus.pending;
      case 'completed':
        return PaymentStatus.completed;
      case 'failed':
        return PaymentStatus.failed;
      case 'refunded':
        return PaymentStatus.refunded;
      default:
        throw ArgumentError('Invalid payment status: $json');
    }
  }

  String get displayName {
    switch (this) {
      case PaymentStatus.pending:
        return 'Pending';
      case PaymentStatus.completed:
        return 'Completed';
      case PaymentStatus.failed:
        return 'Failed';
      case PaymentStatus.refunded:
        return 'Refunded';
    }
  }
}

/// Payment model representing a rent or utility payment
@immutable
class Payment {
  const Payment({
    required this.id,
    required this.tenantId,
    required this.propertyId,
    this.recordedBy,
    required this.amount,
    this.currency = 'INR',
    required this.paymentMethod,
    required this.paymentType,
    required this.status,
    required this.paymentDate,
    this.paymentPeriodStart,
    this.paymentPeriodEnd,
    this.transactionReference,
    this.notes,
    this.receiptUrl,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Create Payment from JSON (API response)
  factory Payment.fromJson(Map<String, dynamic> json) {
    return Payment(
      id: json['id'] as String,
      tenantId: json['tenant_id'] as String,
      propertyId: json['property_id'] as String,
      recordedBy: json['recorded_by'] as String?,
      amount: (json['amount'] as num).toDouble(),
      currency: json['currency'] as String? ?? 'INR',
      paymentMethod: PaymentMethod.fromJson(json['payment_method'] as String),
      paymentType: PaymentType.fromJson(json['payment_type'] as String),
      status: PaymentStatus.fromJson(json['status'] as String),
      paymentDate: DateTime.parse(json['payment_date'] as String),
      paymentPeriodStart: json['payment_period_start'] != null
          ? DateTime.parse(json['payment_period_start'] as String)
          : null,
      paymentPeriodEnd: json['payment_period_end'] != null
          ? DateTime.parse(json['payment_period_end'] as String)
          : null,
      transactionReference: json['transaction_reference'] as String?,
      notes: json['notes'] as String?,
      receiptUrl: json['receipt_url'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Create Payment from SQLite database row
  factory Payment.fromDatabase(Map<String, dynamic> map) {
    return Payment(
      id: map['id'] as String,
      tenantId: map['tenant_id'] as String,
      propertyId: map['property_id'] as String,
      recordedBy: map['recorded_by'] as String?,
      amount: map['amount'] as double,
      currency: map['currency'] as String? ?? 'INR',
      paymentMethod: PaymentMethod.fromJson(map['payment_method'] as String),
      paymentType: PaymentType.fromJson(map['payment_type'] as String),
      status: PaymentStatus.fromJson(map['status'] as String),
      paymentDate: DateTime.parse(map['payment_date'] as String),
      paymentPeriodStart: map['payment_period_start'] != null
          ? DateTime.parse(map['payment_period_start'] as String)
          : null,
      paymentPeriodEnd: map['payment_period_end'] != null
          ? DateTime.parse(map['payment_period_end'] as String)
          : null,
      transactionReference: map['transaction_reference'] as String?,
      notes: map['notes'] as String?,
      receiptUrl: map['receipt_url'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
    );
  }
  final String id;
  final String tenantId;
  final String propertyId;
  final String? recordedBy;
  final double amount;
  final String currency;
  final PaymentMethod paymentMethod;
  final PaymentType paymentType;
  final PaymentStatus status;
  final DateTime paymentDate;
  final DateTime? paymentPeriodStart;
  final DateTime? paymentPeriodEnd;
  final String? transactionReference;
  final String? notes;
  final String? receiptUrl;
  final DateTime createdAt;
  final DateTime updatedAt;

  /// Convert Payment to JSON (for API requests)
  Map<String, dynamic> toJson() => {
        'id': id,
        'tenant_id': tenantId,
        'property_id': propertyId,
        'recorded_by': recordedBy,
        'amount': amount,
        'currency': currency,
        'payment_method': paymentMethod.toJson(),
        'payment_type': paymentType.toJson(),
        'status': status.toJson(),
        'payment_date': paymentDate.toIso8601String(),
        'payment_period_start': paymentPeriodStart?.toIso8601String(),
        'payment_period_end': paymentPeriodEnd?.toIso8601String(),
        'transaction_reference': transactionReference,
        'notes': notes,
        'receipt_url': receiptUrl,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Convert Payment to SQLite database map
  Map<String, dynamic> toDatabase() => {
        'id': id,
        'tenant_id': tenantId,
        'property_id': propertyId,
        'recorded_by': recordedBy,
        'amount': amount,
        'currency': currency,
        'payment_method': paymentMethod.toJson(),
        'payment_type': paymentType.toJson(),
        'status': status.toJson(),
        'payment_date': paymentDate.toIso8601String(),
        'payment_period_start': paymentPeriodStart?.toIso8601String(),
        'payment_period_end': paymentPeriodEnd?.toIso8601String(),
        'transaction_reference': transactionReference,
        'notes': notes,
        'receipt_url': receiptUrl,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Copy with method for immutable updates
  Payment copyWith({
    String? id,
    String? tenantId,
    String? propertyId,
    String? recordedBy,
    double? amount,
    String? currency,
    PaymentMethod? paymentMethod,
    PaymentType? paymentType,
    PaymentStatus? status,
    DateTime? paymentDate,
    DateTime? paymentPeriodStart,
    DateTime? paymentPeriodEnd,
    String? transactionReference,
    String? notes,
    String? receiptUrl,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) =>
      Payment(
        id: id ?? this.id,
        tenantId: tenantId ?? this.tenantId,
        propertyId: propertyId ?? this.propertyId,
        recordedBy: recordedBy ?? this.recordedBy,
        amount: amount ?? this.amount,
        currency: currency ?? this.currency,
        paymentMethod: paymentMethod ?? this.paymentMethod,
        paymentType: paymentType ?? this.paymentType,
        status: status ?? this.status,
        paymentDate: paymentDate ?? this.paymentDate,
        paymentPeriodStart: paymentPeriodStart ?? this.paymentPeriodStart,
        paymentPeriodEnd: paymentPeriodEnd ?? this.paymentPeriodEnd,
        transactionReference: transactionReference ?? this.transactionReference,
        notes: notes ?? this.notes,
        receiptUrl: receiptUrl ?? this.receiptUrl,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
      );

  /// Check if payment is overdue (for rent payments)
  bool get isOverdue {
    if (paymentType != PaymentType.rent || status == PaymentStatus.completed) {
      return false;
    }
    return paymentDate.isBefore(DateTime.now());
  }

  /// Get formatted amount with currency
  String get formattedAmount => '$currency ${amount.toStringAsFixed(2)}';

  /// Get payment period display string
  String? get periodDisplay {
    if (paymentPeriodStart == null || paymentPeriodEnd == null) {
      return null;
    }
    final start = paymentPeriodStart!;
    final end = paymentPeriodEnd!;
    return '${start.day}/${start.month}/${start.year} - ${end.day}/${end.month}/${end.year}';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is Payment &&
        other.id == id &&
        other.tenantId == tenantId &&
        other.propertyId == propertyId &&
        other.recordedBy == recordedBy &&
        other.amount == amount &&
        other.currency == currency &&
        other.paymentMethod == paymentMethod &&
        other.paymentType == paymentType &&
        other.status == status &&
        other.paymentDate == paymentDate &&
        other.paymentPeriodStart == paymentPeriodStart &&
        other.paymentPeriodEnd == paymentPeriodEnd &&
        other.transactionReference == transactionReference &&
        other.notes == notes &&
        other.receiptUrl == receiptUrl &&
        other.createdAt == createdAt &&
        other.updatedAt == updatedAt;
  }

  @override
  int get hashCode => Object.hash(
        id,
        tenantId,
        propertyId,
        recordedBy,
        amount,
        currency,
        paymentMethod,
        paymentType,
        status,
        paymentDate,
        paymentPeriodStart,
        paymentPeriodEnd,
        transactionReference,
        notes,
        receiptUrl,
        createdAt,
        updatedAt,
      );

  @override
  String toString() =>
      'Payment(id: $id, amount: $formattedAmount, type: ${paymentType.displayName}, status: ${status.displayName})';
}

/// Tenant balance response model
@immutable
class TenantBalance {
  const TenantBalance({
    required this.tenantId,
    required this.propertyId,
    required this.totalPaid,
    required this.totalDue,
    required this.outstandingBalance,
    this.lastPaymentDate,
    this.lastPaymentAmount,
    required this.monthsBehind,
  });

  factory TenantBalance.fromJson(Map<String, dynamic> json) {
    return TenantBalance(
      tenantId: json['tenant_id'] as String,
      propertyId: json['property_id'] as String,
      totalPaid: (json['total_paid'] as num).toDouble(),
      totalDue: (json['total_due'] as num).toDouble(),
      outstandingBalance: (json['outstanding_balance'] as num).toDouble(),
      lastPaymentDate: json['last_payment_date'] != null
          ? DateTime.parse(json['last_payment_date'] as String)
          : null,
      lastPaymentAmount: json['last_payment_amount'] != null
          ? (json['last_payment_amount'] as num).toDouble()
          : null,
      monthsBehind: json['months_behind'] as int,
    );
  }
  final String tenantId;
  final String propertyId;
  final double totalPaid;
  final double totalDue;
  final double outstandingBalance;
  final DateTime? lastPaymentDate;
  final double? lastPaymentAmount;
  final int monthsBehind;

  Map<String, dynamic> toJson() => {
        'tenant_id': tenantId,
        'property_id': propertyId,
        'total_paid': totalPaid,
        'total_due': totalDue,
        'outstanding_balance': outstandingBalance,
        'last_payment_date': lastPaymentDate?.toIso8601String(),
        'last_payment_amount': lastPaymentAmount,
        'months_behind': monthsBehind,
      };

  /// Check if tenant is behind on payments
  bool get isBehind => monthsBehind > 0;

  /// Get formatted outstanding balance
  String get formattedOutstanding =>
      'INR ${outstandingBalance.toStringAsFixed(2)}';

  @override
  String toString() =>
      'TenantBalance(outstanding: $formattedOutstanding, monthsBehind: $monthsBehind)';
}
