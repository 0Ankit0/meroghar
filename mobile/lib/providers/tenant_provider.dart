import 'package:flutter/foundation.dart';
import '../models/tenant.dart';
import '../services/api_service.dart';

/// Provider for tenant-related state management
class TenantProvider with ChangeNotifier {
  TenantProvider(this._apiService);
  final ApiService _apiService;

  List<Tenant> _tenants = [];
  Tenant? _selectedTenant;
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Tenant> get tenants => _tenants;
  Tenant? get selectedTenant => _selectedTenant;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Load all tenants for the current user/property
  Future<void> loadTenants({String? propertyId}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      var endpoint = '/api/v1/tenants';
      if (propertyId != null) {
        endpoint += '?property_id=$propertyId';
      }

      final response = await _apiService.get(endpoint);

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['items'] ?? response.data;
        _tenants = data.map((json) => Tenant.fromJson(json)).toList();
      } else {
        _error = 'Failed to load tenants';
      }
    } catch (e) {
      _error = 'Error loading tenants: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Select a tenant
  void selectTenant(Tenant? tenant) {
    _selectedTenant = tenant;
    notifyListeners();
  }

  /// Get tenant by ID
  Tenant? getTenantById(String id) {
    try {
      return _tenants.firstWhere((t) => t.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Get active tenants only
  List<Tenant> get activeTenants =>
      _tenants.where((t) => t.status == 'active').toList();

  /// Clear all data
  void clear() {
    _tenants = [];
    _selectedTenant = null;
    _error = null;
    notifyListeners();
  }
}
