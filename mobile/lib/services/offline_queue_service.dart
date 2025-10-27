/// Offline operation queue service.
/// Implements T150 from tasks.md.
library;

import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import '../models/sync_operation.dart';
import '../services/database_service.dart';

/// Service for managing offline operation queue.
///
/// Features:
/// - Queue CRUD operations when offline
/// - Track operation status (pending, completed, failed)
/// - Retry failed operations
/// - Clear completed operations
class OfflineQueueService {
  static final OfflineQueueService instance = OfflineQueueService._internal();

  final DatabaseService _dbService = DatabaseService.instance;

  factory OfflineQueueService() => instance;

  OfflineQueueService._internal();

  /// Add operation to the queue.
  Future<int> queueOperation({
    required String operation,
    required String entityType,
    required String entityId,
    required Map<String, dynamic> data,
  }) async {
    final db = await _dbService.database;

    // Add updated_at timestamp for conflict resolution
    data['updated_at'] = DateTime.now().toIso8601String();

    final id = await db.insert(
      'sync_queue',
      {
        'operation': operation,
        'entity_type': entityType,
        'entity_id': entityId,
        'data': jsonEncode(data),
        'status': 'pending',
        'retry_count': 0,
        'created_at': DateTime.now().toIso8601String(),
      },
    );

    return id;
  }

  /// Get all pending operations.
  Future<List<SyncOperation>> getPendingOperations() async {
    final db = await _dbService.database;

    final results = await db.query(
      'sync_queue',
      where: 'status = ?',
      whereArgs: ['pending'],
      orderBy: 'created_at ASC',
    );

    return results.map((row) => SyncOperation.fromMap(row)).toList();
  }

  /// Get operation by ID.
  Future<SyncOperation?> getOperation(int id) async {
    final db = await _dbService.database;

    final results = await db.query(
      'sync_queue',
      where: 'id = ?',
      whereArgs: [id],
    );

    if (results.isEmpty) return null;

    return SyncOperation.fromMap(results.first);
  }

  /// Mark operation as completed.
  Future<void> markOperationCompleted(int id) async {
    final db = await _dbService.database;

    await db.update(
      'sync_queue',
      {'status': 'completed'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Mark operation as failed.
  Future<void> markOperationFailed(int id, String errorMessage) async {
    final db = await _dbService.database;

    await db.update(
      'sync_queue',
      {
        'status': 'failed',
        'last_attempt_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Retry failed operation.
  Future<void> retryOperation(int id) async {
    final db = await _dbService.database;

    final operation = await getOperation(id);
    if (operation == null) return;

    await db.update(
      'sync_queue',
      {
        'status': 'pending',
        'retry_count': operation.retryCount + 1,
        'last_attempt_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Get failed operations.
  Future<List<SyncOperation>> getFailedOperations() async {
    final db = await _dbService.database;

    final results = await db.query(
      'sync_queue',
      where: 'status = ?',
      whereArgs: ['failed'],
      orderBy: 'created_at ASC',
    );

    return results.map((row) => SyncOperation.fromMap(row)).toList();
  }

  /// Get completed operations.
  Future<List<SyncOperation>> getCompletedOperations() async {
    final db = await _dbService.database;

    final results = await db.query(
      'sync_queue',
      where: 'status = ?',
      whereArgs: ['completed'],
      orderBy: 'created_at DESC',
      limit: 100,
    );

    return results.map((row) => SyncOperation.fromMap(row)).toList();
  }

  /// Clear completed operations older than specified days.
  Future<int> clearCompletedOperations({int olderThanDays = 7}) async {
    final db = await _dbService.database;

    final cutoffDate = DateTime.now()
        .subtract(Duration(days: olderThanDays))
        .toIso8601String();

    return await db.delete(
      'sync_queue',
      where: 'status = ? AND created_at < ?',
      whereArgs: ['completed', cutoffDate],
    );
  }

  /// Get queue statistics.
  Future<Map<String, int>> getQueueStats() async {
    final db = await _dbService.database;

    final pending = Sqflite.firstIntValue(
          await db.rawQuery(
            'SELECT COUNT(*) FROM sync_queue WHERE status = ?',
            ['pending'],
          ),
        ) ??
        0;

    final failed = Sqflite.firstIntValue(
          await db.rawQuery(
            'SELECT COUNT(*) FROM sync_queue WHERE status = ?',
            ['failed'],
          ),
        ) ??
        0;

    final completed = Sqflite.firstIntValue(
          await db.rawQuery(
            'SELECT COUNT(*) FROM sync_queue WHERE status = ?',
            ['completed'],
          ),
        ) ??
        0;

    return {
      'pending': pending,
      'failed': failed,
      'completed': completed,
      'total': pending + failed + completed,
    };
  }

  /// Clear all operations (use with caution).
  Future<void> clearAllOperations() async {
    final db = await _dbService.database;
    await db.delete('sync_queue');
  }
}
