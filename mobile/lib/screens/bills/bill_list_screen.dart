/// Bill list screen for displaying bills.
///
/// Implements T091 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../models/bill.dart';
import '../../providers/bill_provider.dart';

class BillListScreen extends StatefulWidget {
  const BillListScreen({
    super.key,
    this.propertyId,
    this.tenantId,
  });
  final String? propertyId;
  final String? tenantId;

  @override
  State<BillListScreen> createState() => _BillListScreenState();
}

class _BillListScreenState extends State<BillListScreen> {
  final _currencyFormat = NumberFormat.currency(symbol: '₹');
  final _dateFormat = DateFormat('MMM dd, yyyy');

  BillStatus? _filterStatus;
  BillType? _filterType;

  @override
  void initState() {
    super.initState();
    _loadBills();
  }

  Future<void> _loadBills() async {
    final provider = context.read<BillProvider>();
    await provider.fetchBills(
      propertyId: widget.propertyId,
      status: _filterStatus,
      billType: _filterType,
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Bills'),
          actions: [
            IconButton(
              icon: const Icon(Icons.filter_list),
              onPressed: _showFilterDialog,
            ),
          ],
        ),
        body: Consumer<BillProvider>(
          builder: (context, provider, child) {
            if (provider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            if (provider.hasError) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(provider.error ?? 'An error occurred'),
                    ElevatedButton(
                      onPressed: _loadBills,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              );
            }

            // Filter bills
            List<Bill> bills = provider.bills;
            if (widget.propertyId != null) {
              bills = provider.getBillsByProperty(widget.propertyId!);
            }
            if (widget.tenantId != null) {
              bills = provider.getBillsForTenant(widget.tenantId!);
            }
            if (_filterStatus != null) {
              bills = bills.where((b) => b.status == _filterStatus).toList();
            }
            if (_filterType != null) {
              bills = bills.where((b) => b.billType == _filterType).toList();
            }

            if (bills.isEmpty) {
              return const Center(
                child: Text('No bills found'),
              );
            }

            return RefreshIndicator(
              onRefresh: _loadBills,
              child: ListView.builder(
                itemCount: bills.length,
                itemBuilder: (context, index) {
                  final bill = bills[index];
                  return _BillCard(
                    bill: bill,
                    tenantId: widget.tenantId,
                    currencyFormat: _currencyFormat,
                    dateFormat: _dateFormat,
                  );
                },
              ),
            );
          },
        ),
        floatingActionButton:
            widget.propertyId != null && widget.tenantId == null
                ? FloatingActionButton(
                    onPressed: () {
                      // Navigate to create bill screen
                      Navigator.pushNamed(
                        context,
                        '/bills/create',
                        arguments: {'propertyId': widget.propertyId},
                      );
                    },
                    child: const Icon(Icons.add),
                  )
                : null,
      );

  Future<void> _showFilterDialog() async {
    await showDialog(
      context: context,
      builder: (context) {
        var tempStatus = _filterStatus;
        var tempType = _filterType;

        return StatefulBuilder(
          builder: (context, setState) => AlertDialog(
            title: const Text('Filter Bills'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<BillStatus>(
                  value: tempStatus,
                  decoration: const InputDecoration(labelText: 'Status'),
                  items: [
                    const DropdownMenuItem(
                      value: null,
                      child: Text('All'),
                    ),
                    ...BillStatus.values.map((status) {
                      return DropdownMenuItem(
                        value: status,
                        child: Text(status.displayName),
                      );
                    }),
                  ],
                  onChanged: (value) => setState(() => tempStatus = value),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<BillType>(
                  value: tempType,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: [
                    const DropdownMenuItem(
                      value: null,
                      child: Text('All'),
                    ),
                    ...BillType.values.map((type) {
                      return DropdownMenuItem(
                        value: type,
                        child: Text(type.displayName),
                      );
                    }),
                  ],
                  onChanged: (value) => setState(() => tempType = value),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
              TextButton(
                onPressed: () {
                  setState(() {
                    _filterStatus = tempStatus;
                    _filterType = tempType;
                  });
                  Navigator.pop(context);
                  _loadBills();
                },
                child: const Text('Apply'),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _BillCard extends StatelessWidget {
  const _BillCard({
    required this.bill,
    this.tenantId,
    required this.currencyFormat,
    required this.dateFormat,
  });
  final Bill bill;
  final String? tenantId;
  final NumberFormat currencyFormat;
  final DateFormat dateFormat;

  @override
  Widget build(BuildContext context) {
    // Get allocation for this tenant if tenantId provided
    BillAllocation? myAllocation;
    if (tenantId != null) {
      myAllocation = bill.allocations.cast<BillAllocation?>().firstWhere(
            (alloc) => alloc?.tenantId == tenantId,
            orElse: () => null,
          );
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: () {
          Navigator.pushNamed(
            context,
            '/bills/detail',
            arguments: {'billId': bill.id},
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      bill.billType.displayName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  _StatusChip(status: bill.status),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Period: ${dateFormat.format(bill.periodStart)} - ${dateFormat.format(bill.periodEnd)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 4),
              Text(
                'Due: ${dateFormat.format(bill.dueDate)}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: bill.isOverdue ? Colors.red : null,
                      fontWeight:
                          bill.isOverdue ? FontWeight.bold : FontWeight.normal,
                    ),
              ),
              const SizedBox(height: 8),
              if (myAllocation != null) ...[
                Text(
                  'Your Share: ${currencyFormat.format(myAllocation.allocatedAmount)}',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: Theme.of(context).primaryColor,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                if (myAllocation.percentage != null)
                  Text(
                    '(${myAllocation.percentage}% of total)',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                if (myAllocation.isPaid)
                  const Text(
                    '✓ Paid',
                    style: TextStyle(color: Colors.green),
                  )
                else
                  const Text(
                    '✗ Unpaid',
                    style: TextStyle(color: Colors.red),
                  ),
              ] else ...[
                Text(
                  'Total: ${currencyFormat.format(bill.totalAmount)}',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  '${bill.paidCount}/${bill.allocations.length} tenants paid',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
              if (bill.description != null) ...[
                const SizedBox(height: 4),
                Text(
                  bill.description!,
                  style: Theme.of(context).textTheme.bodySmall,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final BillStatus status;

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (status) {
      case BillStatus.pending:
        color = Colors.orange;
        break;
      case BillStatus.partiallyPaid:
        color = Colors.blue;
        break;
      case BillStatus.paid:
        color = Colors.green;
        break;
      case BillStatus.overdue:
        color = Colors.red;
        break;
    }

    return Chip(
      label: Text(
        status.displayName,
        style: const TextStyle(color: Colors.white, fontSize: 12),
      ),
      backgroundColor: color,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }
}
