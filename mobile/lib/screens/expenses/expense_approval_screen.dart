/// Expense approval screen for property owners.
///
/// Implements T138 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/expense.dart';
import '../../providers/expense_provider.dart';

class ExpenseApprovalScreen extends StatefulWidget {
  final String propertyId;

  const ExpenseApprovalScreen({
    super.key,
    required this.propertyId,
  });

  @override
  State<ExpenseApprovalScreen> createState() => _ExpenseApprovalScreenState();
}

class _ExpenseApprovalScreenState extends State<ExpenseApprovalScreen> {
  @override
  void initState() {
    super.initState();
    _loadPendingExpenses();
  }

  Future<void> _loadPendingExpenses() async {
    final expenseProvider = context.read<ExpenseProvider>();
    await expenseProvider.fetchExpenses(
      propertyId: widget.propertyId,
      status: ExpenseStatus.pending,
    );
  }

  Color _getCategoryColor(ExpenseCategory category) {
    switch (category) {
      case ExpenseCategory.maintenance:
        return Colors.blue;
      case ExpenseCategory.repair:
        return Colors.orange;
      case ExpenseCategory.cleaning:
        return Colors.green;
      case ExpenseCategory.landscaping:
        return Colors.teal;
      case ExpenseCategory.security:
        return Colors.red;
      case ExpenseCategory.utilities:
        return Colors.amber;
      case ExpenseCategory.insurance:
        return Colors.indigo;
      case ExpenseCategory.taxes:
        return Colors.purple;
      case ExpenseCategory.legal:
        return Colors.brown;
      case ExpenseCategory.administrative:
        return Colors.grey;
      case ExpenseCategory.other:
        return Colors.blueGrey;
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

  Future<void> _approveExpense(Expense expense) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Approve Expense'),
        content: Text(
          'Are you sure you want to approve this expense of \$${expense.amount.toStringAsFixed(2)}?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
            ),
            child: const Text('Approve'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      final expenseProvider = context.read<ExpenseProvider>();
      final result = await expenseProvider.approveExpense(
        expenseId: expense.id,
        status: ExpenseStatus.approved,
      );

      if (mounted) {
        if (result != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Expense approved successfully'),
              backgroundColor: Colors.green,
            ),
          );
          _loadPendingExpenses();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                expenseProvider.error ?? 'Failed to approve expense',
              ),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  Future<void> _rejectExpense(Expense expense) async {
    final reasonController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reject Expense'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Reject expense of \$${expense.amount.toStringAsFixed(2)}?',
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: reasonController,
                decoration: const InputDecoration(
                  labelText: 'Rejection Reason',
                  border: OutlineInputBorder(),
                  hintText: 'Enter reason for rejection',
                ),
                maxLines: 3,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please provide a rejection reason';
                  }
                  return null;
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                Navigator.pop(context, true);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            child: const Text('Reject'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      final expenseProvider = context.read<ExpenseProvider>();
      final result = await expenseProvider.approveExpense(
        expenseId: expense.id,
        status: ExpenseStatus.rejected,
        rejectionReason: reasonController.text.trim(),
      );

      if (mounted) {
        if (result != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Expense rejected'),
              backgroundColor: Colors.orange,
            ),
          );
          _loadPendingExpenses();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                expenseProvider.error ?? 'Failed to reject expense',
              ),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }

    reasonController.dispose();
  }

  Widget _buildExpenseCard(Expense expense) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        children: [
          // Header with category
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _getCategoryColor(expense.category).withOpacity(0.1),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(8),
                topRight: Radius.circular(8),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  _getCategoryIcon(expense.category),
                  color: _getCategoryColor(expense.category),
                  size: 32,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        expense.category.displayName,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      Text(
                        '${expense.expenseDate.day}/${expense.expenseDate.month}/${expense.expenseDate.year}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                Text(
                  '\$${expense.amount.toStringAsFixed(2)}',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getCategoryColor(expense.category),
                      ),
                ),
              ],
            ),
          ),

          // Expense details
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Description
                Text(
                  'Description',
                  style: Theme.of(context).textTheme.labelSmall,
                ),
                const SizedBox(height: 4),
                Text(
                  expense.description,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 12),

                // Vendor and invoice
                if (expense.vendorName != null || expense.invoiceNumber != null)
                  Row(
                    children: [
                      if (expense.vendorName != null) ...[
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Vendor',
                                style: Theme.of(context).textTheme.labelSmall,
                              ),
                              const SizedBox(height: 4),
                              Text(expense.vendorName!),
                            ],
                          ),
                        ),
                      ],
                      if (expense.invoiceNumber != null) ...[
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Invoice',
                                style: Theme.of(context).textTheme.labelSmall,
                              ),
                              const SizedBox(height: 4),
                              Text(expense.invoiceNumber!),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),

                if (expense.paidBy != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Paid By',
                    style: Theme.of(context).textTheme.labelSmall,
                  ),
                  const SizedBox(height: 4),
                  Text(expense.paidBy!),
                ],

                // Reimbursable badge
                if (expense.isReimbursable) ...[
                  const SizedBox(height: 12),
                  Chip(
                    avatar: const Icon(Icons.info_outline, size: 16),
                    label: const Text('Reimbursable'),
                    backgroundColor: Colors.orange.withOpacity(0.1),
                  ),
                ],

                // Receipt indicator
                if (expense.receiptUrl != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.attach_file, size: 16),
                      const SizedBox(width: 4),
                      const Text('Receipt attached'),
                      const Spacer(),
                      TextButton.icon(
                        icon: const Icon(Icons.visibility),
                        label: const Text('View'),
                        onPressed: () {
                          // TODO: Open receipt viewer
                        },
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),

          // Action buttons
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.close),
                    label: const Text('Reject'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                    ),
                    onPressed: () => _rejectExpense(expense),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.check),
                    label: const Text('Approve'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                    ),
                    onPressed: () => _approveExpense(expense),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final expenseProvider = context.watch<ExpenseProvider>();
    final pendingExpenses = expenseProvider.expenses
        .where((e) => e.status == ExpenseStatus.pending)
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Pending Approvals'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadPendingExpenses,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadPendingExpenses,
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
                          onPressed: _loadPendingExpenses,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : pendingExpenses.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.check_circle_outline,
                              size: 64,
                              color: Colors.green.shade300,
                            ),
                            const SizedBox(height: 16),
                            const Text('No pending expenses to review'),
                            const SizedBox(height: 8),
                            Text(
                              'All expenses have been reviewed',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        itemCount: pendingExpenses.length,
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        itemBuilder: (context, index) {
                          return _buildExpenseCard(pendingExpenses[index]);
                        },
                      ),
      ),
    );
  }
}
