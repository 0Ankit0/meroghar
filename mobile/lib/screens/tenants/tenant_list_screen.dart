/// Tenant list screen with card view.
///
/// Implements T049 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../models/tenant.dart';
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
                    Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
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
                    Icon(Icons.people_outline, size: 64, color: Colors.grey.shade400),
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

class _TenantCard extends StatelessWidget {
  final Tenant tenant;

  const _TenantCard({required this.tenant});

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
    final dateFormat = DateFormat('MMM dd, yyyy');

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      child: InkWell(
        onTap: () {
          // Navigate to tenant details
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    backgroundColor: tenant.status == TenantStatus.active
                        ? Colors.green.shade100
                        : Colors.grey.shade200,
                    child: Icon(
                      Icons.person,
                      color: tenant.status == TenantStatus.active
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
                          'Tenant ${tenant.id.substring(0, 8)}...',
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
                                color: tenant.status == TenantStatus.active
                                    ? Colors.green.shade100
                                    : Colors.grey.shade200,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                tenant.status.value.toUpperCase(),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: tenant.status == TenantStatus.active
                                      ? Colors.green.shade700
                                      : Colors.grey.shade700,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '${tenant.monthsStayed} months',
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
                        currencyFormat.format(tenant.monthlyRent),
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
              const Divider(height: 24),
              Row(
                children: [
                  Expanded(
                    child: _InfoItem(
                      icon: Icons.calendar_today,
                      label: 'Move In',
                      value: dateFormat.format(tenant.moveInDate),
                    ),
                  ),
                  Expanded(
                    child: _InfoItem(
                      icon: Icons.account_balance_wallet,
                      label: 'Deposit',
                      value: currencyFormat.format(tenant.securityDeposit),
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
                      value: '${tenant.electricityRate}/unit',
                    ),
                  ),
                  if (tenant.moveOutDate != null)
                    Expanded(
                      child: _InfoItem(
                        icon: Icons.exit_to_app,
                        label: 'Move Out',
                        value: dateFormat.format(tenant.moveOutDate!),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
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
