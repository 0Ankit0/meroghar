import 'package:flutter/foundation.dart';

/// Rent collection trend data for a specific month
@immutable
class RentCollectionTrend {
  final DateTime month;
  final double totalCollected;
  final int paymentCount;
  final double completedAmount;
  final double pendingAmount;

  const RentCollectionTrend({
    required this.month,
    required this.totalCollected,
    required this.paymentCount,
    required this.completedAmount,
    required this.pendingAmount,
  });

  factory RentCollectionTrend.fromJson(Map<String, dynamic> json) {
    return RentCollectionTrend(
      month: DateTime.parse(json['month'] as String),
      totalCollected: (json['total_collected'] as num).toDouble(),
      paymentCount: json['payment_count'] as int,
      completedAmount: (json['completed_amount'] as num).toDouble(),
      pendingAmount: (json['pending_amount'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'month': month.toIso8601String(),
      'total_collected': totalCollected,
      'payment_count': paymentCount,
      'completed_amount': completedAmount,
      'pending_amount': pendingAmount,
    };
  }
}

/// Payment status breakdown
@immutable
class PaymentStatusOverview {
  final Map<String, PaymentStatusData> statusBreakdown;
  final int totalCount;
  final double totalAmount;
  final DateRange dateRange;

  const PaymentStatusOverview({
    required this.statusBreakdown,
    required this.totalCount,
    required this.totalAmount,
    required this.dateRange,
  });

  factory PaymentStatusOverview.fromJson(Map<String, dynamic> json) {
    final statusBreakdownJson = json['status_breakdown'] as Map<String, dynamic>;
    final statusBreakdown = <String, PaymentStatusData>{};
    
    statusBreakdownJson.forEach((key, value) {
      statusBreakdown[key] = PaymentStatusData.fromJson(value as Map<String, dynamic>);
    });

    return PaymentStatusOverview(
      statusBreakdown: statusBreakdown,
      totalCount: json['total_count'] as int,
      totalAmount: (json['total_amount'] as num).toDouble(),
      dateRange: DateRange.fromJson(json['date_range'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status_breakdown': statusBreakdown.map((key, value) => MapEntry(key, value.toJson())),
      'total_count': totalCount,
      'total_amount': totalAmount,
      'date_range': dateRange.toJson(),
    };
  }

  PaymentStatusData get completed => statusBreakdown['completed'] ?? const PaymentStatusData(count: 0, amount: 0);
  PaymentStatusData get pending => statusBreakdown['pending'] ?? const PaymentStatusData(count: 0, amount: 0);
  PaymentStatusData get failed => statusBreakdown['failed'] ?? const PaymentStatusData(count: 0, amount: 0);
}

/// Individual payment status data
@immutable
class PaymentStatusData {
  final int count;
  final double amount;

  const PaymentStatusData({
    required this.count,
    required this.amount,
  });

  factory PaymentStatusData.fromJson(Map<String, dynamic> json) {
    return PaymentStatusData(
      count: json['count'] as int,
      amount: (json['amount'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'count': count,
      'amount': amount,
    };
  }
}

/// Date range for analytics
@immutable
class DateRange {
  final DateTime start;
  final DateTime end;

  const DateRange({
    required this.start,
    required this.end,
  });

  factory DateRange.fromJson(Map<String, dynamic> json) {
    return DateRange(
      start: DateTime.parse(json['start'] as String),
      end: DateTime.parse(json['end'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'start': start.toIso8601String(),
      'end': end.toIso8601String(),
    };
  }
}

/// Expense breakdown by bill type
@immutable
class ExpenseBreakdown {
  final String billType;
  final int billCount;
  final double totalAmount;
  final double averageAmount;
  final double percentage;

  const ExpenseBreakdown({
    required this.billType,
    required this.billCount,
    required this.totalAmount,
    required this.averageAmount,
    required this.percentage,
  });

  factory ExpenseBreakdown.fromJson(Map<String, dynamic> json) {
    return ExpenseBreakdown(
      billType: json['bill_type'] as String,
      billCount: json['bill_count'] as int,
      totalAmount: (json['total_amount'] as num).toDouble(),
      averageAmount: (json['average_amount'] as num).toDouble(),
      percentage: (json['percentage'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'bill_type': billType,
      'bill_count': billCount,
      'total_amount': totalAmount,
      'average_amount': averageAmount,
      'percentage': percentage,
    };
  }
}

/// Revenue vs expenses comparison
@immutable
class RevenueExpensesComparison {
  final RevenueData revenue;
  final ExpenseData expenses;
  final double netProfit;
  final double profitMargin;
  final DateRange dateRange;

  const RevenueExpensesComparison({
    required this.revenue,
    required this.expenses,
    required this.netProfit,
    required this.profitMargin,
    required this.dateRange,
  });

  factory RevenueExpensesComparison.fromJson(Map<String, dynamic> json) {
    return RevenueExpensesComparison(
      revenue: RevenueData.fromJson(json['revenue'] as Map<String, dynamic>),
      expenses: ExpenseData.fromJson(json['expenses'] as Map<String, dynamic>),
      netProfit: (json['net_profit'] as num).toDouble(),
      profitMargin: (json['profit_margin'] as num).toDouble(),
      dateRange: DateRange.fromJson(json['date_range'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'revenue': revenue.toJson(),
      'expenses': expenses.toJson(),
      'net_profit': netProfit,
      'profit_margin': profitMargin,
      'date_range': dateRange.toJson(),
    };
  }
}

/// Revenue data
@immutable
class RevenueData {
  final double total;
  final int paymentCount;

  const RevenueData({
    required this.total,
    required this.paymentCount,
  });

  factory RevenueData.fromJson(Map<String, dynamic> json) {
    return RevenueData(
      total: (json['total'] as num).toDouble(),
      paymentCount: json['payment_count'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total': total,
      'payment_count': paymentCount,
    };
  }
}

/// Expense data
@immutable
class ExpenseData {
  final double total;
  final int billCount;

  const ExpenseData({
    required this.total,
    required this.billCount,
  });

  factory ExpenseData.fromJson(Map<String, dynamic> json) {
    return ExpenseData(
      total: (json['total'] as num).toDouble(),
      billCount: json['bill_count'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total': total,
      'bill_count': billCount,
    };
  }
}

/// Property performance data
@immutable
class PropertyPerformance {
  final String propertyId;
  final String propertyName;
  final String propertyAddress;
  final int tenantCount;
  final double totalRevenue;
  final double totalExpenses;
  final double netProfit;
  final double occupancyRate;

  const PropertyPerformance({
    required this.propertyId,
    required this.propertyName,
    required this.propertyAddress,
    required this.tenantCount,
    required this.totalRevenue,
    required this.totalExpenses,
    required this.netProfit,
    required this.occupancyRate,
  });

  factory PropertyPerformance.fromJson(Map<String, dynamic> json) {
    return PropertyPerformance(
      propertyId: json['property_id'] as String,
      propertyName: json['property_name'] as String,
      propertyAddress: json['property_address'] as String,
      tenantCount: json['tenant_count'] as int,
      totalRevenue: (json['total_revenue'] as num).toDouble(),
      totalExpenses: (json['total_expenses'] as num).toDouble(),
      netProfit: (json['net_profit'] as num).toDouble(),
      occupancyRate: (json['occupancy_rate'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'property_id': propertyId,
      'property_name': propertyName,
      'property_address': propertyAddress,
      'tenant_count': tenantCount,
      'total_revenue': totalRevenue,
      'total_expenses': totalExpenses,
      'net_profit': netProfit,
      'occupancy_rate': occupancyRate,
    };
  }
}
