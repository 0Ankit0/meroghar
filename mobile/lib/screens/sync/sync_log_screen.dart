/// Sync log viewer screen.
/// Implements T156 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../../models/sync_operation.dart';
import '../../services/offline_queue_service.dart';

/// Screen for viewing sync operation logs.
///
/// Features:
/// - View pending, failed, and completed operations
/// - Filter by status
/// - Retry failed operations
/// - View operation details
class SyncLogScreen extends StatefulWidget {
  const SyncLogScreen({super.key});

  @override
  State<SyncLogScreen> createState() => _SyncLogScreenState();
}

class _SyncLogScreenState extends State<SyncLogScreen>
    with SingleTickerProviderStateMixin {
  final OfflineQueueService _queueService = OfflineQueueService.instance;

  late TabController _tabController;

  List<SyncOperation>? _pendingOps;
  List<SyncOperation>? _failedOps;
  List<SyncOperation>? _completedOps;

  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadLogs();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadLogs() async {
    setState(() {
      _isLoading = true;
    });

    _pendingOps = await _queueService.getPendingOperations();
    _failedOps = await _queueService.getFailedOperations();
    _completedOps = await _queueService.getCompletedOperations();

    setState(() {
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sync Logs'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadLogs,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(
              text: 'Pending',
              icon: Badge(
                label: Text('${_pendingOps?.length ?? 0}'),
                child: const Icon(Icons.schedule),
              ),
            ),
            Tab(
              text: 'Failed',
              icon: Badge(
                label: Text('${_failedOps?.length ?? 0}'),
                child: const Icon(Icons.error),
              ),
            ),
            Tab(
              text: 'Completed',
              icon: Badge(
                label: Text('${_completedOps?.length ?? 0}'),
                child: const Icon(Icons.check_circle),
              ),
            ),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildOperationsList(_pendingOps, 'pending'),
                _buildOperationsList(_failedOps, 'failed'),
                _buildOperationsList(_completedOps, 'completed'),
              ],
            ),
    );
  }

  Widget _buildOperationsList(List<SyncOperation>? operations, String status) {
    if (operations == null || operations.isEmpty) {
      return _buildEmptyState(status);
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: operations.length,
      itemBuilder: (context, index) {
        final operation = operations[index];
        return _buildOperationCard(operation, status);
      },
    );
  }

  Widget _buildEmptyState(String status) {
    String message;
    IconData icon;
    Color color;

    switch (status) {
      case 'pending':
        message = 'No pending operations';
        icon = Icons.check_circle;
        color = Colors.green;
        break;
      case 'failed':
        message = 'No failed operations';
        icon = Icons.check_circle;
        color = Colors.green;
        break;
      case 'completed':
        message = 'No completed operations yet';
        icon = Icons.history;
        color = Colors.grey;
        break;
      default:
        message = 'No operations';
        icon = Icons.info;
        color = Colors.grey;
    }

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: color),
          const SizedBox(height: 16),
          Text(
            message,
            style: const TextStyle(fontSize: 18),
          ),
        ],
      ),
    );
  }

  Widget _buildOperationCard(SyncOperation operation, String status) {
    Color statusColor;
    IconData statusIcon;

    switch (status) {
      case 'pending':
        statusColor = Colors.orange;
        statusIcon = Icons.schedule;
        break;
      case 'failed':
        statusColor = Colors.red;
        statusIcon = Icons.error;
        break;
      case 'completed':
        statusColor = Colors.green;
        statusIcon = Icons.check_circle;
        break;
      default:
        statusColor = Colors.grey;
        statusIcon = Icons.info;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(statusIcon, color: statusColor),
        title: Text(
          '${operation.operation.toUpperCase()} ${operation.entityType}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text('Entity ID: ${operation.entityId}'),
            Text('Created: ${_formatDateTime(operation.createdAt)}'),
            if (operation.retryCount > 0)
              Text(
                'Retry count: ${operation.retryCount}',
                style: const TextStyle(color: Colors.orange),
              ),
            if (operation.lastAttemptAt != null)
              Text(
                  'Last attempt: ${_formatDateTime(operation.lastAttemptAt!)}'),
          ],
        ),
        isThreeLine: true,
        trailing: status == 'failed'
            ? IconButton(
                icon: const Icon(Icons.replay),
                tooltip: 'Retry',
                onPressed: () => _retryOperation(operation),
              )
            : null,
        onTap: () => _showOperationDetails(operation),
      ),
    );
  }

  Future<void> _showOperationDetails(SyncOperation operation) async {
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
            '${operation.operation.toUpperCase()} ${operation.entityType}'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildDetailRow('ID', operation.id.toString()),
              _buildDetailRow('Entity Type', operation.entityType),
              _buildDetailRow('Entity ID', operation.entityId),
              _buildDetailRow('Operation', operation.operation),
              _buildDetailRow('Status', operation.status),
              _buildDetailRow('Retry Count', operation.retryCount.toString()),
              _buildDetailRow('Created', _formatDateTime(operation.createdAt)),
              if (operation.lastAttemptAt != null)
                _buildDetailRow(
                    'Last Attempt', _formatDateTime(operation.lastAttemptAt!)),
              const Divider(height: 24),
              const Text(
                'Data:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  operation.data,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                ),
              ),
            ],
          ),
        ),
        actions: [
          if (operation.status == 'failed')
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _retryOperation(operation);
              },
              child: const Text('Retry'),
            ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  Future<void> _retryOperation(SyncOperation operation) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Retry Operation?'),
        content: const Text(
          'This will mark the operation as pending and attempt to sync it again.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Retry'),
          ),
        ],
      ),
    );

    if (confirmed == true && operation.id != null) {
      await _queueService.retryOperation(operation.id!);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Operation marked for retry'),
            backgroundColor: Colors.green,
          ),
        );
      }

      await _loadLogs();
    }
  }

  String _formatDateTime(String dateTimeStr) {
    try {
      final dt = DateTime.parse(dateTimeStr);
      return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
          '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateTimeStr;
    }
  }
}
