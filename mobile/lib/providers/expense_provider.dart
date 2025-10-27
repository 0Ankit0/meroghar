/// Expense provider for state management.
///
/// Implements T135 from tasks.md.
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:sqflite/sqflite.dart';

import '../models/expense.dart';
import '../services/api_service.dart';
import '../services/database_service.dart';

/// Provider for expense-related operations and state management
class ExpenseProvider with ChangeNotifier {
  final ApiService _apiService;
  final DatabaseService _databaseService;

  List<Expense> _expenses = [];
  ExpenseSummary? _expenseSummary;
  bool _isLoading = false;
  String? _error;

  ExpenseProvider({
    required ApiService apiService,
    required DatabaseService databaseService,
  })  : _apiService = apiService,
        _databaseService = databaseService;

  // Getters
  List<Expense> get expenses => _expenses;
  ExpenseSummary? get expenseSummary => _expenseSummary;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasError => _error != null;

  /// Get expenses filtered by various criteria
  List<Expense> getExpensesByProperty(String propertyId) {
    return _expenses.where((e) => e.propertyId == propertyId).toList();
  }

  List<Expense> getExpensesByCategory(ExpenseCategory category) {
    return _expenses.where((e) => e.category == category).toList();
  }

  List<Expense> getExpensesByStatus(ExpenseStatus status) {
    return _expenses.where((e) => e.status == status).toList();
  }

  List<Expense> getPendingExpenses() {
    return _expenses.where((e) => e.status == ExpenseStatus.pending).toList();
  }

  /// Record a new expense
  Future<Expense?> recordExpense({
    required String propertyId,
    required double amount,
    required ExpenseCategory category,
    required DateTime expenseDate,
    required String description,
    String? vendorName,
    String? invoiceNumber,
    String? paidBy,
    bool isReimbursable = true,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Prepare request data
      final requestData = {
        'property_id': propertyId,
        'amount': amount,
        'category': category.toJson(),
        'expense_date': expenseDate.toIso8601String().split('T')[0],
        'description': description,
        if (vendorName != null) 'vendor_name': vendorName,
        if (invoiceNumber != null) 'invoice_number': invoiceNumber,
        if (paidBy != null) 'paid_by': paidBy,
        'is_reimbursable': isReimbursable,
      };

      // Call API
      final response = await _apiService.post(
        '/expenses',
        data: requestData,
      );

      // Parse response
      final expense = Expense.fromJson(response.data as Map<String, dynamic>);

      // Save to local database
      await _saveExpenseToDatabase(expense);

      // Add to list
      _expenses.insert(0, expense);

      notifyListeners();
      return expense;
    } catch (e) {
      _setError('Failed to record expense: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Upload receipt for an expense
  Future<Expense?> uploadReceipt({
    required String expenseId,
    required File receiptFile,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Prepare multipart form data
      final fileName = receiptFile.path.split('/').last;
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          receiptFile.path,
          filename: fileName,
        ),
      });

      // Call API
      final response = await _apiService.post(
        '/expenses/$expenseId/receipt',
        data: formData,
      );

      // Parse response
      final expense = Expense.fromJson(response.data as Map<String, dynamic>);

      // Update in local database
      await _saveExpenseToDatabase(expense);

      // Update in list
      final index = _expenses.indexWhere((e) => e.id == expenseId);
      if (index != -1) {
        _expenses[index] = expense;
      }

      notifyListeners();
      return expense;
    } catch (e) {
      _setError('Failed to upload receipt: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch expenses list with optional filters
  Future<void> fetchExpenses({
    String? propertyId,
    ExpenseCategory? category,
    ExpenseStatus? status,
    DateTime? startDate,
    DateTime? endDate,
    int page = 1,
    int pageSize = 50,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Build query parameters
      final queryParams = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
        if (propertyId != null) 'property_id': propertyId,
        if (category != null) 'category': category.toJson(),
        if (status != null) 'status': status.toJson(),
        if (startDate != null)
          'start_date': startDate.toIso8601String().split('T')[0],
        if (endDate != null)
          'end_date': endDate.toIso8601String().split('T')[0],
      };

      // Call API
      final response = await _apiService.get(
        '/expenses',
        queryParameters: queryParams,
      );

      // Parse response
      final responseData = response.data as Map<String, dynamic>;
      final expensesList = (responseData['expenses'] as List)
          .map((json) => Expense.fromJson(json as Map<String, dynamic>))
          .toList();

      // Save to local database
      for (final expense in expensesList) {
        await _saveExpenseToDatabase(expense);
      }

      // Update list
      if (page == 1) {
        _expenses = expensesList;
      } else {
        _expenses.addAll(expensesList);
      }

      notifyListeners();
    } catch (e) {
      _setError('Failed to fetch expenses: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }

  /// Approve or reject an expense
  Future<Expense?> approveExpense({
    required String expenseId,
    required ExpenseStatus status,
    String? rejectionReason,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Prepare request data
      final requestData = {
        'status': status.toJson(),
        if (rejectionReason != null) 'rejection_reason': rejectionReason,
      };

      // Call API
      final response = await _apiService.patch(
        '/expenses/$expenseId/approve',
        data: requestData,
      );

      // Parse response
      final expense = Expense.fromJson(response.data as Map<String, dynamic>);

      // Update in local database
      await _saveExpenseToDatabase(expense);

      // Update in list
      final index = _expenses.indexWhere((e) => e.id == expenseId);
      if (index != -1) {
        _expenses[index] = expense;
      }

      notifyListeners();
      return expense;
    } catch (e) {
      _setError('Failed to approve expense: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Mark expense as reimbursed
  Future<Expense?> markReimbursed({
    required String expenseId,
    DateTime? reimbursedDate,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Prepare request data
      final requestData = {
        if (reimbursedDate != null)
          'reimbursed_date': reimbursedDate.toIso8601String().split('T')[0],
      };

      // Call API
      final response = await _apiService.patch(
        '/expenses/$expenseId/reimburse',
        data: requestData,
      );

      // Parse response
      final expense = Expense.fromJson(response.data as Map<String, dynamic>);

      // Update in local database
      await _saveExpenseToDatabase(expense);

      // Update in list
      final index = _expenses.indexWhere((e) => e.id == expenseId);
      if (index != -1) {
        _expenses[index] = expense;
      }

      notifyListeners();
      return expense;
    } catch (e) {
      _setError('Failed to mark expense as reimbursed: ${e.toString()}');
      return null;
    } finally {
      _setLoading(false);
    }
  }

  /// Fetch expense report/summary
  Future<void> fetchExpenseReport({
    String? propertyId,
    DateTime? startDate,
    DateTime? endDate,
    ExpenseCategory? category,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      // Build query parameters
      final queryParams = <String, dynamic>{
        if (propertyId != null) 'property_id': propertyId,
        if (startDate != null)
          'start_date': startDate.toIso8601String().split('T')[0],
        if (endDate != null)
          'end_date': endDate.toIso8601String().split('T')[0],
        if (category != null) 'category': category.toJson(),
      };

      // Call API
      final response = await _apiService.get(
        '/reports/expenses',
        queryParameters: queryParams,
      );

      // Parse response
      _expenseSummary = ExpenseSummary.fromJson(
        response.data as Map<String, dynamic>,
      );

      notifyListeners();
    } catch (e) {
      _setError('Failed to fetch expense report: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }

  /// Load expenses from local database
  Future<void> loadExpensesFromDatabase({String? propertyId}) async {
    try {
      final db = await _databaseService.database;

      String query = 'SELECT * FROM expenses';
      List<dynamic> arguments = [];

      if (propertyId != null) {
        query += ' WHERE property_id = ?';
        arguments.add(propertyId);
      }

      query += ' ORDER BY expense_date DESC';

      final List<Map<String, dynamic>> maps =
          await db.rawQuery(query, arguments);

      _expenses = maps.map((map) => Expense.fromJson(map)).toList();
      notifyListeners();
    } catch (e) {
      _setError('Failed to load expenses from database: ${e.toString()}');
    }
  }

  /// Save expense to local database
  Future<void> _saveExpenseToDatabase(Expense expense) async {
    try {
      final db = await _databaseService.database;

      await db.insert(
        'expenses',
        expense.toJson(),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    } catch (e) {
      debugPrint('Failed to save expense to database: $e');
    }
  }

  /// Clear expenses
  void clearExpenses() {
    _expenses = [];
    _expenseSummary = null;
    notifyListeners();
  }

  // Private helper methods
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _error = error;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
  }
}
