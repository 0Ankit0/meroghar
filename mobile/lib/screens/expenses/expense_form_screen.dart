/// Expense recording form screen with image picker.
///
/// Implements T136 from tasks.md.
library;

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../models/expense.dart';
import '../../models/property.dart';
import '../../providers/expense_provider.dart';

class ExpenseFormScreen extends StatefulWidget {
  // For editing existing expense

  const ExpenseFormScreen({
    super.key,
    required this.property,
    this.expense,
  });
  final Property property;
  final Expense? expense;

  @override
  State<ExpenseFormScreen> createState() => _ExpenseFormScreenState();
}

class _ExpenseFormScreenState extends State<ExpenseFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _vendorNameController = TextEditingController();
  final _invoiceNumberController = TextEditingController();
  final _paidByController = TextEditingController();

  ExpenseCategory _selectedCategory = ExpenseCategory.maintenance;
  DateTime _expenseDate = DateTime.now();
  bool _isReimbursable = true;
  File? _receiptImage;
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void initState() {
    super.initState();
    if (widget.expense != null) {
      _loadExpenseData();
    }
  }

  void _loadExpenseData() {
    final expense = widget.expense!;
    _amountController.text = expense.amount.toStringAsFixed(2);
    _descriptionController.text = expense.description;
    _vendorNameController.text = expense.vendorName ?? '';
    _invoiceNumberController.text = expense.invoiceNumber ?? '';
    _paidByController.text = expense.paidBy ?? '';
    _selectedCategory = expense.category;
    _expenseDate = expense.expenseDate;
    _isReimbursable = expense.isReimbursable;
  }

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    _vendorNameController.dispose();
    _invoiceNumberController.dispose();
    _paidByController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _expenseDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      helpText: 'Select expense date',
    );

    if (picked != null && picked != _expenseDate) {
      setState(() {
        _expenseDate = picked;
      });
    }
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final pickedFile = await _imagePicker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (pickedFile != null) {
        setState(() {
          _receiptImage = File(pickedFile.path);
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to pick image: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Camera'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Gallery'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _submitExpense() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final expenseProvider = context.read<ExpenseProvider>();

    // Record expense
    final expense = await expenseProvider.recordExpense(
      propertyId: widget.property.id,
      amount: double.parse(_amountController.text),
      category: _selectedCategory,
      expenseDate: _expenseDate,
      description: _descriptionController.text,
      vendorName: _vendorNameController.text.isNotEmpty
          ? _vendorNameController.text
          : null,
      invoiceNumber: _invoiceNumberController.text.isNotEmpty
          ? _invoiceNumberController.text
          : null,
      paidBy: _paidByController.text.isNotEmpty ? _paidByController.text : null,
      isReimbursable: _isReimbursable,
    );

    if (!mounted) return;

    if (expense == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            expenseProvider.error ?? 'Failed to record expense',
          ),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Upload receipt if selected
    if (_receiptImage != null) {
      final updatedExpense = await expenseProvider.uploadReceipt(
        expenseId: expense.id,
        receiptFile: _receiptImage!,
      );

      if (!mounted) return;

      if (updatedExpense == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              expenseProvider.error ?? 'Failed to upload receipt',
            ),
            backgroundColor: Colors.orange,
          ),
        );
      }
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Expense recorded successfully'),
          backgroundColor: Colors.green,
        ),
      );
      Navigator.pop(context, expense);
    }
  }

  @override
  Widget build(BuildContext context) {
    final expenseProvider = context.watch<ExpenseProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.expense == null ? 'Record Expense' : 'Edit Expense',
        ),
        elevation: 0,
      ),
      body: expenseProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Property info
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.property.name,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              widget.property.fullAddress,
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Category
                    DropdownButtonFormField<ExpenseCategory>(
                      value: _selectedCategory,
                      decoration: const InputDecoration(
                        labelText: 'Category',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.category),
                      ),
                      items: ExpenseCategory.values
                          .map((category) => DropdownMenuItem(
                                value: category,
                                child: Text(category.displayName),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            _selectedCategory = value;
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 16),

                    // Amount
                    TextFormField(
                      controller: _amountController,
                      decoration: InputDecoration(
                        labelText: 'Amount (${widget.property.baseCurrency})',
                        border: const OutlineInputBorder(),
                        prefixIcon: const Icon(Icons.attach_money),
                      ),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter amount';
                        }
                        final amount = double.tryParse(value);
                        if (amount == null || amount <= 0) {
                          return 'Please enter valid amount';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Expense date
                    InkWell(
                      onTap: () => _selectDate(context),
                      child: InputDecorator(
                        decoration: const InputDecoration(
                          labelText: 'Expense Date',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.calendar_today),
                        ),
                        child: Text(
                          '${_expenseDate.day}/${_expenseDate.month}/${_expenseDate.year}',
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Description
                    TextFormField(
                      controller: _descriptionController,
                      decoration: const InputDecoration(
                        labelText: 'Description',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.description),
                      ),
                      maxLines: 3,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter description';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Vendor name
                    TextFormField(
                      controller: _vendorNameController,
                      decoration: const InputDecoration(
                        labelText: 'Vendor Name (Optional)',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.business),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Invoice number
                    TextFormField(
                      controller: _invoiceNumberController,
                      decoration: const InputDecoration(
                        labelText: 'Invoice Number (Optional)',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.receipt_long),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Paid by
                    TextFormField(
                      controller: _paidByController,
                      decoration: const InputDecoration(
                        labelText: 'Paid By (Optional)',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.person),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Reimbursable checkbox
                    CheckboxListTile(
                      title: const Text('Reimbursable'),
                      subtitle: const Text(
                        'Check if this expense should be reimbursed',
                      ),
                      value: _isReimbursable,
                      onChanged: (value) {
                        setState(() {
                          _isReimbursable = value ?? true;
                        });
                      },
                    ),
                    const SizedBox(height: 24),

                    // Receipt upload section
                    Text(
                      'Receipt Photo',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    if (_receiptImage != null)
                      Stack(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Image.file(
                              _receiptImage!,
                              width: double.infinity,
                              height: 200,
                              fit: BoxFit.cover,
                            ),
                          ),
                          Positioned(
                            top: 8,
                            right: 8,
                            child: IconButton(
                              icon: const Icon(
                                Icons.close,
                                color: Colors.white,
                              ),
                              onPressed: () {
                                setState(() {
                                  _receiptImage = null;
                                });
                              },
                              style: IconButton.styleFrom(
                                backgroundColor: Colors.red,
                              ),
                            ),
                          ),
                        ],
                      )
                    else
                      OutlinedButton.icon(
                        onPressed: _showImageSourceDialog,
                        icon: const Icon(Icons.camera_alt),
                        label: const Text('Add Receipt Photo'),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size(double.infinity, 50),
                        ),
                      ),
                    const SizedBox(height: 32),

                    // Submit button
                    ElevatedButton(
                      onPressed:
                          expenseProvider.isLoading ? null : _submitExpense,
                      style: ElevatedButton.styleFrom(
                        minimumSize: const Size(double.infinity, 50),
                      ),
                      child: const Text('Record Expense'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
