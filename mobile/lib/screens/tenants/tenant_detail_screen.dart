/// Tenant detail screen with rent history view.
///
/// Implements T201 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../../models/tenant.dart';
import '../../services/api_service.dart';
import 'rent_policy_screen.dart';
import 'rent_override_screen.dart';

class TenantDetailScreen extends StatefulWidget {
  final Tenant tenant;

  const TenantDetailScreen({
    super.key,
    required this.tenant,
  });

  @override
  State<TenantDetailScreen> createState() => _TenantDetailScreenState();
}

class _TenantDetailScreenState extends State<TenantDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Map<String, dynamic>> _rentHistory = [];
  bool _isLoadingHistory = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadRentHistory();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadRentHistory() async {
    setState(() {
      _isLoadingHistory = true;
      _error = null;
    });

    try {
      final apiService = ApiService.instance;
      final response = await apiService.get(
        '/api/v1/tenants/${widget.tenant.id}/rent-history',
      );

      if (!mounted) return;

      if (response.isSuccess) {
        setState(() {
          _rentHistory = List<Map<String, dynamic>>.from(
            (response.data as Map<String, dynamic>)['data'] as List? ?? [],
          );
          _isLoadingHistory = false;
        });
      } else {
        setState(() {
          _error = response.message ?? 'Failed to load rent history';
          _isLoadingHistory = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Error loading rent history: $e';
        _isLoadingHistory = false;
      });
    }
  }

  Future<void> _navigateToRentPolicy() async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => RentPolicyScreen(tenant: widget.tenant),
      ),
    );

    if (result == true) {
      _loadRentHistory();
    }
  }

  Future<void> _navigateToRentOverride() async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => RentOverrideScreen(tenant: widget.tenant),
      ),
    );

    if (result == true) {
      _loadRentHistory();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tenant Details'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Overview', icon: Icon(Icons.person)),
            Tab(text: 'Rent History', icon: Icon(Icons.history)),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              switch (value) {
                case 'policy':
                  _navigateToRentPolicy();
                  break;
                case 'override':
                  _navigateToRentOverride();
                  break;
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'policy',
                child: Row(
                  children: [
                    Icon(Icons.policy),
                    SizedBox(width: 8),
                    Text('Set Rent Policy'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'override',
                child: Row(
                  children: [
                    Icon(Icons.edit),
                    SizedBox(width: 8),
                    Text('Override Rent'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOverviewTab(),
          _buildRentHistoryTab(),
        ],
      ),
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: widget.tenant.isActive ? Colors.green : Colors.grey,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              widget.tenant.isActive ? 'ACTIVE' : 'MOVED OUT',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Tenant Information
          Text(
            'Tenant Information',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  _buildInfoRow('Tenant ID', widget.tenant.id),
                  const Divider(),
                  _buildInfoRow('User ID', widget.tenant.userId),
                  const Divider(),
                  _buildInfoRow('Property ID', widget.tenant.propertyId),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Rental Details
          Text(
            'Rental Details',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  _buildHighlightedRow(
                    'Monthly Rent',
                    '\$${widget.tenant.monthlyRent.toStringAsFixed(2)}',
                    Colors.blue,
                  ),
                  const Divider(),
                  _buildInfoRow(
                    'Security Deposit',
                    '\$${widget.tenant.securityDeposit.toStringAsFixed(2)}',
                  ),
                  const Divider(),
                  _buildInfoRow(
                    'Electricity Rate',
                    '\$${widget.tenant.electricityRate.toStringAsFixed(2)}/unit',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Occupancy Details
          Text(
            'Occupancy Details',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  _buildInfoRow(
                    'Move-in Date',
                    _formatDate(widget.tenant.moveInDate),
                  ),
                  if (widget.tenant.moveOutDate != null) ...[
                    const Divider(),
                    _buildInfoRow(
                      'Move-out Date',
                      _formatDate(widget.tenant.moveOutDate!),
                    ),
                  ],
                  const Divider(),
                  _buildHighlightedRow(
                    'Months Stayed',
                    '${widget.tenant.monthsStayed} months',
                    Colors.green,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRentHistoryTab() {
    if (_isLoadingHistory) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
            const SizedBox(height: 16),
            Text(
              _error!,
              style: const TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadRentHistory,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_rentHistory.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history, size: 64, color: Colors.grey.shade300),
            const SizedBox(height: 16),
            const Text(
              'No rent history available',
              style: TextStyle(color: Colors.grey, fontSize: 16),
            ),
            const SizedBox(height: 8),
            const Text(
              'Rent changes will appear here',
              style: TextStyle(color: Colors.grey, fontSize: 14),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadRentHistory,
      child: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: _rentHistory.length,
        itemBuilder: (context, index) {
          final entry = _rentHistory[index];
          return _buildRentHistoryCard(entry, index == 0);
        },
      ),
    );
  }

  Widget _buildRentHistoryCard(Map<String, dynamic> entry, bool isCurrent) {
    final oldRent = (entry['old_rent'] as num?)?.toDouble();
    final newRent = (entry['new_rent'] as num).toDouble();
    final changeType = entry['change_type'] as String;
    final effectiveDate = DateTime.parse(entry['effective_date'] as String);
    final reason = entry['reason'] as String?;
    final appliedBy = entry['applied_by'] as String?;

    final isIncrease = oldRent != null && newRent > oldRent;
    final percentageChange =
        oldRent != null ? ((newRent - oldRent) / oldRent * 100).abs() : 0.0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: isCurrent ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isCurrent
            ? BorderSide(color: Colors.blue.shade300, width: 2)
            : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      _getChangeTypeIcon(changeType),
                      color: _getChangeTypeColor(changeType),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _getChangeTypeLabel(changeType),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: _getChangeTypeColor(changeType),
                      ),
                    ),
                  ],
                ),
                if (isCurrent)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.blue,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      'CURRENT',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),

            // Rent Change Details
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (oldRent != null) ...[
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Previous',
                        style: TextStyle(color: Colors.grey, fontSize: 12),
                      ),
                      Text(
                        '\$${oldRent.toStringAsFixed(2)}',
                        style: const TextStyle(
                          fontSize: 16,
                          decoration: TextDecoration.lineThrough,
                        ),
                      ),
                    ],
                  ),
                  Icon(
                    Icons.arrow_forward,
                    color: isIncrease ? Colors.green : Colors.red,
                  ),
                ],
                Column(
                  crossAxisAlignment: oldRent != null
                      ? CrossAxisAlignment.end
                      : CrossAxisAlignment.start,
                  children: [
                    Text(
                      oldRent != null ? 'New' : 'Initial',
                      style: const TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                    Text(
                      '\$${newRent.toStringAsFixed(2)}',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.blue,
                      ),
                    ),
                  ],
                ),
              ],
            ),

            if (oldRent != null && percentageChange > 0) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isIncrease ? Colors.green.shade50 : Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${isIncrease ? '+' : '-'}${percentageChange.toStringAsFixed(1)}%',
                  style: TextStyle(
                    color: isIncrease
                        ? Colors.green.shade700
                        : Colors.red.shade700,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],

            const Divider(height: 24),

            // Metadata
            _buildHistoryInfoRow('Effective Date', _formatDate(effectiveDate)),
            if (reason != null && reason.isNotEmpty) ...[
              const SizedBox(height: 8),
              _buildHistoryInfoRow('Reason', reason),
            ],
            if (appliedBy != null) ...[
              const SizedBox(height: 8),
              _buildHistoryInfoRow('Applied By', appliedBy),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(color: Colors.grey, fontSize: 14),
        ),
        Text(
          value,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
      ],
    );
  }

  Widget _buildHighlightedRow(String label, String value, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 18,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildHistoryInfoRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$label: ',
          style: const TextStyle(color: Colors.grey, fontSize: 13),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontSize: 13),
          ),
        ),
      ],
    );
  }

  IconData _getChangeTypeIcon(String changeType) {
    switch (changeType) {
      case 'initial':
        return Icons.start;
      case 'automatic':
        return Icons.auto_mode;
      case 'manual':
        return Icons.edit;
      default:
        return Icons.change_circle;
    }
  }

  Color _getChangeTypeColor(String changeType) {
    switch (changeType) {
      case 'initial':
        return Colors.blue;
      case 'automatic':
        return Colors.green;
      case 'manual':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  String _getChangeTypeLabel(String changeType) {
    switch (changeType) {
      case 'initial':
        return 'Initial Rent';
      case 'automatic':
        return 'Automatic Increment';
      case 'manual':
        return 'Manual Override';
      default:
        return 'Rent Change';
    }
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
