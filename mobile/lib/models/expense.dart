/// Expense model for local storage and API communication.
///
/// Implements T134 from tasks.md.
library;

import 'package:flutter/foundation.dart';

/// Expense category enum matching backend ExpenseCategory
enum ExpenseCategory {
  maintenance,
  repair,
  cleaning,
  landscaping,
  security,
  utilities,
  insurance,
  taxes,
  legal,
  administrative,
  other;

  String toJson() => name;

  static ExpenseCategory fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'maintenance':
        return ExpenseCategory.maintenance;
      case 'repair':
        return ExpenseCategory.repair;
      case 'cleaning':
        return ExpenseCategory.cleaning;
      case 'landscaping':
        return ExpenseCategory.landscaping;
      case 'security':
        return ExpenseCategory.security;
      case 'utilities':
        return ExpenseCategory.utilities;
      case 'insurance':
        return ExpenseCategory.insurance;
      case 'taxes':
        return ExpenseCategory.taxes;
      case 'legal':
        return ExpenseCategory.legal;
      case 'administrative':
        return ExpenseCategory.administrative;
      case 'other':
        return ExpenseCategory.other;
      default:
        throw ArgumentError('Invalid expense category: $json');
    }
  }

  String get displayName {
    switch (this) {
      case ExpenseCategory.maintenance:
        return 'Maintenance';
      case ExpenseCategory.repair:
        return 'Repair';
      case ExpenseCategory.cleaning:
        return 'Cleaning';
      case ExpenseCategory.landscaping:
        return 'Landscaping';
      case ExpenseCategory.security:
        return 'Security';
      case ExpenseCategory.utilities:
        return 'Utilities';
      case ExpenseCategory.insurance:
        return 'Insurance';
      case ExpenseCategory.taxes:
        return 'Taxes';
      case ExpenseCategory.legal:
        return 'Legal';
      case ExpenseCategory.administrative:
        return 'Administrative';
      case ExpenseCategory.other:
        return 'Other';
    }
  }
}

/// Expense status enum matching backend ExpenseStatus
enum ExpenseStatus {
  pending,
  approved,
  rejected,
  reimbursed;

  String toJson() => name;

  static ExpenseStatus fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'pending':
        return ExpenseStatus.pending;
      case 'approved':
        return ExpenseStatus.approved;
      case 'rejected':
        return ExpenseStatus.rejected;
      case 'reimbursed':
        return ExpenseStatus.reimbursed;
      default:
        throw ArgumentError('Invalid expense status: $json');
    }
  }

  String get displayName {
    switch (this) {
      case ExpenseStatus.pending:
        return 'Pending';
      case ExpenseStatus.approved:
        return 'Approved';
      case ExpenseStatus.rejected:
        return 'Rejected';
      case ExpenseStatus.reimbursed:
        return 'Reimbursed';
    }
  }
}

/// Expense model
@immutable
class Expense {
  const Expense({
    required this.id,
    required this.propertyId,
    required this.amount,
    required this.category,
    required this.expenseDate,
    required this.description,
    this.vendorName,
    this.invoiceNumber,
    this.receiptUrl,
    this.paidBy,
    required this.isReimbursable,
    required this.isReimbursed,
    this.reimbursedDate,
    required this.status,
    required this.recordedBy,
    this.approvedBy,
    this.approvedDate,
    this.rejectionReason,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Create from JSON
  factory Expense.fromJson(Map<String, dynamic> json) {
    return Expense(
      id: json['id'] as String,
      propertyId: json['property_id'] as String,
      amount: (json['amount'] as num).toDouble(),
      category: ExpenseCategory.fromJson(json['category'] as String),
      expenseDate: DateTime.parse(json['expense_date'] as String),
      description: json['description'] as String,
      vendorName: json['vendor_name'] as String?,
      invoiceNumber: json['invoice_number'] as String?,
      receiptUrl: json['receipt_url'] as String?,
      paidBy: json['paid_by'] as String?,
      isReimbursable: json['is_reimbursable'] as bool,
      isReimbursed: json['is_reimbursed'] as bool,
      reimbursedDate: json['reimbursed_date'] != null
          ? DateTime.parse(json['reimbursed_date'] as String)
          : null,
      status: ExpenseStatus.fromJson(json['status'] as String),
      recordedBy: json['recorded_by'] as String,
      approvedBy: json['approved_by'] as String?,
      approvedDate: json['approved_date'] != null
          ? DateTime.parse(json['approved_date'] as String)
          : null,
      rejectionReason: json['rejection_reason'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Unique expense identifier
  final String id;

  /// Property ID
  final String propertyId;

  /// Expense amount
  final double amount;

  /// Expense category
  final ExpenseCategory category;

  /// Expense date
  final DateTime expenseDate;

  /// Description
  final String description;

  /// Vendor name
  final String? vendorName;

  /// Invoice number
  final String? invoiceNumber;

  /// Receipt URL
  final String? receiptUrl;

  /// Person who paid
  final String? paidBy;

  /// Is reimbursable
  final bool isReimbursable;

  /// Is reimbursed
  final bool isReimbursed;

  /// Reimbursed date
  final DateTime? reimbursedDate;

  /// Expense status
  final ExpenseStatus status;

  /// User who recorded the expense
  final String recordedBy;

  /// User who approved the expense
  final String? approvedBy;

  /// Approved date
  final DateTime? approvedDate;

  /// Rejection reason
  final String? rejectionReason;

  /// Created timestamp
  final DateTime createdAt;

  /// Updated timestamp
  final DateTime updatedAt;

  /// Convert to JSON
  Map<String, dynamic> toJson() => {
        'id': id,
        'property_id': propertyId,
        'amount': amount,
        'category': category.toJson(),
        'expense_date': expenseDate.toIso8601String().split('T')[0],
        'description': description,
        'vendor_name': vendorName,
        'invoice_number': invoiceNumber,
        'receipt_url': receiptUrl,
        'paid_by': paidBy,
        'is_reimbursable': isReimbursable,
        'is_reimbursed': isReimbursed,
        'reimbursed_date': reimbursedDate?.toIso8601String().split('T')[0],
        'status': status.toJson(),
        'recorded_by': recordedBy,
        'approved_by': approvedBy,
        'approved_date': approvedDate?.toIso8601String(),
        'rejection_reason': rejectionReason,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };

  /// Copy with
  Expense copyWith({
    String? id,
    String? propertyId,
    double? amount,
    ExpenseCategory? category,
    DateTime? expenseDate,
    String? description,
    String? vendorName,
    String? invoiceNumber,
    String? receiptUrl,
    String? paidBy,
    bool? isReimbursable,
    bool? isReimbursed,
    DateTime? reimbursedDate,
    ExpenseStatus? status,
    String? recordedBy,
    String? approvedBy,
    DateTime? approvedDate,
    String? rejectionReason,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) =>
      Expense(
        id: id ?? this.id,
        propertyId: propertyId ?? this.propertyId,
        amount: amount ?? this.amount,
        category: category ?? this.category,
        expenseDate: expenseDate ?? this.expenseDate,
        description: description ?? this.description,
        vendorName: vendorName ?? this.vendorName,
        invoiceNumber: invoiceNumber ?? this.invoiceNumber,
        receiptUrl: receiptUrl ?? this.receiptUrl,
        paidBy: paidBy ?? this.paidBy,
        isReimbursable: isReimbursable ?? this.isReimbursable,
        isReimbursed: isReimbursed ?? this.isReimbursed,
        reimbursedDate: reimbursedDate ?? this.reimbursedDate,
        status: status ?? this.status,
        recordedBy: recordedBy ?? this.recordedBy,
        approvedBy: approvedBy ?? this.approvedBy,
        approvedDate: approvedDate ?? this.approvedDate,
        rejectionReason: rejectionReason ?? this.rejectionReason,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
      );

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Expense && other.id == id;
  }

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() =>
      'Expense(id: $id, amount: $amount, category: ${category.displayName}, status: ${status.displayName})';
}

/// Expense summary model
@immutable
class ExpenseSummary {
  const ExpenseSummary({
    required this.totalAmount,
    required this.pendingAmount,
    required this.approvedAmount,
    required this.reimbursedAmount,
    required this.outstandingAmount,
    required this.byCategory,
  });

  /// Create from JSON
  factory ExpenseSummary.fromJson(Map<String, dynamic> json) {
    return ExpenseSummary(
      totalAmount: (json['total_amount'] as num).toDouble(),
      pendingAmount: (json['pending_amount'] as num).toDouble(),
      approvedAmount: (json['approved_amount'] as num).toDouble(),
      reimbursedAmount: (json['reimbursed_amount'] as num).toDouble(),
      outstandingAmount: (json['outstanding_amount'] as num).toDouble(),
      byCategory: (json['by_category'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      ),
    );
  }

  /// Total amount
  final double totalAmount;

  /// Pending amount
  final double pendingAmount;

  /// Approved amount
  final double approvedAmount;

  /// Reimbursed amount
  final double reimbursedAmount;

  /// Outstanding amount (approved but not reimbursed)
  final double outstandingAmount;

  /// Breakdown by category
  final Map<String, double> byCategory;

  /// Convert to JSON
  Map<String, dynamic> toJson() => {
        'total_amount': totalAmount,
        'pending_amount': pendingAmount,
        'approved_amount': approvedAmount,
        'reimbursed_amount': reimbursedAmount,
        'outstanding_amount': outstandingAmount,
        'by_category': byCategory,
      };
}
