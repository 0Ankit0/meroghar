/// Payment provider for state management.
///
/// Implements T066 from tasks.md.
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:sqflite/sqflite.dart';

import '../models/payment.dart';
import '../services/api_service.dart';
import '../services/database_service.dart';

/// Provider for payment-related operations and state management
class PaymentProvider with ChangeNotifier {
  PaymentProvider({
    required ApiService apiService,
    required DatabaseService databaseService,
  })  : _apiService = apiService,
        _databaseService = databaseService;
  final ApiService _apiService;
  final DatabaseService _databaseService;

  List<Payment> _payments = [];
  TenantBalance? _currentBalance;
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Payment> get payments => _payments;
  TenantBalance? get currentBalance => _currentBalance;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasError => _error != null;

  /// Get payments filtered by various criteria
  List<Payment> getPaymentsByTenant(String tenantId) =>
      _payments.where((p) => p.tenantId == tenantId).toList();

  List<Payment> getPaymentsByProperty(String propertyId) =>
      _payments.where((p) => p.propertyId == propertyId).toList();

  List<Payment> getPaymentsByStatus(PaymentStatus status) =>
      _payments.where((p) => p.status == status).toList();

  List<Payment> getOverduePayments() =>
      _payments.where((p) => p.isOverdue).toList();

  /// Record a new payment
  Future<Payment?> recordPayment({
    required String tenantId,
    required String propertyId,
    required double amount,
    required PaymentMethod paymentMethod,
    required PaymentType paymentType,
    required DateTime paymentDate,
    String currency = 'INR',
    DateTime? paymentPeriodStart,
    DateTime? paymentPeriodEnd,
    String? transactionReference,
    String? notes,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Prepare request data
      final requestData = {
        'tenant_id': tenantId,
        'property_id': propertyId,
        'amount': amount,
        'currency': currency,
        'payment_method': paymentMethod.toJson(),
        'payment_type': paymentType.toJson(),
        'payment_date': paymentDate.toIso8601String().split('T')[0],
        if (paymentPeriodStart != null)
          'payment_period_start':
              paymentPeriodStart.toIso8601String().split('T')[0],
        if (paymentPeriodEnd != null)
          'payment_period_end':
              paymentPeriodEnd.toIso8601String().split('T')[0],
        if (transactionReference != null)
          'transaction_reference': transactionReference,
        if (notes != null) 'notes': notes,
      };

      // Call API
      final response = await _apiService.post(
        '/payments',
        data: requestData,
      );

      // Parse response
      final payment = Payment.fromJson(response.data as Map<String, dynamic>);

      // Save to local database
      await _savePaymentToDatabase(payment);

      // Add to list
      _payments.insert(0, payment);

      notifyListeners();
      return payment;
    } catch (e) {
      _setError('Failed to record payment: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch payments list with optional filters
  Future<void> fetchPayments({
    String? tenantId,
    String? propertyId,
    PaymentType? paymentType,
    PaymentStatus? paymentStatus,
    DateTime? dateFrom,
    DateTime? dateTo,
    int skip = 0,
    int limit = 50,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Build query parameters
      final queryParams = <String, dynamic>{
        'skip': skip,
        'limit': limit,
        if (tenantId != null) 'tenant_id': tenantId,
        if (propertyId != null) 'property_id': propertyId,
        if (paymentType != null) 'payment_type': paymentType.toJson(),
        if (paymentStatus != null) 'payment_status': paymentStatus.toJson(),
        if (dateFrom != null)
          'date_from': dateFrom.toIso8601String().split('T')[0],
        if (dateTo != null) 'date_to': dateTo.toIso8601String().split('T')[0],
      };

      // Call API
      final response = await _apiService.get(
        '/payments',
        queryParameters: queryParams,
      );

      // Parse response
      final data = response.data as Map<String, dynamic>;
      final paymentsList = data['payments'] as List<dynamic>;

      _payments = paymentsList
          .map((json) => Payment.fromJson(json as Map<String, dynamic>))
          .toList();

      // Save to local database
      for (final payment in _payments) {
        await _savePaymentToDatabase(payment);
      }

      notifyListeners();
    } catch (e) {
      _setError('Failed to fetch payments: ${e.toString()}');
      // Try loading from local database as fallback
      await _loadPaymentsFromDatabase();
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch tenant balance
  Future<TenantBalance?> fetchTenantBalance({
    required String tenantId,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Call API
      final response = await _apiService.get(
        '/tenants/$tenantId/balance',
      );

      // Parse response
      final data = response.data as Map<String, dynamic>;
      _currentBalance =
          TenantBalance.fromJson(data['data'] as Map<String, dynamic>);

      notifyListeners();
      return _currentBalance;
    } catch (e) {
      _setError('Failed to fetch balance: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Download payment receipt as PDF bytes
  Future<Uint8List?> downloadReceipt(String paymentId) async {
    _setLoading(true);
    _clearError();

    try {
      // Call API with bytes response type to get PDF file
      final response = await _apiService.get<Uint8List>(
        '/payments/$paymentId/receipt',
        options: Options(responseType: ResponseType.bytes),
      );

      _setLoading(false);

      if (response.isSuccess && response.data != null) {
        return response.data;
      }

      _setError(response.message ?? 'Failed to download receipt');
      return null;
    } catch (e) {
      _setError('Failed to download receipt: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Save payment to local database
  Future<void> _savePaymentToDatabase(Payment payment) async {
    try {
      final db = await _databaseService.database;
      await db.insert(
        'payments',
        payment.toDatabase(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    } catch (e) {
      debugPrint('Error saving payment to database: $e');
    }
  }

  /// Load payments from local database
  Future<void> _loadPaymentsFromDatabase() async {
    try {
      final db = await _databaseService.database;
      final List<Map<String, dynamic>> maps = await db.query(
        'payments',
        orderBy: 'payment_date DESC',
      );

      _payments = maps.map(Payment.fromDatabase).toList();
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading payments from database: $e');
    }
  }

  /// Clear all payments (for logout)
  Future<void> clearPayments() async {
    _payments = [];
    _currentBalance = null;
    _error = null;

    try {
      final db = await _databaseService.database;
      await db.delete('payments');
    } catch (e) {
      debugPrint('Error clearing payments: $e');
    }

    notifyListeners();
  }

  /// Get payment statistics
  Map<String, dynamic> getPaymentStats() {
    final totalPayments = _payments.length;
    final completedPayments =
        _payments.where((p) => p.status == PaymentStatus.completed).length;
    final pendingPayments =
        _payments.where((p) => p.status == PaymentStatus.pending).length;
    final totalAmount = _payments
        .where((p) => p.status == PaymentStatus.completed)
        .fold<double>(0, (sum, p) => sum + p.amount);

    return {
      'total': totalPayments,
      'completed': completedPayments,
      'pending': pendingPayments,
      'totalAmount': totalAmount,
    };
  }

  /// Get payment by ID
  Payment? getPaymentById(String id) {
    try {
      return _payments.firstWhere((p) => p.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Retry failed payment through gateway.
  ///
  /// Implements T123 from tasks.md.
  ///
  /// This method handles retry logic for failed payments:
  /// 1. Checks if payment can be retried (failed status only)
  /// 2. Initiates new payment with same details
  /// 3. Returns payment URL for webview
  Future<Map<String, dynamic>?> retryFailedPayment({
    required String paymentId,
    String? gateway,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Get existing payment
      final payment = getPaymentById(paymentId);

      if (payment == null) {
        throw Exception('Payment not found');
      }

      // Check if payment can be retried (only failed payments)
      if (payment.status != PaymentStatus.failed) {
        throw Exception('Can only retry failed payments. '
            'Current status: ${payment.status.toString()}');
      }

      debugPrint('Retrying failed payment $paymentId');

      // Initiate new payment with same details
      final response = await _apiService.post(
        '/payments/initiate',
        data: {
          'tenant_id': payment.tenantId,
          'amount': payment.amount * 100, // Convert to paisa
          'payment_type': payment.paymentType.toJson(),
          'gateway': gateway ?? 'KHALTI',
        },
      );

      final result = response.data as Map<String, dynamic>;

      _setLoading(false);

      return {
        'payment_url': result['payment_url'],
        'pidx': result['pidx'],
        'expires_at': result['expires_at'],
        'expires_in': result['expires_in'],
      };
    } catch (e) {
      _setError(e.toString());
      _setLoading(false);
      debugPrint('Error retrying payment: $e');
      return null;
    }
  }

  /// Check if payment can be retried
  bool canRetryPayment(String paymentId) {
    final payment = getPaymentById(paymentId);

    if (payment == null) return false;

    // Can only retry failed payments
    return payment.status == PaymentStatus.failed;
  }

  // Private helper methods
  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _setError(String message) {
    _error = message;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
  }
}
