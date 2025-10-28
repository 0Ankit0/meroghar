/// Tenant dashboard screen with bill information.
///
/// Implements T092 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../models/bill.dart';
import '../../models/payment.dart';
import '../../models/user.dart';
import '../../providers/bill_provider.dart';
import '../../providers/payment_provider.dart';
import '../../providers/auth_provider.dart';

class TenantDashboardScreen extends StatefulWidget {
  const TenantDashboardScreen({super.key});

  @override
  State<TenantDashboardScreen> createState() => _TenantDashboardScreenState();
}

class _TenantDashboardScreenState extends State<TenantDashboardScreen> {
  final _currencyFormat = NumberFormat.currency(symbol: '₹');
  final _dateFormat = DateFormat('MMM dd, yyyy');

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final authProvider = context.read<AuthProvider>();
    final user = authProvider.currentUser;

    if (user != null && user.role == UserRole.tenant) {
      final billProvider = context.read<BillProvider>();
      final paymentProvider = context.read<PaymentProvider>();

      // For tenants, use user ID as tenant filter
      await Future.wait([
        billProvider.fetchBills(),
        paymentProvider.fetchPayments(tenantId: user.id),
      ]);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Dashboard'),
        ),
        body: Consumer3<AuthProvider, BillProvider, PaymentProvider>(
          builder:
              (context, authProvider, billProvider, paymentProvider, child) {
            final user = authProvider.currentUser;

            if (user == null || user.role != UserRole.tenant) {
              return const Center(
                child: Text('This dashboard is for tenants only'),
              );
            }

            // For tenants, user.id represents their tenant ID
            final tenantId = user.id;

            if (billProvider.isLoading || paymentProvider.isLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            // Get tenant's bills and allocations
            final myBills = billProvider.getBillsForTenant(tenantId);
            final unpaidAllocations =
                billProvider.getUnpaidAllocationsForTenant(tenantId);
            final totalUnpaid = billProvider.getTotalUnpaidForTenant(tenantId);

            // Get recent payments
            final recentPayments =
                paymentProvider.getPaymentsByTenant(tenantId).take(5).toList();

            return RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Balance Summary Card
                  _BalanceSummaryCard(
                    totalUnpaid: totalUnpaid,
                    unpaidCount: unpaidAllocations.length,
                    currencyFormat: _currencyFormat,
                  ),
                  const SizedBox(height: 16),

                  // Overdue Bills Section
                  _OverdueBillsSection(
                    bills: myBills.where((b) => b.isOverdue).toList(),
                    tenantId: tenantId,
                    currencyFormat: _currencyFormat,
                    dateFormat: _dateFormat,
                  ),
                  const SizedBox(height: 16),

                  // Pending Bills Section
                  _PendingBillsSection(
                    bills: myBills
                        .where((b) =>
                            !b.isOverdue &&
                            (b.status == BillStatus.pending ||
                                b.status == BillStatus.partiallyPaid))
                        .toList(),
                    tenantId: tenantId,
                    currencyFormat: _currencyFormat,
                    dateFormat: _dateFormat,
                  ),
                  const SizedBox(height: 16),

                  // Recent Payments Section
                  _RecentPaymentsSection(
                    payments: recentPayments,
                    currencyFormat: _currencyFormat,
                    dateFormat: _dateFormat,
                  ),
                ],
              ),
            );
          },
        ),
      );
}

class _BalanceSummaryCard extends StatelessWidget {
  const _BalanceSummaryCard({
    required this.totalUnpaid,
    required this.unpaidCount,
    required this.currencyFormat,
  });
  final double totalUnpaid;
  final int unpaidCount;
  final NumberFormat currencyFormat;

  @override
  Widget build(BuildContext context) => Card(
        elevation: 4,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Outstanding Balance',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                currencyFormat.format(totalUnpaid),
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: totalUnpaid > 0 ? Colors.red : Colors.green,
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                '$unpaidCount unpaid bill(s)',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      );
}

class _OverdueBillsSection extends StatelessWidget {
  const _OverdueBillsSection({
    required this.bills,
    required this.tenantId,
    required this.currencyFormat,
    required this.dateFormat,
  });
  final List<Bill> bills;
  final String tenantId;
  final NumberFormat currencyFormat;
  final DateFormat dateFormat;

  @override
  Widget build(BuildContext context) {
    if (bills.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.warning, color: Colors.red),
            const SizedBox(width: 8),
            Text(
              'Overdue Bills',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.red,
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...bills.map((bill) {
          final myAllocation =
              bill.allocations.cast<BillAllocation?>().firstWhere(
                    (alloc) => alloc?.tenantId == tenantId,
                    orElse: () => null,
                  );

          return Card(
            color: Colors.red.shade50,
            margin: const EdgeInsets.symmetric(vertical: 4),
            child: ListTile(
              title: Text(bill.billType.displayName),
              subtitle: Text('Due: ${dateFormat.format(bill.dueDate)}'),
              trailing: myAllocation != null
                  ? Text(
                      currencyFormat.format(myAllocation.allocatedAmount),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    )
                  : null,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  '/bills/detail',
                  arguments: {'billId': bill.id},
                );
              },
            ),
          );
        }),
      ],
    );
  }
}

class _PendingBillsSection extends StatelessWidget {
  const _PendingBillsSection({
    required this.bills,
    required this.tenantId,
    required this.currencyFormat,
    required this.dateFormat,
  });
  final List<Bill> bills;
  final String tenantId;
  final NumberFormat currencyFormat;
  final DateFormat dateFormat;

  @override
  Widget build(BuildContext context) {
    if (bills.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'No pending bills',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.green,
                ),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Pending Bills',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        ...bills.take(5).map((bill) {
          final myAllocation =
              bill.allocations.cast<BillAllocation?>().firstWhere(
                    (alloc) => alloc?.tenantId == tenantId,
                    orElse: () => null,
                  );

          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4),
            child: ListTile(
              title: Text(bill.billType.displayName),
              subtitle: Text('Due: ${dateFormat.format(bill.dueDate)}'),
              trailing: myAllocation != null
                  ? Text(
                      currencyFormat.format(myAllocation.allocatedAmount),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    )
                  : null,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  '/bills/detail',
                  arguments: {'billId': bill.id},
                );
              },
            ),
          );
        }),
        if (bills.length > 5)
          TextButton(
            onPressed: () {
              Navigator.pushNamed(context, '/bills');
            },
            child: const Text('View All Bills'),
          ),
      ],
    );
  }
}

class _RecentPaymentsSection extends StatelessWidget {
  const _RecentPaymentsSection({
    required this.payments,
    required this.currencyFormat,
    required this.dateFormat,
  });
  final List<Payment> payments;
  final NumberFormat currencyFormat;
  final DateFormat dateFormat;

  @override
  Widget build(BuildContext context) {
    if (payments.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Recent Payments',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        ...payments.map((payment) => Card(
              margin: const EdgeInsets.symmetric(vertical: 4),
              child: ListTile(
                leading: const Icon(Icons.payment, color: Colors.green),
                title: Text(payment.paymentType.displayName),
                subtitle: Text(dateFormat.format(payment.paymentDate)),
                trailing: Text(
                  currencyFormat.format(payment.amount),
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
              ),
            )),
        TextButton(
          onPressed: () {
            Navigator.pushNamed(context, '/payments');
          },
          child: const Text('View All Payments'),
        ),
      ],
    );
  }
}
