/// Authentication provider for state management.
///
/// Implements T043 from tasks.md.
library;

import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/secure_storage_service.dart';

/// Authentication state.
enum AuthState {
  initial,
  loading,
  authenticated,
  unauthenticated,
  error,
}

/// Auth provider with ChangeNotifier for state management.
class AuthProvider with ChangeNotifier {
  final ApiService _apiService;
  final SecureStorageService _storageService;

  AuthState _state = AuthState.initial;
  User? _currentUser;
  String? _errorMessage;
  String? _accessToken;
  String? _refreshToken;

  AuthProvider({
    required ApiService apiService,
    required SecureStorageService storageService,
  })  : _apiService = apiService,
        _storageService = storageService;

  // Getters
  AuthState get state => _state;
  User? get currentUser => _currentUser;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _state == AuthState.authenticated;
  bool get isLoading => _state == AuthState.loading;

  /// Initialize auth state from stored tokens.
  Future<void> initialize() async {
    _setState(AuthState.loading);

    try {
      // Try to load stored tokens
      _accessToken = await _storageService.getAccessToken();
      _refreshToken = await _storageService.getRefreshToken();

      if (_accessToken != null && _refreshToken != null) {
        // Tokens exist, mark as authenticated
        // Note: This would require a /me endpoint in the backend to fetch user profile
        // For now, we'll just mark as authenticated
        _setState(AuthState.authenticated);
      } else {
        _setState(AuthState.unauthenticated);
      }
    } catch (e) {
      _setError('Failed to initialize auth: $e');
    }
  }

  /// Register a new user.
  Future<bool> register({
    required String email,
    required String password,
    required String fullName,
    required UserRole role,
    String? phone,
  }) async {
    _setState(AuthState.loading);

    try {
      final response = await _apiService.post(
        '/api/v1/auth/register',
        data: {
          'email': email,
          'password': password,
          'full_name': fullName,
          'role': role.value,
          if (phone != null) 'phone': phone,
        },
      );

      if (response.isSuccess && response.data != null) {
        await _handleAuthResponse(response.data as Map<String, dynamic>);
        return true;
      } else {
        _setError(response.message ?? 'Registration failed');
        return false;
      }
    } catch (e) {
      _setError('Registration failed: $e');
      return false;
    }
  }

  /// Login existing user.
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _setState(AuthState.loading);

    try {
      final response = await _apiService.post(
        '/api/v1/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      if (response.isSuccess && response.data != null) {
        await _handleAuthResponse(response.data as Map<String, dynamic>);
        return true;
      } else {
        _setError(response.message ?? 'Login failed');
        return false;
      }
    } catch (e) {
      _setError('Login failed: $e');
      return false;
    }
  }

  /// Logout user.
  Future<void> logout() async {
    _setState(AuthState.loading);

    try {
      // Call logout endpoint (optional, just for logging)
      await _apiService.post('/api/v1/auth/logout');
    } catch (e) {
      // Ignore errors on logout endpoint
      debugPrint('Logout endpoint error: $e');
    }

    // Clear local state
    await _clearAuthState();
    _setState(AuthState.unauthenticated);
  }

  /// Refresh access token using refresh token.
  Future<bool> refreshAccessToken() async {
    if (_refreshToken == null) {
      await logout();
      return false;
    }

    try {
      final response = await _apiService.post(
        '/api/v1/auth/refresh',
        data: {
          'refresh_token': _refreshToken,
        },
      );

      if (response.isSuccess && response.data != null) {
        final data = response.data as Map<String, dynamic>;
        _accessToken = data['access_token'] as String;
        _refreshToken = data['refresh_token'] as String;

        // Store new tokens
        await _storageService.saveAccessToken(_accessToken!);
        await _storageService.saveRefreshToken(_refreshToken!);

        return true;
      } else {
        await logout();
        return false;
      }
    } catch (e) {
      debugPrint('Token refresh failed: $e');
      await logout();
      return false;
    }
  }

  /// Handle authentication response (register/login).
  Future<void> _handleAuthResponse(Map<String, dynamic> data) async {
    _accessToken = data['access_token'] as String;
    _refreshToken = data['refresh_token'] as String;

    // Store tokens (API service will pick them up automatically via interceptor)
    await _storageService.saveAccessToken(_accessToken!);
    await _storageService.saveRefreshToken(_refreshToken!);

    // Create user object
    _currentUser = User(
      id: data['user_id'] as String,
      email: data['email'] as String,
      fullName: data['full_name'] as String,
      role: UserRole.fromString(data['role'] as String),
      isActive: true,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    _setState(AuthState.authenticated);
  }

  /// Clear authentication state.
  Future<void> _clearAuthState() async {
    _currentUser = null;
    _accessToken = null;
    _refreshToken = null;
    _errorMessage = null;

    await _storageService.deleteAccessToken();
    await _storageService.deleteRefreshToken();
  }

  /// Set state and notify listeners.
  void _setState(AuthState newState) {
    _state = newState;
    if (newState != AuthState.error) {
      _errorMessage = null;
    }
    notifyListeners();
  }

  /// Set error state.
  void _setError(String message) {
    _errorMessage = message;
    _state = AuthState.error;
    notifyListeners();
  }

  /// Clear error message.
  void clearError() {
    _errorMessage = null;
    if (_state == AuthState.error) {
      _state = _currentUser != null
          ? AuthState.authenticated
          : AuthState.unauthenticated;
    }
    notifyListeners();
  }
}
