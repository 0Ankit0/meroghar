/// Bill allocation detail screen.
///
/// Implements T090 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../models/bill.dart';
import '../../providers/bill_provider.dart';

class BillAllocationScreen extends StatefulWidget {
  final String billId;

  const BillAllocationScreen({super.key, required this.billId});

  @override
  State<BillAllocationScreen> createState() => _BillAllocationScreenState();
}

class _BillAllocationScreenState extends State<BillAllocationScreen> {
  final _currencyFormat = NumberFormat.currency(symbol: '₹');
  final _dateFormat = DateFormat('MMM dd, yyyy');

  @override
  void initState() {
    super.initState();
    _loadBill();
  }

  Future<void> _loadBill() async {
    final provider = context.read<BillProvider>();
    await provider.fetchBillById(widget.billId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bill Allocations')),
      body: Consumer<BillProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          final bill = provider.bills
              .cast<Bill?>()
              .firstWhere((b) => b?.id == widget.billId, orElse: () => null);

          if (bill == null) {
            return const Center(child: Text('Bill not found'));
          }

          return RefreshIndicator(
            onRefresh: _loadBill,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _BillSummaryCard(
                  bill: bill,
                  currencyFormat: _currencyFormat,
                  dateFormat: _dateFormat,
                ),
                const SizedBox(height: 16),
                Text(
                  'Allocations',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                ...bill.allocations.map((allocation) {
                  return _AllocationCard(
                    billId: widget.billId,
                    allocation: allocation,
                    currencyFormat: _currencyFormat,
                  );
                }),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _BillSummaryCard extends StatelessWidget {
  final Bill bill;
  final NumberFormat currencyFormat;
  final DateFormat dateFormat;

  const _BillSummaryCard({
    required this.bill,
    required this.currencyFormat,
    required this.dateFormat,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              bill.billType.displayName,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text('Total: ${currencyFormat.format(bill.totalAmount)}'),
            Text('Paid: ${currencyFormat.format(bill.totalPaid)}'),
            Text('Method: ${bill.allocationMethod.displayName}'),
            Text('Due: ${dateFormat.format(bill.dueDate)}'),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: bill.totalAmount > 0 
                  ? bill.totalPaid / bill.totalAmount 
                  : 0,
            ),
            const SizedBox(height: 4),
            Text(
              '${bill.paidCount}/${bill.allocations.length} tenants paid',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _AllocationCard extends StatelessWidget {
  final String billId;
  final BillAllocation allocation;
  final NumberFormat currencyFormat;

  const _AllocationCard({
    required this.billId,
    required this.allocation,
    required this.currencyFormat,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        title: Text(currencyFormat.format(allocation.allocatedAmount)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (allocation.percentage != null)
              Text('${allocation.percentage}% of total'),
            if (allocation.notes != null) Text(allocation.notes!),
          ],
        ),
        trailing: allocation.isPaid
            ? const Icon(Icons.check_circle, color: Colors.green)
            : ElevatedButton(
                onPressed: () => _markAsPaid(context),
                child: const Text('Mark Paid'),
              ),
      ),
    );
  }

  Future<void> _markAsPaid(BuildContext context) async {
    final provider = context.read<BillProvider>();
    final success = await provider.markAllocationAsPaid(
      billId: billId,
      allocationId: allocation.id,
    );

    if (success && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Marked as paid')),
      );
    }
  }
}
