/// Payment recording form screen.
///
/// Implements T067 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/payment.dart';
import '../../models/tenant.dart';
import '../../providers/payment_provider.dart';

class PaymentFormScreen extends StatefulWidget {
  const PaymentFormScreen({
    super.key,
    required this.tenant,
    required this.propertyId,
  });
  final Tenant tenant;
  final String propertyId;

  @override
  State<PaymentFormScreen> createState() => _PaymentFormScreenState();
}

class _PaymentFormScreenState extends State<PaymentFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _transactionRefController = TextEditingController();
  final _notesController = TextEditingController();

  PaymentMethod _selectedMethod = PaymentMethod.cash;
  PaymentType _selectedType = PaymentType.rent;
  DateTime _paymentDate = DateTime.now();
  DateTime? _periodStart;
  DateTime? _periodEnd;

  @override
  void initState() {
    super.initState();
    // Pre-fill amount with monthly rent for rent payments
    if (_selectedType == PaymentType.rent) {
      _amountController.text = widget.tenant.monthlyRent.toStringAsFixed(2);
    }
  }

  @override
  void dispose() {
    _amountController.dispose();
    _transactionRefController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _selectDate(BuildContext context, bool isPaymentDate) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate:
          isPaymentDate ? _paymentDate : (_periodStart ?? DateTime.now()),
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );

    if (picked != null) {
      setState(() {
        if (isPaymentDate) {
          _paymentDate = picked;
        } else {
          _periodStart = picked;
        }
      });
    }
  }

  Future<void> _selectPeriodEnd(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _periodEnd ?? _periodStart ?? DateTime.now(),
      firstDate: _periodStart ?? DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );

    if (picked != null) {
      setState(() {
        _periodEnd = picked;
      });
    }
  }

  Future<void> _submitPayment() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final paymentProvider = context.read<PaymentProvider>();

    final payment = await paymentProvider.recordPayment(
      tenantId: widget.tenant.id,
      propertyId: widget.propertyId,
      amount: double.parse(_amountController.text),
      paymentMethod: _selectedMethod,
      paymentType: _selectedType,
      paymentDate: _paymentDate,
      paymentPeriodStart: _periodStart,
      paymentPeriodEnd: _periodEnd,
      transactionReference: _transactionRefController.text.isNotEmpty
          ? _transactionRefController.text
          : null,
      notes: _notesController.text.isNotEmpty ? _notesController.text : null,
    );

    if (!mounted) return;

    if (payment != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Payment recorded successfully'),
          backgroundColor: Colors.green,
        ),
      );
      Navigator.pop(context, payment);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            paymentProvider.error ?? 'Failed to record payment',
          ),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final paymentProvider = context.watch<PaymentProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Record Payment'),
        elevation: 0,
      ),
      body: paymentProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Tenant Info Card
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Tenant Information',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                                'Tenant ID: ${widget.tenant.id.substring(0, 8)}...'),
                            Text(
                                'Property ID: ${widget.propertyId.substring(0, 8)}...'),
                            Text(
                              'Monthly Rent: INR ${widget.tenant.monthlyRent.toStringAsFixed(2)}',
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Payment Type
                    Text(
                      'Payment Type',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<PaymentType>(
                      initialValue: _selectedType,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                      ),
                      items: PaymentType.values
                          .map((type) => DropdownMenuItem(
                                value: type,
                                child: Text(type.displayName),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            _selectedType = value;
                            // Auto-fill amount for rent
                            if (value == PaymentType.rent) {
                              _amountController.text =
                                  widget.tenant.monthlyRent.toStringAsFixed(2);
                            }
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 16),

                    // Amount
                    Text(
                      'Amount',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _amountController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        prefixText: 'INR ',
                        hintText: '0.00',
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter amount';
                        }
                        final amount = double.tryParse(value);
                        if (amount == null || amount <= 0) {
                          return 'Please enter a valid amount';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),

                    // Payment Method
                    Text(
                      'Payment Method',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<PaymentMethod>(
                      initialValue: _selectedMethod,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 8,
                        ),
                      ),
                      items: PaymentMethod.values
                          .map((method) => DropdownMenuItem(
                                value: method,
                                child: Text(method.displayName),
                              ))
                          .toList(),
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            _selectedMethod = value;
                          });
                        }
                      },
                    ),
                    const SizedBox(height: 16),

                    // Payment Date
                    Text(
                      'Payment Date',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    InkWell(
                      onTap: () => _selectDate(context, true),
                      child: InputDecorator(
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                          suffixIcon: Icon(Icons.calendar_today),
                        ),
                        child: Text(
                          '${_paymentDate.day}/${_paymentDate.month}/${_paymentDate.year}',
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Payment Period (for rent)
                    if (_selectedType == PaymentType.rent) ...[
                      Text(
                        'Payment Period (Optional)',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: InkWell(
                              onTap: () => _selectDate(context, false),
                              child: InputDecorator(
                                decoration: const InputDecoration(
                                  border: OutlineInputBorder(),
                                  labelText: 'Start Date',
                                  suffixIcon: Icon(Icons.calendar_today),
                                ),
                                child: Text(
                                  _periodStart != null
                                      ? '${_periodStart!.day}/${_periodStart!.month}/${_periodStart!.year}'
                                      : 'Select',
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: InkWell(
                              onTap: () => _selectPeriodEnd(context),
                              child: InputDecorator(
                                decoration: const InputDecoration(
                                  border: OutlineInputBorder(),
                                  labelText: 'End Date',
                                  suffixIcon: Icon(Icons.calendar_today),
                                ),
                                child: Text(
                                  _periodEnd != null
                                      ? '${_periodEnd!.day}/${_periodEnd!.month}/${_periodEnd!.year}'
                                      : 'Select',
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Transaction Reference
                    Text(
                      'Transaction Reference (Optional)',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _transactionRefController,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        hintText: 'e.g., Check #123, UPI Ref',
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Notes
                    Text(
                      'Notes (Optional)',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _notesController,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        hintText: 'Any additional information...',
                      ),
                    ),
                    const SizedBox(height: 32),

                    // Submit Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed:
                            paymentProvider.isLoading ? null : _submitPayment,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text(
                          'Record Payment',
                          style: TextStyle(fontSize: 16),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
