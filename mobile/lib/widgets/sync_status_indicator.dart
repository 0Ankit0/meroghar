/// Sync status indicator widget.
/// Implements T151 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../services/offline_queue_service.dart';
import '../services/sync_service.dart';

/// Widget that displays the current sync status.
///
/// Shows:
/// - Syncing animation when sync in progress
/// - Success icon when sync complete
/// - Error icon when sync failed
/// - Pending count badge
class SyncStatusIndicator extends StatefulWidget {
  const SyncStatusIndicator({
    super.key,
    this.onTap,
  });
  final VoidCallback? onTap;

  @override
  State<SyncStatusIndicator> createState() => _SyncStatusIndicatorState();
}

class _SyncStatusIndicatorState extends State<SyncStatusIndicator> {
  final SyncService _syncService = SyncService.instance;
  final OfflineQueueService _queueService = OfflineQueueService.instance;

  Map<String, int>? _queueStats;

  @override
  void initState() {
    super.initState();
    _loadQueueStats();
  }

  Future<void> _loadQueueStats() async {
    final stats = await _queueService.getQueueStats();
    if (mounted) {
      setState(() {
        _queueStats = stats;
      });
    }
  }

  @override
  Widget build(BuildContext context) => StreamBuilder<SyncStatus>(
        stream: _syncService.statusStream,
        initialData: _syncService.status,
        builder: (context, snapshot) {
          final status = snapshot.data ?? SyncStatus.idle;

          return InkWell(
            onTap: widget.onTap ?? _handleTap,
            borderRadius: BorderRadius.circular(20),
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Stack(
                children: [
                  _buildStatusIcon(status),
                  if (_queueStats != null && _queueStats!['pending']! > 0)
                    Positioned(
                      right: 0,
                      top: 0,
                      child: Container(
                        padding: const EdgeInsets.all(4),
                        decoration: const BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                        constraints: const BoxConstraints(
                          minWidth: 16,
                          minHeight: 16,
                        ),
                        child: Text(
                          '${_queueStats!['pending']}',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      );

  Widget _buildStatusIcon(SyncStatus status) {
    switch (status) {
      case SyncStatus.idle:
        return const Icon(
          Icons.cloud_outlined,
          color: Colors.grey,
        );

      case SyncStatus.syncing:
        return const SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
          ),
        );

      case SyncStatus.success:
        return const Icon(
          Icons.cloud_done,
          color: Colors.green,
        );

      case SyncStatus.error:
        return const Icon(
          Icons.cloud_off,
          color: Colors.red,
        );
    }
  }

  void _handleTap() {
    // Show sync status dialog or navigate to sync screen
    _showSyncDialog();
  }

  void _showSyncDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sync Status'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildStatusRow('Status', _getStatusText(_syncService.status)),
            if (_queueStats != null) ...[
              const SizedBox(height: 8),
              _buildStatusRow('Pending', '${_queueStats!['pending']}'),
              _buildStatusRow('Failed', '${_queueStats!['failed']}'),
              _buildStatusRow('Completed', '${_queueStats!['completed']}'),
            ],
            if (_syncService.lastError != null) ...[
              const SizedBox(height: 8),
              const Text(
                'Last Error:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(
                _syncService.lastError!,
                style: const TextStyle(color: Colors.red),
              ),
            ],
            if (_syncService.lastSyncAt != null) ...[
              const SizedBox(height: 8),
              Text(
                'Last sync: ${_formatDateTime(_syncService.lastSyncAt!)}',
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ],
        ),
        actions: [
          if (_queueStats != null && _queueStats!['pending']! > 0)
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _triggerSync();
              },
              child: const Text('Sync Now'),
            ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(value),
          ],
        ),
      );

  String _getStatusText(SyncStatus status) {
    switch (status) {
      case SyncStatus.idle:
        return 'Idle';
      case SyncStatus.syncing:
        return 'Syncing...';
      case SyncStatus.success:
        return 'Success';
      case SyncStatus.error:
        return 'Error';
    }
  }

  String _formatDateTime(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);

    if (diff.inSeconds < 60) {
      return 'Just now';
    } else if (diff.inMinutes < 60) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}h ago';
    } else {
      return '${diff.inDays}d ago';
    }
  }

  Future<void> _triggerSync() async {
    await _syncService.sync();
    await _loadQueueStats();
  }
}
