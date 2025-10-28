/// Tenant record creation form screen.
///
/// Implements T048 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../services/api_service.dart';

class TenantFormScreen extends StatefulWidget {
  const TenantFormScreen({
    super.key,
    required this.userId,
    required this.propertyId,
  });
  final String userId;
  final String propertyId;

  @override
  State<TenantFormScreen> createState() => _TenantFormScreenState();
}

class _TenantFormScreenState extends State<TenantFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _monthlyRentController = TextEditingController();
  final _securityDepositController = TextEditingController();
  final _electricityRateController = TextEditingController();

  DateTime _moveInDate = DateTime.now();
  bool _isLoading = false;

  @override
  void dispose() {
    _monthlyRentController.dispose();
    _securityDepositController.dispose();
    _electricityRateController.dispose();
    super.dispose();
  }

  Future<void> _selectMoveInDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _moveInDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );

    if (picked != null) {
      setState(() => _moveInDate = picked);
    }
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    try {
      final apiService = ApiService.instance;
      final response = await apiService.post(
        '/api/v1/tenants',
        data: {
          'user_id': widget.userId,
          'property_id': widget.propertyId,
          'move_in_date': DateFormat('yyyy-MM-dd').format(_moveInDate),
          'monthly_rent': double.parse(_monthlyRentController.text),
          'security_deposit': double.parse(_securityDepositController.text),
          'electricity_rate': double.parse(_electricityRateController.text),
        },
      );

      if (!mounted) return;

      if (response.isSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Tenant record created successfully'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to create tenant'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  String? _validateAmount(String? value) {
    if (value == null || value.isEmpty) {
      return 'Amount is required';
    }
    final amount = double.tryParse(value);
    if (amount == null || amount <= 0) {
      return 'Enter a valid amount';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Create Tenant Record'),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Tenancy Details',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      Card(
                        child: ListTile(
                          leading: const Icon(Icons.calendar_today),
                          title: const Text('Move-In Date'),
                          subtitle: Text(
                              DateFormat('MMM dd, yyyy').format(_moveInDate)),
                          trailing: const Icon(Icons.edit),
                          onTap: _selectMoveInDate,
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        'Financial Details',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _monthlyRentController,
                        decoration: const InputDecoration(
                          labelText: 'Monthly Rent *',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.payments),
                          suffixText: 'per month',
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        validator: _validateAmount,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _securityDepositController,
                        decoration: const InputDecoration(
                          labelText: 'Security Deposit *',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.lock),
                          suffixText: 'one-time',
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        validator: _validateAmount,
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _electricityRateController,
                        decoration: const InputDecoration(
                          labelText: 'Electricity Rate *',
                          hintText: 'Per unit charge',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.electric_bolt),
                          suffixText: 'per unit',
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        validator: _validateAmount,
                      ),
                      const SizedBox(height: 24),
                      Card(
                        color: Colors.blue.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(Icons.info_outline,
                                      color: Colors.blue.shade700),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Note',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.blue.shade700,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Make sure the tenant user account is created before creating this tenancy record.',
                                style: TextStyle(fontSize: 13),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: _handleSubmit,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: const Text('Create Tenant Record'),
                      ),
                    ],
                  ),
                ),
              ),
      );
}
