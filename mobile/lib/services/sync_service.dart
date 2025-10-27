/// Synchronization service for offline-first functionality.
/// Implements T149 from tasks.md.
library;

import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';

import '../models/sync_log.dart';
import '../services/api_service.dart';
import '../services/database_service.dart';
import '../services/offline_queue_service.dart';
import '../config/env.example.dart';

/// Sync status enum.
enum SyncStatus {
  idle,
  syncing,
  success,
  error,
}

/// Sync result class.
class SyncResult {
  final SyncStatus status;
  final String? message;
  final int? syncLogId;
  final int totalRecords;
  final int successful;
  final int failed;
  final int conflicts;

  SyncResult({
    required this.status,
    this.message,
    this.syncLogId,
    this.totalRecords = 0,
    this.successful = 0,
    this.failed = 0,
    this.conflicts = 0,
  });
}

/// Synchronization service for handling offline operations.
///
/// Features:
/// - Automatic sync on connection restore
/// - Exponential backoff retry
/// - Conflict detection and resolution
/// - Bulk sync operations
/// - Sync status tracking
class SyncService {
  static final SyncService instance = SyncService._internal();

  final DatabaseService _dbService = DatabaseService.instance;
  final OfflineQueueService _queueService = OfflineQueueService.instance;
  final ApiService _apiService = ApiService.instance;

  // Sync state
  SyncStatus _status = SyncStatus.idle;
  String? _lastError;
  DateTime? _lastSyncAt;
  int _retryCount = 0;

  // Exponential backoff parameters
  static const int _baseRetryDelay = 5; // seconds
  static const int _maxRetryDelay = 300; // 5 minutes
  static const int _maxRetries = 10;
  static const int _batchSize = 50; // Process 50 operations at a time

  // Stream controller for sync status updates
  final _statusController = StreamController<SyncStatus>.broadcast();

  factory SyncService() => instance;

  SyncService._internal();

  /// Get current sync status.
  SyncStatus get status => _status;

  /// Get last error message.
  String? get lastError => _lastError;

  /// Get last successful sync timestamp.
  DateTime? get lastSyncAt => _lastSyncAt;

  /// Stream of sync status changes.
  Stream<SyncStatus> get statusStream => _statusController.stream;

  /// Dispose resources.
  void dispose() {
    _statusController.close();
  }

  /// Perform full sync of all pending operations.
  Future<SyncResult> sync() async {
    if (_status == SyncStatus.syncing) {
      return SyncResult(
        status: SyncStatus.error,
        message: 'Sync already in progress',
      );
    }

    _updateStatus(SyncStatus.syncing);
    _lastError = null;

    try {
      // Get pending operations from offline queue
      final pendingOps = await _queueService.getPendingOperations();

      if (pendingOps.isEmpty) {
        _updateStatus(SyncStatus.success);
        _lastSyncAt = DateTime.now();
        return SyncResult(
          status: SyncStatus.success,
          message: 'No operations to sync',
          totalRecords: 0,
          successful: 0,
        );
      }

      // Build sync request
      final deviceId = await _dbService.getDeviceId();
      final deviceName = await _dbService.getDeviceName();

      final syncRequest = {
        'records': pendingOps
            .map((op) => {
                  'client_id': op.id.toString(),
                  'model': op.entityType,
                  'operation': op.operation,
                  'data': jsonDecode(op.data),
                })
            .toList(),
      };

      // Send bulk sync request
      final response = await _apiService.dio.post(
        '/v1/sync',
        data: syncRequest,
        options: Options(
          headers: {
            'X-Device-ID': deviceId,
            if (deviceName != null) 'X-Device-Name': deviceName,
          },
        ),
      );

      // Process response
      final syncResponse = response.data as Map<String, dynamic>;
      final results = syncResponse['results'] as List<dynamic>;

      // Update offline queue based on results
      for (var i = 0; i < results.length; i++) {
        final result = results[i] as Map<String, dynamic>;
        final op = pendingOps[i];
        final resultStatus = result['status'] as String;

        if (resultStatus == 'success') {
          // Mark operation as completed
          await _queueService.markOperationCompleted(op.id!);

          // Update local database with server ID if create operation
          if (op.operation == 'create' && result['server_id'] != null) {
            await _updateLocalRecordId(
              op.entityType,
              op.entityId,
              result['server_id'].toString(),
            );
          }
        } else if (resultStatus == 'conflict') {
          // Mark as failed with conflict details
          await _queueService.markOperationFailed(
            op.id!,
            'Conflict: ${result['message']}',
          );
        } else {
          // Mark as failed
          await _queueService.markOperationFailed(
            op.id!,
            result['message'] as String,
          );
        }
      }

      // Reset retry count on success
      _retryCount = 0;
      _lastSyncAt = DateTime.now();
      _updateStatus(SyncStatus.success);

      return SyncResult(
        status: SyncStatus.success,
        message: 'Sync completed successfully',
        syncLogId: syncResponse['sync_log_id'] as int?,
        totalRecords: syncResponse['total_records'] as int,
        successful: syncResponse['successful'] as int,
        failed: syncResponse['failed'] as int,
        conflicts: syncResponse['conflicts'] as int,
      );
    } on DioException catch (e) {
      _lastError = e.message ?? 'Network error';
      _updateStatus(SyncStatus.error);

      // Schedule retry with exponential backoff
      if (_retryCount < _maxRetries) {
        _scheduleRetry();
      }

      return SyncResult(
        status: SyncStatus.error,
        message: _lastError,
      );
    } catch (e) {
      _lastError = e.toString();
      _updateStatus(SyncStatus.error);

      return SyncResult(
        status: SyncStatus.error,
        message: _lastError,
      );
    }
  }

  /// Get sync status from server.
  Future<Map<String, dynamic>?> getSyncStatus() async {
    try {
      final deviceId = await _dbService.getDeviceId();

      final response = await _apiService.dio.get(
        '/v1/sync/status',
        options: Options(
          headers: {
            'X-Device-ID': deviceId,
          },
        ),
      );

      return response.data as Map<String, dynamic>;
    } catch (e) {
      return null;
    }
  }

  /// Get unresolved conflicts from server.
  Future<List<Map<String, dynamic>>> getConflicts() async {
    try {
      final deviceId = await _dbService.getDeviceId();

      final response = await _apiService.dio.get(
        '/v1/sync/conflicts',
        options: Options(
          headers: {
            'X-Device-ID': deviceId,
          },
        ),
      );

      return (response.data as List<dynamic>).cast<Map<String, dynamic>>();
    } catch (e) {
      return [];
    }
  }

  /// Update status and notify listeners.
  void _updateStatus(SyncStatus newStatus) {
    _status = newStatus;
    _statusController.add(_status);
  }

  /// Schedule retry with exponential backoff.
  void _scheduleRetry() {
    _retryCount++;

    final delaySeconds = (_baseRetryDelay * (1 << (_retryCount - 1)))
        .clamp(_baseRetryDelay, _maxRetryDelay);

    Future.delayed(Duration(seconds: delaySeconds), () {
      if (_status == SyncStatus.error) {
        sync();
      }
    });
  }

  /// Update local record ID after server creation.
  Future<void> _updateLocalRecordId(
    String entityType,
    String clientId,
    String serverId,
  ) async {
    final db = await _dbService.database;

    // Map entity type to table name
    final tableName = _getTableName(entityType);
    if (tableName == null) return;

    // Update the ID
    await db.update(
      tableName,
      {'id': serverId},
      where: 'id = ?',
      whereArgs: [clientId],
    );
  }

  /// Get table name from entity type.
  String? _getTableName(String entityType) {
    switch (entityType) {
      case 'property':
        return 'properties';
      case 'tenant':
        return 'tenants';
      case 'payment':
        return 'payments';
      case 'bill':
        return 'bills';
      case 'expense':
        return 'expenses';
      default:
        return null;
    }
  }
}
