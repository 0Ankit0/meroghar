import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../models/analytics.dart';
import '../services/api_service.dart';

/// Provider for analytics data and chart state
/// Implements T102 from tasks.md
class AnalyticsProvider with ChangeNotifier {
  AnalyticsProvider(this._apiService);
  final ApiService _apiService;

  List<RentCollectionTrend> _rentTrends = [];
  PaymentStatusOverview? _paymentStatus;
  List<ExpenseBreakdown> _expenseBreakdown = [];
  RevenueExpensesComparison? _revenueExpenses;
  List<PropertyPerformance> _propertyPerformance = [];

  bool _isLoading = false;
  String? _error;

  // Getters
  List<RentCollectionTrend> get rentTrends => _rentTrends;
  PaymentStatusOverview? get paymentStatus => _paymentStatus;
  List<ExpenseBreakdown> get expenseBreakdown => _expenseBreakdown;
  RevenueExpensesComparison? get revenueExpenses => _revenueExpenses;
  List<PropertyPerformance> get propertyPerformance => _propertyPerformance;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Fetch rent collection trends
  Future<void> fetchRentCollectionTrends({
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (propertyId != null) queryParams['property_id'] = propertyId;
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
      }

      final response = await _apiService.get(
        '/analytics/rent-trends',
        queryParameters: queryParams,
      );

      _rentTrends = (response.data as List)
          .map((json) =>
              RentCollectionTrend.fromJson(json as Map<String, dynamic>))
          .toList();

      _error = null;
    } on DioException catch (e) {
      _error = e.response?.data['detail'] ?? 'Failed to fetch rent trends';
      debugPrint('Error fetching rent trends: $_error');
    } catch (e) {
      _error = 'An unexpected error occurred';
      debugPrint('Unexpected error fetching rent trends: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch payment status overview
  Future<void> fetchPaymentStatusOverview({
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (propertyId != null) queryParams['property_id'] = propertyId;
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
      }

      final response = await _apiService.get(
        '/analytics/payment-status',
        queryParameters: queryParams,
      );

      _paymentStatus =
          PaymentStatusOverview.fromJson(response.data as Map<String, dynamic>);
      _error = null;
    } on DioException catch (e) {
      _error = e.response?.data['detail'] ?? 'Failed to fetch payment status';
      debugPrint('Error fetching payment status: $_error');
    } catch (e) {
      _error = 'An unexpected error occurred';
      debugPrint('Unexpected error fetching payment status: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch expense breakdown
  Future<void> fetchExpenseBreakdown({
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (propertyId != null) queryParams['property_id'] = propertyId;
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
      }

      final response = await _apiService.get(
        '/analytics/expense-breakdown',
        queryParameters: queryParams,
      );

      _expenseBreakdown = (response.data as List)
          .map(
              (json) => ExpenseBreakdown.fromJson(json as Map<String, dynamic>))
          .toList();

      _error = null;
    } on DioException catch (e) {
      _error =
          e.response?.data['detail'] ?? 'Failed to fetch expense breakdown';
      debugPrint('Error fetching expense breakdown: $_error');
    } catch (e) {
      _error = 'An unexpected error occurred';
      debugPrint('Unexpected error fetching expense breakdown: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch revenue vs expenses comparison
  Future<void> fetchRevenueVsExpenses({
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (propertyId != null) queryParams['property_id'] = propertyId;
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
      }

      final response = await _apiService.get(
        '/analytics/revenue-expenses',
        queryParameters: queryParams,
      );

      _revenueExpenses = RevenueExpensesComparison.fromJson(
          response.data as Map<String, dynamic>);
      _error = null;
    } on DioException catch (e) {
      _error =
          e.response?.data['detail'] ?? 'Failed to fetch revenue vs expenses';
      debugPrint('Error fetching revenue vs expenses: $_error');
    } catch (e) {
      _error = 'An unexpected error occurred';
      debugPrint('Unexpected error fetching revenue vs expenses: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch property performance comparison
  Future<void> fetchPropertyPerformance({
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
      }

      final response = await _apiService.get(
        '/analytics/property-performance',
        queryParameters: queryParams,
      );

      _propertyPerformance = (response.data as List)
          .map((json) =>
              PropertyPerformance.fromJson(json as Map<String, dynamic>))
          .toList();

      _error = null;
    } on DioException catch (e) {
      _error =
          e.response?.data['detail'] ?? 'Failed to fetch property performance';
      debugPrint('Error fetching property performance: $_error');
    } catch (e) {
      _error = 'An unexpected error occurred';
      debugPrint('Unexpected error fetching property performance: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch all analytics data at once
  Future<void> fetchAllAnalytics({
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    await Future.wait([
      fetchRentCollectionTrends(
          propertyId: propertyId, startDate: startDate, endDate: endDate),
      fetchPaymentStatusOverview(
          propertyId: propertyId, startDate: startDate, endDate: endDate),
      fetchExpenseBreakdown(
          propertyId: propertyId, startDate: startDate, endDate: endDate),
      fetchRevenueVsExpenses(
          propertyId: propertyId, startDate: startDate, endDate: endDate),
      if (propertyId == null)
        fetchPropertyPerformance(startDate: startDate, endDate: endDate),
    ]);
  }

  /// Export analytics data
  Future<Map<String, dynamic>?> exportAnalytics({
    required String reportType,
    String format = 'excel',
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'report_type': reportType,
        'format': format,
      };
      if (propertyId != null) queryParams['property_id'] = propertyId;
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String().split('T')[0];
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String().split('T')[0];
      }

      final response = await _apiService.post(
        '/analytics/export',
        queryParameters: queryParams,
      );

      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      _error = e.response?.data['detail'] ?? 'Failed to export analytics';
      debugPrint('Error exporting analytics: $_error');
      notifyListeners();
      return null;
    } catch (e) {
      _error = 'An unexpected error occurred';
      debugPrint('Unexpected error exporting analytics: $e');
      notifyListeners();
      return null;
    }
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Reset all data
  void reset() {
    _rentTrends = [];
    _paymentStatus = null;
    _expenseBreakdown = [];
    _revenueExpenses = null;
    _propertyPerformance = [];
    _error = null;
    _isLoading = false;
    notifyListeners();
  }
}
