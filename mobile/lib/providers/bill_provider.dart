/// Bill provider for state management.
///
/// Implements T088 from tasks.md.
library;

import 'package:flutter/foundation.dart';
import 'package:sqflite/sqflite.dart';

import '../models/bill.dart';
import '../services/api_service.dart';
import '../services/database_service.dart';

/// Provider for bill-related operations and state management
class BillProvider with ChangeNotifier {
  BillProvider({
    required ApiService apiService,
    required DatabaseService databaseService,
  })  : _apiService = apiService,
        _databaseService = databaseService;
  final ApiService _apiService;
  final DatabaseService _databaseService;

  List<Bill> _bills = [];
  List<RecurringBill> _recurringBills = [];
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Bill> get bills => _bills;
  List<RecurringBill> get recurringBills => _recurringBills;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasError => _error != null;

  /// Get bills filtered by various criteria
  List<Bill> getBillsByProperty(String propertyId) =>
      _bills.where((b) => b.propertyId == propertyId).toList();

  List<Bill> getBillsByType(BillType type) =>
      _bills.where((b) => b.billType == type).toList();

  List<Bill> getBillsByStatus(BillStatus status) =>
      _bills.where((b) => b.status == status).toList();

  List<Bill> getOverdueBills() => _bills.where((b) => b.isOverdue).toList();

  List<Bill> getPendingBills() => _bills
      .where((b) =>
          b.status == BillStatus.pending ||
          b.status == BillStatus.partiallyPaid)
      .toList();

  /// Get bills allocated to a specific tenant
  List<Bill> getBillsForTenant(String tenantId) => _bills
      .where((b) => b.allocations.any((alloc) => alloc.tenantId == tenantId))
      .toList();

  /// Get unpaid allocations for a tenant
  List<BillAllocation> getUnpaidAllocationsForTenant(String tenantId) {
    final allocations = <BillAllocation>[];
    for (final bill in _bills) {
      for (final alloc in bill.allocations) {
        if (alloc.tenantId == tenantId && !alloc.isPaid) {
          allocations.add(alloc);
        }
      }
    }
    return allocations;
  }

  /// Calculate total unpaid amount for a tenant
  double getTotalUnpaidForTenant(String tenantId) =>
      getUnpaidAllocationsForTenant(tenantId)
          .fold(0, (sum, alloc) => sum + alloc.allocatedAmount);

  /// Create a new bill
  Future<Bill?> createBill({
    required String propertyId,
    required BillType billType,
    required double totalAmount,
    required DateTime periodStart,
    required DateTime periodEnd,
    required DateTime dueDate,
    AllocationMethod allocationMethod = AllocationMethod.equal,
    String currency = 'INR',
    String? description,
    String? billNumber,
    List<Map<String, dynamic>>? customAllocations,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Prepare request data
      final requestData = {
        'property_id': propertyId,
        'bill_type': billType.toJson(),
        'total_amount': totalAmount,
        'currency': currency,
        'period_start': periodStart.toIso8601String().split('T')[0],
        'period_end': periodEnd.toIso8601String().split('T')[0],
        'due_date': dueDate.toIso8601String().split('T')[0],
        'allocation_method': allocationMethod.toJson(),
        if (description != null) 'description': description,
        if (billNumber != null) 'bill_number': billNumber,
      };

      // Call API
      final response = await _apiService.post(
        '/bills',
        data: requestData,
      );

      // Parse response
      final bill = Bill.fromJson(response.data as Map<String, dynamic>);

      // Save to local database
      await _saveBillToDatabase(bill);

      // Add to list
      _bills.insert(0, bill);

      notifyListeners();
      return bill;
    } catch (e) {
      _setError('Failed to create bill: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch bills list with optional filters
  Future<void> fetchBills({
    String? propertyId,
    BillType? billType,
    BillStatus? status,
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
        if (propertyId != null) 'property_id': propertyId,
        if (billType != null) 'bill_type': billType.toJson(),
        if (status != null) 'status': status.toJson(),
      };

      // Call API
      final response = await _apiService.get(
        '/bills',
        queryParameters: queryParams,
      );

      // Parse response
      final data = response.data as Map<String, dynamic>;
      final billsList = data['bills'] as List;

      _bills = billsList
          .map((json) => Bill.fromJson(json as Map<String, dynamic>))
          .toList();

      // Save to local database
      await _saveBillsToDatabase(_bills);

      notifyListeners();
    } catch (e) {
      _setError('Failed to fetch bills: ${e.toString()}');
      // Load from local database on error
      await _loadBillsFromDatabase();
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch a single bill by ID
  Future<Bill?> fetchBillById(String billId) async {
    _setLoading(true);
    _clearError();

    try {
      final response = await _apiService.get('/bills/$billId');

      final bill = Bill.fromJson(response.data as Map<String, dynamic>);

      // Update in list if exists
      final index = _bills.indexWhere((b) => b.id == billId);
      if (index != -1) {
        _bills[index] = bill;
      } else {
        _bills.insert(0, bill);
      }

      // Save to database
      await _saveBillToDatabase(bill);

      notifyListeners();
      return bill;
    } catch (e) {
      _setError('Failed to fetch bill: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Update a bill
  Future<Bill?> updateBill({
    required String billId,
    BillStatus? status,
    double? totalAmount,
    DateTime? dueDate,
    String? description,
    String? billNumber,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final requestData = <String, dynamic>{
        if (status != null) 'status': status.toJson(),
        if (totalAmount != null) 'total_amount': totalAmount,
        if (dueDate != null)
          'due_date': dueDate.toIso8601String().split('T')[0],
        if (description != null) 'description': description,
        if (billNumber != null) 'bill_number': billNumber,
      };

      final response = await _apiService.patch(
        '/bills/$billId',
        data: requestData,
      );

      final bill = Bill.fromJson(response.data as Map<String, dynamic>);

      // Update in list
      final index = _bills.indexWhere((b) => b.id == billId);
      if (index != -1) {
        _bills[index] = bill;
      }

      // Update database
      await _saveBillToDatabase(bill);

      notifyListeners();
      return bill;
    } catch (e) {
      _setError('Failed to update bill: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Update a bill allocation (e.g., mark as paid)
  Future<BillAllocation?> updateAllocation({
    required String billId,
    required String allocationId,
    double? allocatedAmount,
    double? percentage,
    bool? isPaid,
    String? paymentId,
    String? notes,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final requestData = <String, dynamic>{
        if (allocatedAmount != null) 'allocated_amount': allocatedAmount,
        if (percentage != null) 'percentage': percentage,
        if (isPaid != null) 'is_paid': isPaid,
        if (paymentId != null) 'payment_id': paymentId,
        if (notes != null) 'notes': notes,
      };

      final response = await _apiService.patch(
        '/bills/$billId/allocations/$allocationId',
        data: requestData,
      );

      final allocation =
          BillAllocation.fromJson(response.data as Map<String, dynamic>);

      // Refresh bill to get updated status
      await fetchBillById(billId);

      notifyListeners();
      return allocation;
    } catch (e) {
      _setError('Failed to update allocation: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Mark allocation as paid
  Future<bool> markAllocationAsPaid({
    required String billId,
    required String allocationId,
    String? paymentId,
  }) async {
    final allocation = await updateAllocation(
      billId: billId,
      allocationId: allocationId,
      isPaid: true,
      paymentId: paymentId,
    );
    return allocation != null;
  }

  /// Create a recurring bill template
  Future<RecurringBill?> createRecurringBill({
    required String propertyId,
    required BillType billType,
    required RecurringFrequency frequency,
    required double estimatedAmount,
    required int dayOfMonth,
    AllocationMethod allocationMethod = AllocationMethod.equal,
    String currency = 'INR',
    String? description,
    bool isActive = true,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final requestData = {
        'property_id': propertyId,
        'bill_type': billType.toJson(),
        'frequency': frequency.toJson(),
        'allocation_method': allocationMethod.toJson(),
        'estimated_amount': estimatedAmount,
        'currency': currency,
        'day_of_month': dayOfMonth,
        if (description != null) 'description': description,
        'is_active': isActive,
      };

      final response = await _apiService.post(
        '/bills/recurring',
        data: requestData,
      );

      final recurringBill =
          RecurringBill.fromJson(response.data as Map<String, dynamic>);

      _recurringBills.insert(0, recurringBill);

      notifyListeners();
      return recurringBill;
    } catch (e) {
      _setError('Failed to create recurring bill: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch recurring bills
  Future<void> fetchRecurringBills({
    String? propertyId,
    bool? isActive,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final queryParams = <String, dynamic>{
        if (propertyId != null) 'property_id': propertyId,
        if (isActive != null) 'is_active': isActive,
      };

      final response = await _apiService.get(
        '/bills/recurring',
        queryParameters: queryParams,
      );

      final data = response.data as Map<String, dynamic>;
      final billsList = data['recurring_bills'] as List;

      _recurringBills = billsList
          .map((json) => RecurringBill.fromJson(json as Map<String, dynamic>))
          .toList();

      notifyListeners();
    } catch (e) {
      _setError('Failed to fetch recurring bills: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }

  /// Update recurring bill template
  Future<RecurringBill?> updateRecurringBill({
    required String recurringBillId,
    double? estimatedAmount,
    int? dayOfMonth,
    String? description,
    bool? isActive,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final requestData = <String, dynamic>{
        if (estimatedAmount != null) 'estimated_amount': estimatedAmount,
        if (dayOfMonth != null) 'day_of_month': dayOfMonth,
        if (description != null) 'description': description,
        if (isActive != null) 'is_active': isActive,
      };

      final response = await _apiService.patch(
        '/bills/recurring/$recurringBillId',
        data: requestData,
      );

      final recurringBill =
          RecurringBill.fromJson(response.data as Map<String, dynamic>);

      final index =
          _recurringBills.indexWhere((rb) => rb.id == recurringBillId);
      if (index != -1) {
        _recurringBills[index] = recurringBill;
      }

      notifyListeners();
      return recurringBill;
    } catch (e) {
      _setError('Failed to update recurring bill: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Generate bills from recurring templates
  Future<List<Bill>> generateRecurringBills({String? recurringBillId}) async {
    _setLoading(true);
    _clearError();

    try {
      final queryParams = <String, dynamic>{
        if (recurringBillId != null) 'recurring_bill_id': recurringBillId,
      };

      final response = await _apiService.post(
        '/bills/recurring/generate',
        queryParameters: queryParams,
      );

      final data = response.data as Map<String, dynamic>;
      final billsList = data['bills'] as List;

      final generatedBills = billsList
          .map((json) => Bill.fromJson(json as Map<String, dynamic>))
          .toList();

      // Add to bills list
      _bills.insertAll(0, generatedBills);

      // Save to database
      await _saveBillsToDatabase(generatedBills);

      notifyListeners();
      return generatedBills;
    } catch (e) {
      _setError('Failed to generate recurring bills: ${e.toString()}');
      return [];
    } finally {
      _setLoading(false);
    }
  }

  // ==================== Local Database Operations ====================

  Future<void> _saveBillToDatabase(Bill bill) async {
    try {
      final db = await _databaseService.database;
      await db.insert(
        'bills',
        bill.toJson(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );

      // Save allocations
      for (final allocation in bill.allocations) {
        await db.insert(
          'bill_allocations',
          allocation.toJson(),
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    } catch (e) {
      debugPrint('Error saving bill to database: $e');
    }
  }

  Future<void> _saveBillsToDatabase(List<Bill> bills) async {
    for (final bill in bills) {
      await _saveBillToDatabase(bill);
    }
  }

  Future<void> _loadBillsFromDatabase() async {
    try {
      final db = await _databaseService.database;
      final billMaps = await db.query('bills', orderBy: 'created_at DESC');

      _bills = [];
      for (final billMap in billMaps) {
        // Load allocations
        final allocationMaps = await db.query(
          'bill_allocations',
          where: 'bill_id = ?',
          whereArgs: [billMap['id']],
        );

        final allocations =
            allocationMaps.map(BillAllocation.fromJson).toList();

        final billData = Map<String, dynamic>.from(billMap);
        billData['allocations'] = allocations.map((a) => a.toJson()).toList();

        _bills.add(Bill.fromJson(billData));
      }

      notifyListeners();
    } catch (e) {
      debugPrint('Error loading bills from database: $e');
    }
  }

  // ==================== Private Helper Methods ====================

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

  /// Clear all data (for logout)
  Future<void> clear() async {
    _bills = [];
    _recurringBills = [];
    _error = null;
    _isLoading = false;
    notifyListeners();

    // Clear database
    try {
      final db = await _databaseService.database;
      await db.delete('bills');
      await db.delete('bill_allocations');
    } catch (e) {
      debugPrint('Error clearing bills from database: $e');
    }
  }
}
