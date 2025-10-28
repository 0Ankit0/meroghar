/// Payment history screen with filters.
///
/// Implements T068 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/payment.dart';
import '../../providers/payment_provider.dart';
import 'receipt_view_screen.dart';

class PaymentHistoryScreen extends StatefulWidget {
  const PaymentHistoryScreen({
    super.key,
    this.tenantId,
    this.propertyId,
  });
  final String? tenantId;
  final String? propertyId;

  @override
  State<PaymentHistoryScreen> createState() => _PaymentHistoryScreenState();
}

class _PaymentHistoryScreenState extends State<PaymentHistoryScreen> {
  PaymentType? _filterType;
  PaymentStatus? _filterStatus;
  DateTime? _filterDateFrom;
  DateTime? _filterDateTo;

  @override
  void initState() {
    super.initState();
    _loadPayments();
  }

  Future<void> _loadPayments() async {
    final paymentProvider = context.read<PaymentProvider>();
    await paymentProvider.fetchPayments(
      tenantId: widget.tenantId,
      propertyId: widget.propertyId,
      paymentType: _filterType,
      paymentStatus: _filterStatus,
      dateFrom: _filterDateFrom,
      dateTo: _filterDateTo,
    );
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            title: const Text('Filter Payments'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Payment Type'),
                  DropdownButton<PaymentType?>(
                    value: _filterType,
                    isExpanded: true,
                    items: [
                      const DropdownMenuItem(
                        value: null,
                        child: Text('All Types'),
                      ),
                      ...PaymentType.values.map((type) {
                        return DropdownMenuItem(
                          value: type,
                          child: Text(type.displayName),
                        );
                      }),
                    ],
                    onChanged: (value) {
                      setState(() {
                        _filterType = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  const Text('Payment Status'),
                  DropdownButton<PaymentStatus?>(
                    value: _filterStatus,
                    isExpanded: true,
                    items: [
                      const DropdownMenuItem(
                        value: null,
                        child: Text('All Statuses'),
                      ),
                      ...PaymentStatus.values.map((status) {
                        return DropdownMenuItem(
                          value: status,
                          child: Text(status.displayName),
                        );
                      }),
                    ],
                    onChanged: (value) {
                      setState(() {
                        _filterStatus = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.date_range),
                    label: Text(
                      _filterDateFrom != null
                          ? 'From: ${_filterDateFrom!.day}/${_filterDateFrom!.month}/${_filterDateFrom!.year}'
                          : 'Select From Date',
                    ),
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: _filterDateFrom ?? DateTime.now(),
                        firstDate: DateTime(2020),
                        lastDate: DateTime.now(),
                      );
                      if (picked != null) {
                        setState(() {
                          _filterDateFrom = picked;
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.date_range),
                    label: Text(
                      _filterDateTo != null
                          ? 'To: ${_filterDateTo!.day}/${_filterDateTo!.month}/${_filterDateTo!.year}'
                          : 'Select To Date',
                    ),
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: _filterDateTo ?? DateTime.now(),
                        firstDate: _filterDateFrom ?? DateTime(2020),
                        lastDate: DateTime.now(),
                      );
                      if (picked != null) {
                        setState(() {
                          _filterDateTo = picked;
                        });
                      }
                    },
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () {
                  setState(() {
                    _filterType = null;
                    _filterStatus = null;
                    _filterDateFrom = null;
                    _filterDateTo = null;
                  });
                },
                child: const Text('Clear'),
              ),
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  this.setState(() {});
                  _loadPayments();
                },
                child: const Text('Apply'),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final paymentProvider = context.watch<PaymentProvider>();
    final payments = paymentProvider.payments;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Payment History'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
            tooltip: 'Filter',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadPayments,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: paymentProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : paymentProvider.hasError
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.error_outline,
                        size: 48,
                        color: Colors.red,
                      ),
                      const SizedBox(height: 16),
                      Text(paymentProvider.error ?? 'Failed to load payments'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadPayments,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : payments.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.payment,
                            size: 48,
                            color: Colors.grey,
                          ),
                          const SizedBox(height: 16),
                          const Text('No payments found'),
                          if (_filterType != null ||
                              _filterStatus != null ||
                              _filterDateFrom != null ||
                              _filterDateTo != null) ...[
                            const SizedBox(height: 8),
                            TextButton(
                              onPressed: () {
                                setState(() {
                                  _filterType = null;
                                  _filterStatus = null;
                                  _filterDateFrom = null;
                                  _filterDateTo = null;
                                });
                                _loadPayments();
                              },
                              child: const Text('Clear Filters'),
                            ),
                          ],
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadPayments,
                      child: ListView.builder(
                        itemCount: payments.length,
                        padding: const EdgeInsets.all(8),
                        itemBuilder: (context, index) {
                          final payment = payments[index];
                          return _PaymentCard(payment: payment);
                        },
                      ),
                    ),
    );
  }
}

class _PaymentCard extends StatelessWidget {
  const _PaymentCard({required this.payment});
  final Payment payment;

  Color _getStatusColor() {
    switch (payment.status) {
      case PaymentStatus.completed:
        return Colors.green;
      case PaymentStatus.pending:
        return Colors.orange;
      case PaymentStatus.failed:
        return Colors.red;
      case PaymentStatus.refunded:
        return Colors.blue;
    }
  }

  IconData _getPaymentMethodIcon() {
    switch (payment.paymentMethod) {
      case PaymentMethod.cash:
        return Icons.money;
      case PaymentMethod.bankTransfer:
        return Icons.account_balance;
      case PaymentMethod.upi:
        return Icons.qr_code_2;
      case PaymentMethod.cheque:
        return Icons.receipt;
      case PaymentMethod.card:
        return Icons.credit_card;
      case PaymentMethod.online:
        return Icons.language;
    }
  }

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        child: InkWell(
          onTap: () {
            _showPaymentDetails(context);
          },
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      _getPaymentMethodIcon(),
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            payment.paymentType.displayName,
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                          ),
                          Text(
                            '${payment.paymentDate.day}/${payment.paymentDate.month}/${payment.paymentDate.year}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          payment.formattedAmount,
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: Theme.of(context).primaryColor,
                                  ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: _getStatusColor().withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: _getStatusColor(),
                              width: 1,
                            ),
                          ),
                          child: Text(
                            payment.status.displayName,
                            style: TextStyle(
                              fontSize: 12,
                              color: _getStatusColor(),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                if (payment.periodDisplay != null) ...[
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.calendar_today, size: 16),
                      const SizedBox(width: 4),
                      Text(
                        'Period: ${payment.periodDisplay}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
                if (payment.transactionReference != null) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.receipt_long, size: 16),
                      const SizedBox(width: 4),
                      Text(
                        'Ref: ${payment.transactionReference}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
      );

  void _showPaymentDetails(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) {
          return SingleChildScrollView(
            controller: scrollController,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'Payment Details',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const Divider(height: 32),
                _DetailRow(
                  label: 'Amount',
                  value: payment.formattedAmount,
                  valueStyle: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
                _DetailRow(
                  label: 'Payment Type',
                  value: payment.paymentType.displayName,
                ),
                _DetailRow(
                  label: 'Payment Method',
                  value: payment.paymentMethod.displayName,
                ),
                _DetailRow(
                  label: 'Status',
                  value: payment.status.displayName,
                ),
                _DetailRow(
                  label: 'Payment Date',
                  value:
                      '${payment.paymentDate.day}/${payment.paymentDate.month}/${payment.paymentDate.year}',
                ),
                if (payment.periodDisplay != null)
                  _DetailRow(
                    label: 'Payment Period',
                    value: payment.periodDisplay!,
                  ),
                if (payment.transactionReference != null)
                  _DetailRow(
                    label: 'Transaction Reference',
                    value: payment.transactionReference!,
                  ),
                if (payment.notes != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    'Notes',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(payment.notes!),
                ],
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.receipt),
                    label: const Text('View Receipt'),
                    onPressed: () {
                      Navigator.pop(context); // Close the bottom sheet
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => ReceiptViewScreen(
                            paymentId: payment.id,
                            tenantName: payment.tenantId,
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({
    required this.label,
    required this.value,
    this.valueStyle,
  });
  final String label;
  final String value;
  final TextStyle? valueStyle;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 140,
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
              ),
            ),
            Expanded(
              child: Text(
                value,
                style: valueStyle ??
                    Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
              ),
            ),
          ],
        ),
      );
}
