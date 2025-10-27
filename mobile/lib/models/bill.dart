/// Bill models for local storage and API communication.
///
/// Implements T087 from tasks.md.
library;

import 'package:flutter/foundation.dart';

/// Bill type enum matching backend BillType
enum BillType {
  electricity,
  water,
  gas,
  internet,
  maintenance,
  garbage,
  other;

  String toJson() => name;

  static BillType fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'electricity':
        return BillType.electricity;
      case 'water':
        return BillType.water;
      case 'gas':
        return BillType.gas;
      case 'internet':
        return BillType.internet;
      case 'maintenance':
        return BillType.maintenance;
      case 'garbage':
        return BillType.garbage;
      case 'other':
        return BillType.other;
      default:
        throw ArgumentError('Invalid bill type: $json');
    }
  }

  String get displayName {
    switch (this) {
      case BillType.electricity:
        return 'Electricity';
      case BillType.water:
        return 'Water';
      case BillType.gas:
        return 'Gas';
      case BillType.internet:
        return 'Internet';
      case BillType.maintenance:
        return 'Maintenance';
      case BillType.garbage:
        return 'Garbage';
      case BillType.other:
        return 'Other';
    }
  }
}

/// Bill status enum matching backend BillStatus
enum BillStatus {
  pending,
  partiallyPaid,
  paid,
  overdue;

  String toJson() => name;

  static BillStatus fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'pending':
        return BillStatus.pending;
      case 'partially_paid':
      case 'partiallypaid':
        return BillStatus.partiallyPaid;
      case 'paid':
        return BillStatus.paid;
      case 'overdue':
        return BillStatus.overdue;
      default:
        throw ArgumentError('Invalid bill status: $json');
    }
  }

  String get displayName {
    switch (this) {
      case BillStatus.pending:
        return 'Pending';
      case BillStatus.partiallyPaid:
        return 'Partially Paid';
      case BillStatus.paid:
        return 'Paid';
      case BillStatus.overdue:
        return 'Overdue';
    }
  }
}

/// Allocation method enum matching backend AllocationMethod
enum AllocationMethod {
  equal,
  percentage,
  fixedAmount,
  custom;

  String toJson() => name;

  static AllocationMethod fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'equal':
        return AllocationMethod.equal;
      case 'percentage':
        return AllocationMethod.percentage;
      case 'fixed_amount':
      case 'fixedamount':
        return AllocationMethod.fixedAmount;
      case 'custom':
        return AllocationMethod.custom;
      default:
        throw ArgumentError('Invalid allocation method: $json');
    }
  }

  String get displayName {
    switch (this) {
      case AllocationMethod.equal:
        return 'Equal Division';
      case AllocationMethod.percentage:
        return 'Percentage-based';
      case AllocationMethod.fixedAmount:
        return 'Fixed Amount';
      case AllocationMethod.custom:
        return 'Custom';
    }
  }
}

/// Recurring frequency enum matching backend RecurringFrequency
enum RecurringFrequency {
  monthly,
  quarterly,
  yearly;

  String toJson() => name;

  static RecurringFrequency fromJson(String json) {
    switch (json.toLowerCase()) {
      case 'monthly':
        return RecurringFrequency.monthly;
      case 'quarterly':
        return RecurringFrequency.quarterly;
      case 'yearly':
        return RecurringFrequency.yearly;
      default:
        throw ArgumentError('Invalid recurring frequency: $json');
    }
  }

  String get displayName {
    switch (this) {
      case RecurringFrequency.monthly:
        return 'Monthly';
      case RecurringFrequency.quarterly:
        return 'Quarterly';
      case RecurringFrequency.yearly:
        return 'Yearly';
    }
  }
}

/// Bill allocation model
@immutable
class BillAllocation {
  final String id;
  final String billId;
  final String tenantId;
  final double allocatedAmount;
  final double? percentage;
  final bool isPaid;
  final DateTime? paidDate;
  final String? paymentId;
  final String? notes;
  final DateTime createdAt;
  final DateTime updatedAt;

  const BillAllocation({
    required this.id,
    required this.billId,
    required this.tenantId,
    required this.allocatedAmount,
    this.percentage,
    required this.isPaid,
    this.paidDate,
    this.paymentId,
    this.notes,
    required this.createdAt,
    required this.updatedAt,
  });

  factory BillAllocation.fromJson(Map<String, dynamic> json) {
    return BillAllocation(
      id: json['id'] as String,
      billId: json['bill_id'] as String,
      tenantId: json['tenant_id'] as String,
      allocatedAmount: (json['allocated_amount'] as num).toDouble(),
      percentage: json['percentage'] != null
          ? (json['percentage'] as num).toDouble()
          : null,
      isPaid: json['is_paid'] as bool,
      paidDate: json['paid_date'] != null
          ? DateTime.parse(json['paid_date'] as String)
          : null,
      paymentId: json['payment_id'] as String?,
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'bill_id': billId,
      'tenant_id': tenantId,
      'allocated_amount': allocatedAmount,
      'percentage': percentage,
      'is_paid': isPaid,
      'paid_date': paidDate?.toIso8601String(),
      'payment_id': paymentId,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  BillAllocation copyWith({
    String? id,
    String? billId,
    String? tenantId,
    double? allocatedAmount,
    double? percentage,
    bool? isPaid,
    DateTime? paidDate,
    String? paymentId,
    String? notes,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return BillAllocation(
      id: id ?? this.id,
      billId: billId ?? this.billId,
      tenantId: tenantId ?? this.tenantId,
      allocatedAmount: allocatedAmount ?? this.allocatedAmount,
      percentage: percentage ?? this.percentage,
      isPaid: isPaid ?? this.isPaid,
      paidDate: paidDate ?? this.paidDate,
      paymentId: paymentId ?? this.paymentId,
      notes: notes ?? this.notes,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is BillAllocation &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          billId == other.billId &&
          tenantId == other.tenantId;

  @override
  int get hashCode => id.hashCode ^ billId.hashCode ^ tenantId.hashCode;

  @override
  String toString() =>
      'BillAllocation(id: $id, allocatedAmount: $allocatedAmount, isPaid: $isPaid)';
}

/// Bill model
@immutable
class Bill {
  final String id;
  final String propertyId;
  final BillType billType;
  final double totalAmount;
  final String currency;
  final DateTime periodStart;
  final DateTime periodEnd;
  final DateTime dueDate;
  final BillStatus status;
  final AllocationMethod allocationMethod;
  final String? description;
  final String? billNumber;
  final DateTime? paidDate;
  final String? createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<BillAllocation> allocations;

  const Bill({
    required this.id,
    required this.propertyId,
    required this.billType,
    required this.totalAmount,
    required this.currency,
    required this.periodStart,
    required this.periodEnd,
    required this.dueDate,
    required this.status,
    required this.allocationMethod,
    this.description,
    this.billNumber,
    this.paidDate,
    this.createdBy,
    required this.createdAt,
    required this.updatedAt,
    this.allocations = const [],
  });

  factory Bill.fromJson(Map<String, dynamic> json) {
    return Bill(
      id: json['id'] as String,
      propertyId: json['property_id'] as String,
      billType: BillType.fromJson(json['bill_type'] as String),
      totalAmount: (json['total_amount'] as num).toDouble(),
      currency: json['currency'] as String,
      periodStart: DateTime.parse(json['period_start'] as String),
      periodEnd: DateTime.parse(json['period_end'] as String),
      dueDate: DateTime.parse(json['due_date'] as String),
      status: BillStatus.fromJson(json['status'] as String),
      allocationMethod:
          AllocationMethod.fromJson(json['allocation_method'] as String),
      description: json['description'] as String?,
      billNumber: json['bill_number'] as String?,
      paidDate: json['paid_date'] != null
          ? DateTime.parse(json['paid_date'] as String)
          : null,
      createdBy: json['created_by'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      allocations: json['allocations'] != null
          ? (json['allocations'] as List)
              .map((e) => BillAllocation.fromJson(e as Map<String, dynamic>))
              .toList()
          : const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'property_id': propertyId,
      'bill_type': billType.toJson(),
      'total_amount': totalAmount,
      'currency': currency,
      'period_start': periodStart.toIso8601String(),
      'period_end': periodEnd.toIso8601String(),
      'due_date': dueDate.toIso8601String(),
      'status': status.toJson(),
      'allocation_method': allocationMethod.toJson(),
      'description': description,
      'bill_number': billNumber,
      'paid_date': paidDate?.toIso8601String(),
      'created_by': createdBy,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'allocations': allocations.map((e) => e.toJson()).toList(),
    };
  }

  Bill copyWith({
    String? id,
    String? propertyId,
    BillType? billType,
    double? totalAmount,
    String? currency,
    DateTime? periodStart,
    DateTime? periodEnd,
    DateTime? dueDate,
    BillStatus? status,
    AllocationMethod? allocationMethod,
    String? description,
    String? billNumber,
    DateTime? paidDate,
    String? createdBy,
    DateTime? createdAt,
    DateTime? updatedAt,
    List<BillAllocation>? allocations,
  }) {
    return Bill(
      id: id ?? this.id,
      propertyId: propertyId ?? this.propertyId,
      billType: billType ?? this.billType,
      totalAmount: totalAmount ?? this.totalAmount,
      currency: currency ?? this.currency,
      periodStart: periodStart ?? this.periodStart,
      periodEnd: periodEnd ?? this.periodEnd,
      dueDate: dueDate ?? this.dueDate,
      status: status ?? this.status,
      allocationMethod: allocationMethod ?? this.allocationMethod,
      description: description ?? this.description,
      billNumber: billNumber ?? this.billNumber,
      paidDate: paidDate ?? this.paidDate,
      createdBy: createdBy ?? this.createdBy,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      allocations: allocations ?? this.allocations,
    );
  }

  /// Get total paid amount from allocations
  double get totalPaid {
    return allocations
        .where((alloc) => alloc.isPaid)
        .fold(0.0, (sum, alloc) => sum + alloc.allocatedAmount);
  }

  /// Get number of paid allocations
  int get paidCount {
    return allocations.where((alloc) => alloc.isPaid).length;
  }

  /// Check if bill is overdue
  bool get isOverdue {
    return dueDate.isBefore(DateTime.now()) && status != BillStatus.paid;
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Bill &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          propertyId == other.propertyId;

  @override
  int get hashCode => id.hashCode ^ propertyId.hashCode;

  @override
  String toString() =>
      'Bill(id: $id, type: ${billType.displayName}, amount: $totalAmount, status: ${status.displayName})';
}

/// Recurring bill model
@immutable
class RecurringBill {
  final String id;
  final String propertyId;
  final BillType billType;
  final RecurringFrequency frequency;
  final AllocationMethod allocationMethod;
  final double estimatedAmount;
  final String currency;
  final int dayOfMonth;
  final String? description;
  final bool isActive;
  final DateTime? lastGenerated;
  final DateTime? nextGeneration;
  final String? createdBy;
  final DateTime createdAt;
  final DateTime updatedAt;

  const RecurringBill({
    required this.id,
    required this.propertyId,
    required this.billType,
    required this.frequency,
    required this.allocationMethod,
    required this.estimatedAmount,
    required this.currency,
    required this.dayOfMonth,
    this.description,
    required this.isActive,
    this.lastGenerated,
    this.nextGeneration,
    this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });

  factory RecurringBill.fromJson(Map<String, dynamic> json) {
    return RecurringBill(
      id: json['id'] as String,
      propertyId: json['property_id'] as String,
      billType: BillType.fromJson(json['bill_type'] as String),
      frequency: RecurringFrequency.fromJson(json['frequency'] as String),
      allocationMethod:
          AllocationMethod.fromJson(json['allocation_method'] as String),
      estimatedAmount: (json['estimated_amount'] as num).toDouble(),
      currency: json['currency'] as String,
      dayOfMonth: json['day_of_month'] as int,
      description: json['description'] as String?,
      isActive: json['is_active'] as bool,
      lastGenerated: json['last_generated'] != null
          ? DateTime.parse(json['last_generated'] as String)
          : null,
      nextGeneration: json['next_generation'] != null
          ? DateTime.parse(json['next_generation'] as String)
          : null,
      createdBy: json['created_by'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'property_id': propertyId,
      'bill_type': billType.toJson(),
      'frequency': frequency.toJson(),
      'allocation_method': allocationMethod.toJson(),
      'estimated_amount': estimatedAmount,
      'currency': currency,
      'day_of_month': dayOfMonth,
      'description': description,
      'is_active': isActive,
      'last_generated': lastGenerated?.toIso8601String(),
      'next_generation': nextGeneration?.toIso8601String(),
      'created_by': createdBy,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  RecurringBill copyWith({
    String? id,
    String? propertyId,
    BillType? billType,
    RecurringFrequency? frequency,
    AllocationMethod? allocationMethod,
    double? estimatedAmount,
    String? currency,
    int? dayOfMonth,
    String? description,
    bool? isActive,
    DateTime? lastGenerated,
    DateTime? nextGeneration,
    String? createdBy,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return RecurringBill(
      id: id ?? this.id,
      propertyId: propertyId ?? this.propertyId,
      billType: billType ?? this.billType,
      frequency: frequency ?? this.frequency,
      allocationMethod: allocationMethod ?? this.allocationMethod,
      estimatedAmount: estimatedAmount ?? this.estimatedAmount,
      currency: currency ?? this.currency,
      dayOfMonth: dayOfMonth ?? this.dayOfMonth,
      description: description ?? this.description,
      isActive: isActive ?? this.isActive,
      lastGenerated: lastGenerated ?? this.lastGenerated,
      nextGeneration: nextGeneration ?? this.nextGeneration,
      createdBy: createdBy ?? this.createdBy,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is RecurringBill &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          propertyId == other.propertyId;

  @override
  int get hashCode => id.hashCode ^ propertyId.hashCode;

  @override
  String toString() =>
      'RecurringBill(id: $id, type: ${billType.displayName}, frequency: ${frequency.displayName})';
}
