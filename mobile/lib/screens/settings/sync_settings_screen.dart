/// Sync settings screen.
/// Implements T155 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../../services/connectivity_service.dart';
import '../../services/sync_service.dart';
import '../../services/offline_queue_service.dart';
import '../../services/database_service.dart';

/// Screen for managing sync preferences.
///
/// Features:
/// - Toggle auto-sync
/// - View sync statistics
/// - Manual sync trigger
/// - Clear completed operations
/// - Set device name
class SyncSettingsScreen extends StatefulWidget {
  const SyncSettingsScreen({super.key});

  @override
  State<SyncSettingsScreen> createState() => _SyncSettingsScreenState();
}

class _SyncSettingsScreenState extends State<SyncSettingsScreen> {
  final ConnectivityService _connectivityService = ConnectivityService.instance;
  final SyncService _syncService = SyncService.instance;
  final OfflineQueueService _queueService = OfflineQueueService.instance;
  final DatabaseService _dbService = DatabaseService.instance;

  bool _autoSyncEnabled = true;
  String? _deviceId;
  String? _deviceName;
  Map<String, int>? _queueStats;
  Map<String, dynamic>? _syncStatus;
  bool _isLoading = true;
  bool _isSyncing = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() {
      _isLoading = true;
    });

    _autoSyncEnabled = _connectivityService.autoSyncEnabled;
    _deviceId = await _dbService.getDeviceId();
    _deviceName = await _dbService.getDeviceName();
    _queueStats = await _queueService.getQueueStats();
    _syncStatus = await _syncService.getSyncStatus();

    setState(() {
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Sync Settings'),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildAutoSyncSection(),
                  const SizedBox(height: 24),
                  _buildDeviceSection(),
                  const SizedBox(height: 24),
                  _buildQueueSection(),
                  const SizedBox(height: 24),
                  _buildServerStatusSection(),
                  const SizedBox(height: 24),
                  _buildActionsSection(),
                ],
              ),
      );

  Widget _buildAutoSyncSection() => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Auto Sync',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              SwitchListTile(
                title: const Text('Auto-sync when online'),
                subtitle: const Text(
                  'Automatically sync changes when internet connection is restored',
                ),
                value: _autoSyncEnabled,
                onChanged: (value) {
                  setState(() {
                    _autoSyncEnabled = value;
                    _connectivityService.autoSyncEnabled = value;
                  });

                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        value ? 'Auto-sync enabled' : 'Auto-sync disabled',
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      );

  Widget _buildDeviceSection() => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Device Information',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              _buildInfoRow('Device ID', _deviceId ?? 'Not set'),
              const SizedBox(height: 8),
              _buildInfoRow('Device Name', _deviceName ?? 'Not set'),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _editDeviceName,
                icon: const Icon(Icons.edit),
                label: const Text('Edit Device Name'),
              ),
            ],
          ),
        ),
      );

  Widget _buildQueueSection() {
    if (_queueStats == null) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Offline Queue',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildStatRow(
              'Pending',
              _queueStats!['pending']!,
              Colors.orange,
            ),
            _buildStatRow(
              'Failed',
              _queueStats!['failed']!,
              Colors.red,
            ),
            _buildStatRow(
              'Completed',
              _queueStats!['completed']!,
              Colors.green,
            ),
            const Divider(height: 24),
            _buildStatRow(
              'Total',
              _queueStats!['total']!,
              Colors.blue,
              bold: true,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServerStatusSection() {
    if (_syncStatus == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('Unable to fetch server status'),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Server Sync Status',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildStatRow(
              'Total Syncs',
              _syncStatus!['total_syncs'] as int,
              Colors.blue,
            ),
            _buildStatRow(
              'Successful',
              _syncStatus!['success'] as int,
              Colors.green,
            ),
            _buildStatRow(
              'Failed',
              _syncStatus!['failed'] as int,
              Colors.red,
            ),
            _buildStatRow(
              'Conflicts',
              _syncStatus!['conflict'] as int,
              Colors.orange,
            ),
            if (_syncStatus!['latest_sync_at'] != null) ...[
              const SizedBox(height: 8),
              Text(
                'Last sync: ${_formatDateTime(_syncStatus!['latest_sync_at'] as String)}',
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionsSection() => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Actions',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _isSyncing ? null : _manualSync,
                icon: _isSyncing
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.sync),
                label: Text(_isSyncing ? 'Syncing...' : 'Sync Now'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _clearCompletedOperations,
                icon: const Icon(Icons.clear_all),
                label: const Text('Clear Completed Operations'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _refreshStatus,
                icon: const Icon(Icons.refresh),
                label: const Text('Refresh Status'),
              ),
            ],
          ),
        ),
      );

  Widget _buildInfoRow(String label, String value) => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(color: Colors.grey),
              textAlign: TextAlign.end,
            ),
          ),
        ],
      );

  Widget _buildStatRow(String label, int value, Color color,
          {bool bold = false}) =>
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontWeight: bold ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: color),
              ),
              child: Text(
                value.toString(),
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      );

  Future<void> _editDeviceName() async {
    final controller = TextEditingController(text: _deviceName ?? '');

    final newName = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Device Name'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Device Name',
            hintText: 'e.g., My Phone, Work Tablet',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Save'),
          ),
        ],
      ),
    );

    if (newName != null && newName.isNotEmpty) {
      await _dbService.setDeviceName(newName);
      await _loadSettings();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Device name updated'),
            backgroundColor: Colors.green,
          ),
        );
      }
    }
  }

  Future<void> _manualSync() async {
    setState(() {
      _isSyncing = true;
    });

    final result = await _syncService.sync();

    setState(() {
      _isSyncing = false;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.message ?? 'Sync completed'),
          backgroundColor:
              result.status == SyncStatus.success ? Colors.green : Colors.red,
        ),
      );
    }

    await _loadSettings();
  }

  Future<void> _clearCompletedOperations() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear Completed Operations?'),
        content: const Text(
          'This will permanently remove completed sync operations older than 7 days. '
          'This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Clear'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final count = await _queueService.clearCompletedOperations();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Cleared $count completed operation(s)'),
            backgroundColor: Colors.green,
          ),
        );
      }

      await _loadSettings();
    }
  }

  Future<void> _refreshStatus() async {
    await _loadSettings();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Status refreshed'),
        ),
      );
    }
  }

  String _formatDateTime(String dateTimeStr) {
    try {
      final dt = DateTime.parse(dateTimeStr);
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
    } catch (e) {
      return dateTimeStr;
    }
  }
}
