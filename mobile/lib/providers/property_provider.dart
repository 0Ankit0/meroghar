import 'package:flutter/foundation.dart';
import '../models/property.dart';
import '../services/api_service.dart';

/// Provider for property-related state management
class PropertyProvider with ChangeNotifier {
  PropertyProvider(this._apiService);
  final ApiService _apiService;

  List<Property> _properties = [];
  Property? _selectedProperty;
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Property> get properties => _properties;
  Property? get selectedProperty => _selectedProperty;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Load all properties for the current user
  Future<void> loadProperties() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.get('/api/v1/properties');

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['items'] ?? response.data;
        _properties = data.map((json) => Property.fromJson(json)).toList();

        // Set first property as selected if none selected
        if (_selectedProperty == null && _properties.isNotEmpty) {
          _selectedProperty = _properties.first;
        }
      } else {
        _error = 'Failed to load properties';
      }
    } catch (e) {
      _error = 'Error loading properties: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Select a property
  void selectProperty(Property? property) {
    _selectedProperty = property;
    notifyListeners();
  }

  /// Get property by ID
  Property? getPropertyById(String id) {
    try {
      return _properties.firstWhere((p) => p.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Clear all data
  void clear() {
    _properties = [];
    _selectedProperty = null;
    _error = null;
    notifyListeners();
  }
}
