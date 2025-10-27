/// Model for offline sync queue operations.
library;

import 'dart:convert';

/// Represents a queued operation for offline sync.
class SyncOperation {
  final int? id;
  final OperationType operation;
  final String entityType; // 'property', 'tenant', 'payment', etc.
  final String entityId;
  final Map<String, dynamic> data; // parsed JSON payload
  final SyncStatus status;
  final int retryCount;
  final DateTime createdAt;
  final DateTime? lastAttemptAt;

  const SyncOperation({
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

  /// Create from database map. Accepts ISO8601 strings for dates.
  factory SyncOperation.fromMap(Map<String, dynamic> map) {
    DateTime parseDate(dynamic v) {
      if (v == null) return DateTime.fromMillisecondsSinceEpoch(0);
      if (v is DateTime) return v;
      if (v is int) return DateTime.fromMillisecondsSinceEpoch(v);
      return DateTime.parse(v as String);
    }

    return SyncOperation(
      id: map['id'] as int?,
      operation: OperationTypeExtension.fromString(map['operation'] as String),
      entityType: map['entity_type'] as String,
      entityId: map['entity_id'] as String,
      data: map['data'] is String
          ? json.decode(map['data'] as String) as Map<String, dynamic>
          : Map<String, dynamic>.from(map['data'] as Map),
      status: SyncStatusExtension.fromString(map['status'] as String),
      retryCount: map['retry_count'] as int? ?? 0,
      createdAt: parseDate(map['created_at']),
      lastAttemptAt: map['last_attempt_at'] != null
          ? parseDate(map['last_attempt_at'])
          : null,
    );
  }

  /// Convert to database map. Dates become ISO8601 strings.
  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'operation': operation.asString,
      'entity_type': entityType,
      'entity_id': entityId,
      'data': json.encode(data),
      'status': status.asString,
      'retry_count': retryCount,
      'created_at': createdAt.toUtc().toIso8601String(),
      if (lastAttemptAt != null)
        'last_attempt_at': lastAttemptAt!.toUtc().toIso8601String(),
    };
  }

  /// JSON serialization for network or local cache (not DB map which uses strings)
  Map<String, dynamic> toJson() => {
        if (id != null) 'id': id,
        'operation': operation.asString,
        'entity_type': entityType,
        'entity_id': entityId,
        'data': data,
        'status': status.asString,
        'retry_count': retryCount,
        'created_at': createdAt.toUtc().toIso8601String(),
        'last_attempt_at': lastAttemptAt?.toUtc().toIso8601String(),
      };

  factory SyncOperation.fromJson(Map<String, dynamic> jsonMap) {
    DateTime parseDate(dynamic v) {
      if (v == null) return DateTime.fromMillisecondsSinceEpoch(0);
      if (v is DateTime) return v;
      if (v is int) return DateTime.fromMillisecondsSinceEpoch(v);
      return DateTime.parse(v as String);
    }

    return SyncOperation(
      id: jsonMap['id'] as int?,
      operation:
          OperationTypeExtension.fromString(jsonMap['operation'] as String),
      entityType: jsonMap['entity_type'] as String,
      entityId: jsonMap['entity_id'] as String,
      data: jsonMap['data'] as Map<String, dynamic>? ?? {},
      status: SyncStatusExtension.fromString(jsonMap['status'] as String),
      retryCount: jsonMap['retry_count'] as int? ?? 0,
      createdAt: parseDate(jsonMap['created_at']),
      lastAttemptAt: jsonMap['last_attempt_at'] != null
          ? parseDate(jsonMap['last_attempt_at'])
          : null,
    );
  }

  SyncOperation copyWith({
    int? id,
    OperationType? operation,
    String? entityType,
    String? entityId,
    Map<String, dynamic>? data,
    SyncStatus? status,
    int? retryCount,
    DateTime? createdAt,
    DateTime? lastAttemptAt,
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

  /// Whether this operation should be retried.
  bool get needsRetry => status != SyncStatus.completed && retryCount < 5;

  /// Return a new instance with incremented retry count and updated lastAttemptAt.
  SyncOperation withRetryAttempted(DateTime attemptTime) {
    return copyWith(retryCount: retryCount + 1, lastAttemptAt: attemptTime);
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other is SyncOperation &&
            other.id == id &&
            other.operation == operation &&
            other.entityType == entityType &&
            other.entityId == entityId &&
            mapEquals(other.data, data) &&
            other.status == status &&
            other.retryCount == retryCount &&
            other.createdAt == createdAt &&
            other.lastAttemptAt == lastAttemptAt);
  }

  @override
  int get hashCode => Object.hash(
        id,
        operation,
        entityType,
        entityId,
        data.hashCode,
        status,
        retryCount,
        createdAt,
        lastAttemptAt,
      );
}

/// Operation types for sync queue.
enum OperationType { create, update, delete }

extension OperationTypeExtension on OperationType {
  String get asString {
    switch (this) {
      case OperationType.create:
        return 'create';
      case OperationType.update:
        return 'update';
      case OperationType.delete:
        return 'delete';
    }
  }

  static OperationType fromString(String s) =>
      OperationTypeExtension._fromStringInternal(s);

  static OperationType _fromStringInternal(String s) {
    switch (s) {
      case 'create':
        return OperationType.create;
      case 'update':
        return OperationType.update;
      case 'delete':
        return OperationType.delete;
      default:
        throw ArgumentError('Unknown OperationType: $s');
    }
  }
}

/// Status of a sync operation.
enum SyncStatus { pending, completed, failed }

extension SyncStatusExtension on SyncStatus {
  String get asString {
    switch (this) {
      case SyncStatus.pending:
        return 'pending';
      case SyncStatus.completed:
        return 'completed';
      case SyncStatus.failed:
        return 'failed';
    }
  }

  static SyncStatus fromString(String s) {
    switch (s) {
      case 'pending':
        return SyncStatus.pending;
      case 'completed':
        return SyncStatus.completed;
      case 'failed':
        return SyncStatus.failed;
      default:
        throw ArgumentError('Unknown SyncStatus: $s');
    }
  }
}

// Helper to compare maps for equality without importing foundation in every file
bool mapEquals(Map? a, Map? b) {
  if (identical(a, b)) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (final key in a.keys) {
    if (!b.containsKey(key)) return false;
    final va = a[key];
    final vb = b[key];
    if (va is Map && vb is Map) {
      if (!mapEquals(va, vb)) return false;
    } else if (va != vb) return false;
  }
  return true;
}
