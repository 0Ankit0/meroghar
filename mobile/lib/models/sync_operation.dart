/// Model for offline sync queue operations.
library;

/// Represents a queued operation for offline sync.
class SyncOperation {
  final int? id;
  final String operation; // 'create', 'update', 'delete'
  final String entityType; // 'property', 'tenant', 'payment', etc.
  final String entityId;
  final String data; // JSON string
  final String status; // 'pending', 'completed', 'failed'
  final int retryCount;
  final String createdAt;
  final String? lastAttemptAt;

  SyncOperation({
    this.id,
    required this.operation,
    required this.entityType,
    required this.entityId,
    required this.data,
    required this.status,
    required this.retryCount,
    required this.createdAt,
    this.lastAttemptAt,
  });

  /// Create from database map.
  factory SyncOperation.fromMap(Map<String, dynamic> map) {
    return SyncOperation(
      id: map['id'] as int?,
      operation: map['operation'] as String,
      entityType: map['entity_type'] as String,
      entityId: map['entity_id'] as String,
      data: map['data'] as String,
      status: map['status'] as String,
      retryCount: map['retry_count'] as int,
      createdAt: map['created_at'] as String,
      lastAttemptAt: map['last_attempt_at'] as String?,
    );
  }

  /// Convert to database map.
  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'operation': operation,
      'entity_type': entityType,
      'entity_id': entityId,
      'data': data,
      'status': status,
      'retry_count': retryCount,
      'created_at': createdAt,
      if (lastAttemptAt != null) 'last_attempt_at': lastAttemptAt,
    };
  }

  /// Copy with method.
  SyncOperation copyWith({
    int? id,
    String? operation,
    String? entityType,
    String? entityId,
    String? data,
    String? status,
    int? retryCount,
    String? createdAt,
    String? lastAttemptAt,
  }) {
    return SyncOperation(
      id: id ?? this.id,
      operation: operation ?? this.operation,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      data: data ?? this.data,
      status: status ?? this.status,
      retryCount: retryCount ?? this.retryCount,
      createdAt: createdAt ?? this.createdAt,
      lastAttemptAt: lastAttemptAt ?? this.lastAttemptAt,
    );
  }
}
