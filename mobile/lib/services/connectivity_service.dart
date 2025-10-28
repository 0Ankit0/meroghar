/// Connectivity service with automatic sync.
/// Implements T152 from tasks.md.
library;

import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';

import '../services/sync_service.dart';

/// Service for monitoring network connectivity and auto-syncing.
///
/// Features:
/// - Monitor connectivity changes
/// - Auto-sync when connection restored
/// - Debounce multiple rapid connection changes
class ConnectivityService {
  factory ConnectivityService() => instance;

  ConnectivityService._internal();
  static final ConnectivityService instance = ConnectivityService._internal();

  final Connectivity _connectivity = Connectivity();
  final SyncService _syncService = SyncService.instance;

  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;
  Timer? _syncDebounceTimer;

  bool _isConnected = false;
  bool _autoSyncEnabled = true;

  // Debounce duration to avoid multiple rapid syncs
  static const Duration _syncDebounce = Duration(seconds: 3);

  // Stream controller for connectivity status
  final _connectivityController = StreamController<bool>.broadcast();

  /// Get current connectivity status.
  bool get isConnected => _isConnected;

  /// Get/set auto-sync enabled status.
  bool get autoSyncEnabled => _autoSyncEnabled;
  set autoSyncEnabled(bool enabled) {
    _autoSyncEnabled = enabled;
  }

  /// Stream of connectivity status changes.
  Stream<bool> get connectivityStream => _connectivityController.stream;

  /// Initialize connectivity monitoring.
  Future<void> initialize() async {
    // Check initial connectivity
    final result = await _connectivity.checkConnectivity();
    _updateConnectivityStatus(result);

    // Listen to connectivity changes
    _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
      _updateConnectivityStatus,
      onError: (error) {
        // Handle connectivity stream errors
        _isConnected = false;
        _connectivityController.add(false);
      },
    );
  }

  /// Update connectivity status.
  void _updateConnectivityStatus(List<ConnectivityResult> results) {
    final wasConnected = _isConnected;

    // Check if any result indicates connection
    _isConnected = results.any(
      (result) => result != ConnectivityResult.none,
    );

    // Notify listeners
    _connectivityController.add(_isConnected);

    // Trigger auto-sync if connection restored
    if (!wasConnected && _isConnected && _autoSyncEnabled) {
      _scheduleSyncWithDebounce();
    }
  }

  /// Schedule sync with debounce to avoid rapid successive syncs.
  void _scheduleSyncWithDebounce() {
    // Cancel existing timer if any
    _syncDebounceTimer?.cancel();

    // Schedule new sync after debounce period
    _syncDebounceTimer = Timer(_syncDebounce, () {
      if (_isConnected && _autoSyncEnabled) {
        _performAutoSync();
      }
    });
  }

  /// Perform automatic sync.
  Future<void> _performAutoSync() async {
    try {
      await _syncService.sync();
    } catch (e) {
      // Auto-sync errors are silent - manual sync can be triggered if needed
    }
  }

  /// Manually trigger sync check.
  Future<void> checkAndSync() async {
    if (_isConnected && _autoSyncEnabled) {
      await _performAutoSync();
    }
  }

  /// Dispose resources.
  void dispose() {
    _connectivitySubscription?.cancel();
    _syncDebounceTimer?.cancel();
    _connectivityController.close();
  }
}
