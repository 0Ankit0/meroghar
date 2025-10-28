/// Expense list screen with category filters.
///
/// Implements T137 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/expense.dart';
import '../../models/property.dart';
import '../../providers/expense_provider.dart';
import '../../widgets/receipt_viewer_dialog.dart';
import 'expense_form_screen.dart';

class ExpenseListScreen extends StatefulWidget {
  const ExpenseListScreen({
    super.key,
    this.property,
  });
  final Property? property;

  @override
  State<ExpenseListScreen> createState() => _ExpenseListScreenState();
}

class _ExpenseListScreenState extends State<ExpenseListScreen> {
  ExpenseCategory? _filterCategory;
  ExpenseStatus? _filterStatus;
  DateTime? _filterStartDate;
  DateTime? _filterEndDate;

  @override
  void initState() {
    super.initState();
    _loadExpenses();
  }

  Future<void> _loadExpenses() async {
    final expenseProvider = context.read<ExpenseProvider>();
    await expenseProvider.fetchExpenses(
      propertyId: widget.property?.id,
      category: _filterCategory,
      status: _filterStatus,
      startDate: _filterStartDate,
      endDate: _filterEndDate,
    );
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) {
        var tempCategory = _filterCategory;
        var tempStatus = _filterStatus;
        var tempStartDate = _filterStartDate;
        var tempEndDate = _filterEndDate;

        return StatefulBuilder(
          builder: (context, setState) => AlertDialog(
            title: const Text('Filter Expenses'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Category filter
                  const Text('Category'),
                  DropdownButton<ExpenseCategory?>(
                    value: tempCategory,
                    isExpanded: true,
                    items: [
                      const DropdownMenuItem(
                        value: null,
                        child: Text('All Categories'),
                      ),
                      ...ExpenseCategory.values.map((category) {
                        return DropdownMenuItem(
                          value: category,
                          child: Text(category.displayName),
                        );
                      }),
                    ],
                    onChanged: (value) {
                      setState(() {
                        tempCategory = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Status filter
                  const Text('Status'),
                  DropdownButton<ExpenseStatus?>(
                    value: tempStatus,
                    isExpanded: true,
                    items: [
                      const DropdownMenuItem(
                        value: null,
                        child: Text('All Statuses'),
                      ),
                      ...ExpenseStatus.values.map((status) {
                        return DropdownMenuItem(
                          value: status,
                          child: Text(status.displayName),
                        );
                      }),
                    ],
                    onChanged: (value) {
                      setState(() {
                        tempStatus = value;
                      });
                    },
                  ),
                  const SizedBox(height: 16),

                  // Start date filter
                  ElevatedButton.icon(
                    icon: const Icon(Icons.date_range),
                    label: Text(
                      tempStartDate != null
                          ? 'From: ${tempStartDate!.day}/${tempStartDate!.month}/${tempStartDate!.year}'
                          : 'Select Start Date',
                    ),
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: tempStartDate ?? DateTime.now(),
                        firstDate: DateTime(2020),
                        lastDate: DateTime.now(),
                      );
                      if (picked != null) {
                        setState(() {
                          tempStartDate = picked;
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 8),

                  // End date filter
                  ElevatedButton.icon(
                    icon: const Icon(Icons.date_range),
                    label: Text(
                      tempEndDate != null
                          ? 'To: ${tempEndDate!.day}/${tempEndDate!.month}/${tempEndDate!.year}'
                          : 'Select End Date',
                    ),
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: tempEndDate ?? DateTime.now(),
                        firstDate: tempStartDate ?? DateTime(2020),
                        lastDate: DateTime.now(),
                      );
                      if (picked != null) {
                        setState(() {
                          tempEndDate = picked;
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
                    tempCategory = null;
                    tempStatus = null;
                    tempStartDate = null;
                    tempEndDate = null;
                  });
                },
                child: const Text('Clear'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  this.setState(() {
                    _filterCategory = tempCategory;
                    _filterStatus = tempStatus;
                    _filterStartDate = tempStartDate;
                    _filterEndDate = tempEndDate;
                  });
                  Navigator.pop(context);
                  _loadExpenses();
                },
                child: const Text('Apply'),
              ),
            ],
          ),
        );
      },
    );
  }

  Color _getStatusColor(ExpenseStatus status) {
    switch (status) {
      case ExpenseStatus.pending:
        return Colors.orange;
      case ExpenseStatus.approved:
        return Colors.blue;
      case ExpenseStatus.rejected:
        return Colors.red;
      case ExpenseStatus.reimbursed:
        return Colors.green;
    }
  }

  IconData _getCategoryIcon(ExpenseCategory category) {
    switch (category) {
      case ExpenseCategory.maintenance:
        return Icons.build;
      case ExpenseCategory.repair:
        return Icons.construction;
      case ExpenseCategory.cleaning:
        return Icons.cleaning_services;
      case ExpenseCategory.landscaping:
        return Icons.grass;
      case ExpenseCategory.security:
        return Icons.security;
      case ExpenseCategory.utilities:
        return Icons.electrical_services;
      case ExpenseCategory.insurance:
        return Icons.shield;
      case ExpenseCategory.taxes:
        return Icons.account_balance;
      case ExpenseCategory.legal:
        return Icons.gavel;
      case ExpenseCategory.administrative:
        return Icons.admin_panel_settings;
      case ExpenseCategory.other:
        return Icons.more_horiz;
    }
  }

  Future<void> _navigateToExpenseForm() async {
    if (widget.property == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a property first'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ExpenseFormScreen(
          property: widget.property!,
        ),
      ),
    );

    if (result != null && mounted) {
      _loadExpenses();
    }
  }

  Widget _buildExpenseCard(Expense expense) => Card(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: InkWell(
          onTap: () {
            // Navigate to expense detail screen
            _showExpenseDetail(expense);
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header row
                Row(
                  children: [
                    Icon(
                      _getCategoryIcon(expense.category),
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            expense.category.displayName,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          Text(
                            '${expense.expenseDate.day}/${expense.expenseDate.month}/${expense.expenseDate.year}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '\$${expense.amount.toStringAsFixed(2)}',
                          style:
                              Theme.of(context).textTheme.titleLarge?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                        ),
                        Chip(
                          label: Text(
                            expense.status.displayName,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                            ),
                          ),
                          backgroundColor: _getStatusColor(expense.status),
                          padding: EdgeInsets.zero,
                          visualDensity: VisualDensity.compact,
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Description
                Text(
                  expense.description,
                  style: Theme.of(context).textTheme.bodyMedium,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),

                // Vendor and invoice info
                if (expense.vendorName != null || expense.invoiceNumber != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Row(
                      children: [
                        if (expense.vendorName != null) ...[
                          const Icon(Icons.business, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            expense.vendorName!,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                        if (expense.vendorName != null &&
                            expense.invoiceNumber != null)
                          const SizedBox(width: 16),
                        if (expense.invoiceNumber != null) ...[
                          const Icon(Icons.receipt_long, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            expense.invoiceNumber!,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ],
                    ),
                  ),

                // Reimbursable badge
                if (expense.isReimbursable)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Row(
                      children: [
                        Icon(
                          expense.isReimbursed
                              ? Icons.check_circle
                              : Icons.pending,
                          size: 16,
                          color: expense.isReimbursed
                              ? Colors.green
                              : Colors.orange,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          expense.isReimbursed ? 'Reimbursed' : 'Reimbursable',
                          style:
                              Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: expense.isReimbursed
                                        ? Colors.green
                                        : Colors.orange,
                                  ),
                        ),
                      ],
                    ),
                  ),

                // Receipt indicator
                if (expense.receiptUrl != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Row(
                      children: [
                        const Icon(Icons.attach_file, size: 16),
                        const SizedBox(width: 4),
                        Text(
                          'Receipt attached',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
      );

  void _showExpenseDetail(Expense expense) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) {
          return SingleChildScrollView(
            controller: scrollController,
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      _getCategoryIcon(expense.category),
                      size: 32,
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        expense.category.displayName,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
                const Divider(height: 24),
                _buildDetailRow(
                    'Amount', '\$${expense.amount.toStringAsFixed(2)}'),
                _buildDetailRow('Date',
                    '${expense.expenseDate.day}/${expense.expenseDate.month}/${expense.expenseDate.year}'),
                _buildDetailRow('Status', expense.status.displayName),
                _buildDetailRow('Description', expense.description),
                if (expense.vendorName != null)
                  _buildDetailRow('Vendor', expense.vendorName!),
                if (expense.invoiceNumber != null)
                  _buildDetailRow('Invoice Number', expense.invoiceNumber!),
                if (expense.paidBy != null)
                  _buildDetailRow('Paid By', expense.paidBy!),
                _buildDetailRow(
                  'Reimbursable',
                  expense.isReimbursable ? 'Yes' : 'No',
                ),
                if (expense.isReimbursed)
                  _buildDetailRow(
                    'Reimbursed Date',
                    '${expense.reimbursedDate!.day}/${expense.reimbursedDate!.month}/${expense.reimbursedDate!.year}',
                  ),
                if (expense.approvedBy != null)
                  _buildDetailRow(
                    'Approved Date',
                    '${expense.approvedDate!.day}/${expense.approvedDate!.month}/${expense.approvedDate!.year}',
                  ),
                if (expense.rejectionReason != null)
                  _buildDetailRow('Rejection Reason', expense.rejectionReason!),
                if (expense.receiptUrl != null) ...[
                  const SizedBox(height: 16),
                  const Text('Receipt',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  // Display receipt image or view button
                  if (expense.receiptUrl != null &&
                      expense.receiptUrl!.isNotEmpty)
                    Column(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            expense.receiptUrl!,
                            height: 200,
                            width: double.infinity,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                height: 200,
                                color: Colors.grey[200],
                                child: const Center(
                                  child: Icon(Icons.error_outline, size: 48),
                                ),
                              );
                            },
                          ),
                        ),
                        const SizedBox(height: 8),
                        ElevatedButton.icon(
                          icon: const Icon(Icons.open_in_new),
                          label: const Text('View Full Receipt'),
                          onPressed: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => ReceiptViewerDialog(
                                  receiptUrl: expense.receiptUrl!,
                                  expenseName: expense.description,
                                ),
                              ),
                            );
                          },
                        ),
                      ],
                    )
                  else
                    const Text('No receipt attached',
                        style: TextStyle(color: Colors.grey)),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 120,
              child: Text(
                label,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  color: Colors.grey,
                ),
              ),
            ),
            Expanded(
              child: Text(
                value,
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) {
    final expenseProvider = context.watch<ExpenseProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Expenses'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadExpenses,
        child: expenseProvider.isLoading
            ? const Center(child: CircularProgressIndicator())
            : expenseProvider.hasError
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 48),
                        const SizedBox(height: 16),
                        Text(
                            expenseProvider.error ?? 'Failed to load expenses'),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: _loadExpenses,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : expenseProvider.expenses.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.receipt_long, size: 64),
                            const SizedBox(height: 16),
                            const Text('No expenses recorded yet'),
                            const SizedBox(height: 16),
                            if (widget.property != null)
                              ElevatedButton.icon(
                                icon: const Icon(Icons.add),
                                label: const Text('Record Expense'),
                                onPressed: _navigateToExpenseForm,
                              ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: expenseProvider.expenses.length,
                        itemBuilder: (context, index) => _buildExpenseCard(
                          expenseProvider.expenses[index],
                        ),
                      ),
      ),
      floatingActionButton: widget.property != null
          ? FloatingActionButton(
              onPressed: _navigateToExpenseForm,
              child: const Icon(Icons.add),
            )
          : null,
    );
  }
}
