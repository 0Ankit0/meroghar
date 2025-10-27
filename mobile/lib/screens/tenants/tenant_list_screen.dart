/// Tenant list screen with card view.
///
/// Implements T049 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../models/tenant.dart';
import '../../models/payment.dart';
import '../../providers/payment_provider.dart';
import '../../services/api_service.dart';

class TenantListScreen extends StatefulWidget {
  final String? propertyId;

  const TenantListScreen({
    super.key,
    this.propertyId,
  });

  @override
  State<TenantListScreen> createState() => _TenantListScreenState();
}

class _TenantListScreenState extends State<TenantListScreen> {
  final _searchController = TextEditingController();
  List<Tenant> _tenants = [];
  List<Tenant> _filteredTenants = [];
  bool _isLoading = true;
  String? _errorMessage;
  TenantStatus? _statusFilter;

  @override
  void initState() {
    super.initState();
    _loadTenants();
    _searchController.addListener(_filterTenants);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadTenants() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiService = ApiService.instance;
      final queryParams = <String, dynamic>{};
      if (widget.propertyId != null) {
        queryParams['property_id'] = widget.propertyId;
      }
      if (_statusFilter != null) {
        queryParams['status'] = _statusFilter!.value;
      }

      final response = await apiService.get(
        '/api/v1/tenants',
        queryParameters: queryParams,
      );

      if (!mounted) return;

      if (response.isSuccess && response.data != null) {
        final data = response.data as Map<String, dynamic>;
        final tenantsData = data['data'] as List<dynamic>;
        setState(() {
          _tenants = tenantsData
              .map((json) => Tenant.fromJson(json as Map<String, dynamic>))
              .toList();
          _filteredTenants = _tenants;
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = response.message ?? 'Failed to load tenants';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  void _filterTenants() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      _filteredTenants = _tenants.where((tenant) {
        // Filter by search query (would need user/property data for better filtering)
        return tenant.id.toLowerCase().contains(query);
      }).toList();
    });
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Filter Tenants'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              title: const Text('All'),
              leading: Radio<TenantStatus?>(
                value: null,
                groupValue: _statusFilter,
                onChanged: (value) {
                  setState(() => _statusFilter = value);
                  Navigator.pop(context);
                  _loadTenants();
                },
              ),
            ),
            ListTile(
              title: const Text('Active'),
              leading: Radio<TenantStatus?>(
                value: TenantStatus.active,
                groupValue: _statusFilter,
                onChanged: (value) {
                  setState(() => _statusFilter = value);
                  Navigator.pop(context);
                  _loadTenants();
                },
              ),
            ),
            ListTile(
              title: const Text('Moved Out'),
              leading: Radio<TenantStatus?>(
                value: TenantStatus.movedOut,
                groupValue: _statusFilter,
                onChanged: (value) {
                  setState(() => _statusFilter = value);
                  Navigator.pop(context);
                  _loadTenants();
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tenants'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadTenants,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search tenants...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                filled: true,
                fillColor: Colors.grey.shade100,
              ),
            ),
          ),
          if (_isLoading)
            const Expanded(
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_errorMessage != null)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.error_outline,
                        size: 64, color: Colors.red.shade300),
                    const SizedBox(height: 16),
                    Text(_errorMessage!),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _loadTenants,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            )
          else if (_filteredTenants.isEmpty)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.people_outline,
                        size: 64, color: Colors.grey.shade400),
                    const SizedBox(height: 16),
                    Text(
                      'No tenants found',
                      style: TextStyle(
                        fontSize: 18,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            Expanded(
              child: RefreshIndicator(
                onRefresh: _loadTenants,
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _filteredTenants.length,
                  itemBuilder: (context, index) {
                    final tenant = _filteredTenants[index];
                    return _TenantCard(tenant: tenant);
                  },
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Navigate to tenant creation
          Navigator.pushNamed(context, '/tenants/create');
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}

class _TenantCard extends StatefulWidget {
  final Tenant tenant;

  const _TenantCard({required this.tenant});

  @override
  State<_TenantCard> createState() => _TenantCardState();
}

class _TenantCardState extends State<_TenantCard> {
  TenantBalance? _balance;
  bool _isLoadingBalance = true;

  @override
  void initState() {
    super.initState();
    _loadBalance();
  }

  Future<void> _loadBalance() async {
    try {
      final paymentProvider = context.read<PaymentProvider>();
      await paymentProvider.fetchTenantBalance(tenantId: widget.tenant.id);
      if (mounted) {
        setState(() {
          _balance = paymentProvider.currentBalance;
          _isLoadingBalance = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingBalance = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final currencyFormat =
        NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final dateFormat = DateFormat('MMM dd, yyyy');

    // Determine if payment is overdue
    final isOverdue = _balance != null &&
        _balance!.outstandingBalance > 0 &&
        _balance!.monthsBehind > 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: isOverdue ? 4 : 2,
      color: isOverdue ? Colors.red.shade50 : null,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isOverdue
            ? BorderSide(color: Colors.red.shade300, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: () {
          // Navigate to tenant details
        },
        borderRadius: BorderRadius.circular(12),
        child: Stack(
          children: [
            // Overdue badge
            if (isOverdue)
              Positioned(
                top: 8,
                right: 8,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.red.shade700,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.warning,
                        size: 14,
                        color: Colors.white,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'OVERDUE',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
              Row(
                children: [
                  CircleAvatar(
                    backgroundColor: widget.tenant.status == TenantStatus.active
                        ? Colors.green.shade100
                        : Colors.grey.shade200,
                    child: Icon(
                      Icons.person,
                      color: widget.tenant.status == TenantStatus.active
                          ? Colors.green.shade700
                          : Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Tenant ${widget.tenant.id.substring(0, 8)}...',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: widget.tenant.status == TenantStatus.active
                                    ? Colors.green.shade100
                                    : Colors.grey.shade200,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                widget.tenant.status.value.toUpperCase(),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: widget.tenant.status == TenantStatus.active
                                      ? Colors.green.shade700
                                      : Colors.grey.shade700,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '${widget.tenant.monthsStayed} months',
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        currencyFormat.format(widget.tenant.monthlyRent),
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                          color: Colors.blue,
                        ),
                      ),
                      Text(
                        'per month',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              // Payment Status Badge Section
              if (!_isLoadingBalance && _balance != null) ...[
                const SizedBox(height: 12),
                _buildPaymentStatusBadge(currencyFormat),
              ],
              const Divider(height: 24),
              Row(
                children: [
                  Expanded(
                    child: _InfoItem(
                      icon: Icons.calendar_today,
                      label: 'Move In',
                      value: dateFormat.format(widget.tenant.moveInDate),
                    ),
                  ),
                  Expanded(
                    child: _InfoItem(
                      icon: Icons.account_balance_wallet,
                      label: 'Deposit',
                      value: currencyFormat.format(widget.tenant.securityDeposit),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: _InfoItem(
                      icon: Icons.electric_bolt,
                      label: 'Electricity',
                      value: '${widget.tenant.electricityRate}/unit',
                    ),
                  ),
                  if (widget.tenant.moveOutDate != null)
                    Expanded(
                      child: _InfoItem(
                        icon: Icons.exit_to_app,
                        label: 'Move Out',
                        value: dateFormat.format(widget.tenant.moveOutDate!),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
          ],
        ),
      ),
    );
  }

  Widget _buildPaymentStatusBadge(NumberFormat currencyFormat) {
    final balance = _balance!;
    final hasOutstanding = balance.outstandingBalance > 0;
    final monthsBehind = balance.monthsBehind;

    // Determine status color
    Color backgroundColor;
    Color textColor;
    IconData icon;
    String statusText;

    if (!hasOutstanding) {
      // All paid up
      backgroundColor = Colors.green.shade50;
      textColor = Colors.green.shade700;
      icon = Icons.check_circle;
      statusText = 'Paid Up';
    } else if (monthsBehind > 0) {
      // Overdue
      backgroundColor = Colors.red.shade50;
      textColor = Colors.red.shade700;
      icon = Icons.error;
      statusText = '$monthsBehind ${monthsBehind == 1 ? 'Month' : 'Months'} Behind';
    } else {
      // Outstanding but not yet overdue
      backgroundColor = Colors.orange.shade50;
      textColor = Colors.orange.shade700;
      icon = Icons.warning;
      statusText = 'Outstanding';
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: textColor.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: textColor),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  statusText,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: textColor,
                  ),
                ),
                if (hasOutstanding) ...[
                  const SizedBox(height: 2),
                  Text(
                    'Outstanding: ${currencyFormat.format(balance.outstandingBalance)}',
                    style: TextStyle(
                      fontSize: 12,
                      color: textColor,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (hasOutstanding)
            Icon(Icons.arrow_forward_ios, size: 16, color: textColor),
        ],
      ),
    );
  }
}

class _InfoItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoItem({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 16, color: Colors.grey.shade600),
        const SizedBox(width: 4),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey.shade600,
              ),
            ),
            Text(
              value,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
