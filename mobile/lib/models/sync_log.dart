/// Model for sync log from server.
library;

/// Represents a sync log entry from the backend.
class SyncLog {
  final int id;
  final int userId;
  final String deviceId;
  final String? deviceName;
  final String operation;
  final String status;
  final int recordsSynced;
  final int recordsFailed;
  final int recordsConflict;
  final String startedAt;
  final String? completedAt;
  final String? errorMessage;
  final Map<String, dynamic>? conflictDetails;
  final Map<String, dynamic>? syncMetadata;
  final int retryCount;
  final String? nextRetryAt;

  SyncLog({
    required this.id,
    required this.userId,
    required this.deviceId,
    this.deviceName,
    required this.operation,
    required this.status,
    required this.recordsSynced,
    required this.recordsFailed,
    required this.recordsConflict,
    required this.startedAt,
    this.completedAt,
    this.errorMessage,
    this.conflictDetails,
    this.syncMetadata,
    required this.retryCount,
    this.nextRetryAt,
  });

  /// Create from JSON.
  factory SyncLog.fromJson(Map<String, dynamic> json) {
    return SyncLog(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      deviceId: json['device_id'] as String,
      deviceName: json['device_name'] as String?,
      operation: json['operation'] as String,
      status: json['status'] as String,
      recordsSynced: json['records_synced'] as int,
      recordsFailed: json['records_failed'] as int,
      recordsConflict: json['records_conflict'] as int,
      startedAt: json['started_at'] as String,
      completedAt: json['completed_at'] as String?,
      errorMessage: json['error_message'] as String?,
      conflictDetails: json['conflict_details'] as Map<String, dynamic>?,
      syncMetadata: json['sync_metadata'] as Map<String, dynamic>?,
      retryCount: json['retry_count'] as int,
      nextRetryAt: json['next_retry_at'] as String?,
    );
  }

  /// Convert to JSON.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'device_id': deviceId,
      if (deviceName != null) 'device_name': deviceName,
      'operation': operation,
      'status': status,
      'records_synced': recordsSynced,
      'records_failed': recordsFailed,
      'records_conflict': recordsConflict,
      'started_at': startedAt,
      if (completedAt != null) 'completed_at': completedAt,
      if (errorMessage != null) 'error_message': errorMessage,
      if (conflictDetails != null) 'conflict_details': conflictDetails,
      if (syncMetadata != null) 'sync_metadata': syncMetadata,
      'retry_count': retryCount,
      if (nextRetryAt != null) 'next_retry_at': nextRetryAt,
    };
  }

  /// Get total records processed.
  int get totalRecords => recordsSynced + recordsFailed + recordsConflict;

  /// Check if sync is complete.
  bool get isCompleted =>
      status == 'success' || status == 'failed' || status == 'conflict';
}
