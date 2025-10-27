/// Bill creation screen.
///
/// Implements T089 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/bill.dart';
import '../../providers/bill_provider.dart';

class BillCreateScreen extends StatefulWidget {
  final String propertyId;

  const BillCreateScreen({super.key, required this.propertyId});

  @override
  State<BillCreateScreen> createState() => _BillCreateScreenState();
}

class _BillCreateScreenState extends State<BillCreateScreen> {
  final _formKey = GlobalKey<FormState>();

  BillType _billType = BillType.electricity;
  AllocationMethod _allocationMethod = AllocationMethod.equal;
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _billNumberController = TextEditingController();

  DateTime _periodStart = DateTime.now();
  DateTime _periodEnd = DateTime.now().add(const Duration(days: 30));
  DateTime _dueDate = DateTime.now().add(const Duration(days: 40));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Bill')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            DropdownButtonFormField<BillType>(
              value: _billType,
              decoration: const InputDecoration(labelText: 'Bill Type'),
              items: BillType.values.map((type) {
                return DropdownMenuItem(
                  value: type,
                  child: Text(type.displayName),
                );
              }).toList(),
              onChanged: (value) => setState(() => _billType = value!),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _amountController,
              decoration: const InputDecoration(
                labelText: 'Total Amount',
                prefixText: '₹ ',
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter amount';
                }
                if (double.tryParse(value) == null) {
                  return 'Please enter valid number';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<AllocationMethod>(
              value: _allocationMethod,
              decoration: const InputDecoration(labelText: 'Allocation Method'),
              items: AllocationMethod.values.map((method) {
                return DropdownMenuItem(
                  value: method,
                  child: Text(method.displayName),
                );
              }).toList(),
              onChanged: (value) => setState(() => _allocationMethod = value!),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _billNumberController,
              decoration:
                  const InputDecoration(labelText: 'Bill Number (Optional)'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _descriptionController,
              decoration:
                  const InputDecoration(labelText: 'Description (Optional)'),
              maxLines: 3,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _createBill,
              child: const Text('Create Bill'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _createBill() async {
    if (!_formKey.currentState!.validate()) return;

    final provider = context.read<BillProvider>();
    final bill = await provider.createBill(
      propertyId: widget.propertyId,
      billType: _billType,
      totalAmount: double.parse(_amountController.text),
      periodStart: _periodStart,
      periodEnd: _periodEnd,
      dueDate: _dueDate,
      allocationMethod: _allocationMethod,
      description: _descriptionController.text.isEmpty
          ? null
          : _descriptionController.text,
      billNumber: _billNumberController.text.isEmpty
          ? null
          : _billNumberController.text,
    );

    if (bill != null && mounted) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Bill created successfully')),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(provider.error ?? 'Failed to create bill')),
      );
    }
  }

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    _billNumberController.dispose();
    super.dispose();
  }
}
