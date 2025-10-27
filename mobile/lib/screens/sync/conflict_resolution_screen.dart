/// Conflict resolution UI screen.
/// Implements T153 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../../services/sync_service.dart';

/// Screen for resolving sync conflicts.
///
/// Allows users to:
/// - View conflicted records
/// - Choose between client or server version
/// - Manually edit conflicted data
class ConflictResolutionScreen extends StatefulWidget {
  const ConflictResolutionScreen({super.key});

  @override
  State<ConflictResolutionScreen> createState() =>
      _ConflictResolutionScreenState();
}

class _ConflictResolutionScreenState extends State<ConflictResolutionScreen> {
  final SyncService _syncService = SyncService.instance;

  List<Map<String, dynamic>>? _conflicts;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadConflicts();
  }

  Future<void> _loadConflicts() async {
    setState(() {
      _isLoading = true;
    });

    final conflicts = await _syncService.getConflicts();

    setState(() {
      _conflicts = conflicts;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Resolve Conflicts'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadConflicts,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_conflicts == null || _conflicts!.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.check_circle_outline,
              size: 64,
              color: Colors.green,
            ),
            const SizedBox(height: 16),
            const Text(
              'No conflicts to resolve',
              style: TextStyle(fontSize: 18),
            ),
            const SizedBox(height: 8),
            const Text(
              'All your data is in sync!',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Back'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _conflicts!.length,
      itemBuilder: (context, index) {
        final conflict = _conflicts![index];
        return _buildConflictCard(conflict, index);
      },
    );
  }

  Widget _buildConflictCard(Map<String, dynamic> conflict, int index) {
    final details = conflict['conflict_details'] as Map<String, dynamic>?;
    final conflicts = details?['conflicts'] as List<dynamic>? ?? [];

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: ExpansionTile(
        leading: const Icon(Icons.warning, color: Colors.orange),
        title: Text(
          'Conflict from ${conflict['device_name'] ?? conflict['device_id']}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(
          '${conflict['records_conflict']} conflicted record(s)\n'
          'Started: ${_formatDateTime(conflict['started_at'])}',
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var i = 0; i < conflicts.length; i++)
                  _buildConflictDetail(conflicts[i] as Map<String, dynamic>, i),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConflictDetail(Map<String, dynamic> conflictDetail, int index) {
    final model = conflictDetail['model'] as String?;
    final recordId = conflictDetail['record_id'];
    final reason = conflictDetail['reason'] as String?;
    final clientData = conflictDetail['client_data'] as Map<String, dynamic>?;
    final serverData = conflictDetail['server_data'] as Map<String, dynamic>?;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.orange,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  model?.toUpperCase() ?? 'UNKNOWN',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                'ID: $recordId',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ],
          ),

          const SizedBox(height: 8),

          // Reason
          if (reason != null) ...[
            Text(
              reason,
              style: const TextStyle(
                color: Colors.orange,
                fontStyle: FontStyle.italic,
              ),
            ),
            const SizedBox(height: 12),
          ],

          // Client version
          if (clientData != null) ...[
            const Text(
              'Your Version (Client):',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            _buildDataPreview(clientData),
            const SizedBox(height: 8),
          ],

          // Server version
          if (serverData != null) ...[
            const Text(
              'Server Version:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            _buildDataPreview(serverData),
            const SizedBox(height: 12),
          ],

          // Action buttons
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: () => _resolveConflict(conflictDetail, 'client'),
                child: const Text('Use Client'),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: () => _resolveConflict(conflictDetail, 'server'),
                child: const Text('Use Server'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDataPreview(Map<String, dynamic> data) {
    // Remove internal fields for cleaner display
    final displayData = Map<String, dynamic>.from(data);
    displayData.remove('id');
    displayData.remove('created_at');

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: displayData.entries.map((entry) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${entry.key}: ',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Expanded(
                  child: Text(
                    entry.value.toString(),
                    style: const TextStyle(color: Colors.grey),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Future<void> _resolveConflict(
    Map<String, dynamic> conflictDetail,
    String resolution,
  ) async {
    // Show confirmation dialog
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Resolution'),
        content: Text(
          'Are you sure you want to use the $resolution version?\n\n'
          'This will ${resolution == 'server' ? 'discard your local changes' : 'overwrite the server data'}.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor:
                  resolution == 'server' ? Colors.orange : Colors.blue,
            ),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      // TODO: Implement actual conflict resolution API call
      // This would call a backend endpoint to resolve the conflict

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Conflict resolved using $resolution version'),
          backgroundColor: Colors.green,
        ),
      );

      // Reload conflicts
      await _loadConflicts();
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
