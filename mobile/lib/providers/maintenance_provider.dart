/// Maintenance provider for state management.
library;

import 'package:flutter/foundation.dart';

import '../config/constants.dart';
import '../models/maintenance_request.dart';
import '../services/api_service.dart';

class MaintenanceProvider with ChangeNotifier {
  MaintenanceProvider() : _apiService = ApiService.instance;
  final ApiService _apiService;

  List<MaintenanceRequest> _requests = [];
  bool _isLoading = false;
  String? _error;

  // Getters
  List<MaintenanceRequest> get requests => _requests;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasError => _error != null;

  /// Load all maintenance requests
  Future<void> loadRequests({
    String? propertyId,
    MaintenanceStatus? status,
    MaintenancePriority? priority,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final queryParams = <String, dynamic>{};
      if (propertyId != null) queryParams['property_id'] = propertyId;
      if (status != null) queryParams['status'] = status.value;
      if (priority != null) queryParams['priority'] = priority.value;

      final response = await _apiService.get(
        ApiEndpoints.maintenance,
        queryParameters: queryParams,
      );

      if (response.isSuccess && response.data != null) {
        final List<dynamic> list = response.data['data'] as List;
        _requests = list
            .map((json) => MaintenanceRequest.fromJson(json))
            .toList();
      } else {
        _setError(response.message ?? 'Failed to load requests');
      }
    } catch (e) {
      _setError('Error loading requests: $e');
    } finally {
      _setLoading(false);
    }
  }

  /// Create a new maintenance request
  Future<bool> createRequest({
    required String propertyId,
    required String title,
    required String description,
    required MaintenancePriority priority,
    List<String>? images,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final data = {
        'property_id': propertyId,
        'title': title,
        'description': description,
        'priority': priority.value,
        if (images != null) 'images': images,
      };

      final response = await _apiService.post(
        ApiEndpoints.maintenance,
        data: data,
      );

      if (response.isSuccess) {
        // Refresh list
        await loadRequests(); 
        return true;
      } else {
        _setError(response.message ?? 'Failed to create request');
        return false;
      }
    } catch (e) {
      _setError('Error creating request: $e');
      return false;
    } finally {
      // Don't set loading to false here if successful to prevent UI flicker before nav?
      // Actually standard pattern is to finish loading.
       _setLoading(false);
    }
  }

  /// Update a request
  Future<bool> updateRequest(String id, Map<String, dynamic> data) async {
    _setLoading(true);
    _clearError();

    try {
      final response = await _apiService.patch(
        '${ApiEndpoints.maintenance}/$id',
        data: data,
      );

      if (response.isSuccess) {
        // Update local object or reload
        final index = _requests.indexWhere((r) => r.id == id);
        if (index != -1) {
           _requests[index] = MaintenanceRequest.fromJson(response.data['data']);
           notifyListeners();
        }
        return true;
      } else {
        _setError(response.message ?? 'Failed to update request');
        return false;
      }
    } catch (e) {
      _setError('Error updating request: $e');
      return false;
    } finally {
      _setLoading(false);
    }
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
