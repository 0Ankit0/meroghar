/// Rent policy configuration screen for automatic rent increments.
///
/// Implements T200 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../models/tenant.dart';
import '../../services/api_service.dart';

class RentPolicyScreen extends StatefulWidget {
  const RentPolicyScreen({
    super.key,
    required this.tenant,
  });
  final Tenant tenant;

  @override
  State<RentPolicyScreen> createState() => _RentPolicyScreenState();
}

class _RentPolicyScreenState extends State<RentPolicyScreen> {
  final _formKey = GlobalKey<FormState>();
  final _incrementValueController = TextEditingController();
  final _intervalYearsController = TextEditingController();

  String _incrementType = 'percentage';
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadCurrentPolicy();
  }

  @override
  void dispose() {
    _incrementValueController.dispose();
    _intervalYearsController.dispose();
    super.dispose();
  }

  Future<void> _loadCurrentPolicy() async {
    // Check if tenant already has a policy
    // This would be part of the tenant data from the API
    // For now, policy is loaded from tenant data
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    try {
      final apiService = ApiService.instance;
      final response = await apiService.put(
        '/api/v1/tenants/${widget.tenant.id}/rent-policy',
        queryParameters: {
          'increment_type': _incrementType,
          'increment_value': double.parse(_incrementValueController.text),
          'interval_years': int.parse(_intervalYearsController.text),
        },
      );

      if (!mounted) return;

      if (response.isSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Rent policy saved successfully'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to save rent policy'),
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

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Rent Increment Policy'),
          elevation: 0,
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Info Card
                      Card(
                        color: Colors.blue.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            children: [
                              Icon(
                                Icons.info_outline,
                                color: Colors.blue.shade700,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Set up automatic rent increments for this tenant. The system will calculate and apply increases on the anniversary date.',
                                  style: TextStyle(
                                    color: Colors.blue.shade900,
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Tenant Info
                      Text(
                        'Tenant Information',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 12),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _buildInfoRow(
                                'Current Rent',
                                '\$${widget.tenant.monthlyRent.toStringAsFixed(2)}',
                              ),
                              const SizedBox(height: 8),
                              _buildInfoRow(
                                'Move-in Date',
                                _formatDate(widget.tenant.moveInDate),
                              ),
                              const SizedBox(height: 8),
                              _buildInfoRow(
                                'Months Stayed',
                                '${widget.tenant.monthsStayed} months',
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Increment Type Selection
                      Text(
                        'Increment Type',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      Card(
                        child: Column(
                          children: [
                            RadioListTile<String>(
                              title: const Text('Percentage'),
                              subtitle: const Text(
                                  'Increase by a percentage (e.g., 5%)'),
                              value: 'percentage',
                              groupValue: _incrementType,
                              onChanged: (value) {
                                setState(() => _incrementType = value!);
                                _incrementValueController.clear();
                              },
                            ),
                            const Divider(height: 1),
                            RadioListTile<String>(
                              title: const Text('Fixed Amount'),
                              subtitle:
                                  const Text('Increase by a fixed amount'),
                              value: 'fixed',
                              groupValue: _incrementType,
                              onChanged: (value) {
                                setState(() => _incrementType = value!);
                                _incrementValueController.clear();
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Increment Value
                      TextFormField(
                        controller: _incrementValueController,
                        decoration: InputDecoration(
                          labelText: _incrementType == 'percentage'
                              ? 'Increment Percentage'
                              : 'Increment Amount',
                          hintText: _incrementType == 'percentage'
                              ? 'e.g., 5 for 5%'
                              : 'e.g., 100',
                          prefixText:
                              _incrementType == 'percentage' ? '' : '\$ ',
                          suffixText: _incrementType == 'percentage' ? '%' : '',
                          border: const OutlineInputBorder(),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        inputFormatters: [
                          FilteringTextInputFormatter.allow(
                              RegExp(r'^\d+\.?\d{0,2}')),
                        ],
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter increment value';
                          }
                          final numValue = double.tryParse(value);
                          if (numValue == null || numValue <= 0) {
                            return 'Please enter a valid positive number';
                          }
                          if (_incrementType == 'percentage' &&
                              numValue > 100) {
                            return 'Percentage cannot exceed 100%';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      // Interval Years
                      TextFormField(
                        controller: _intervalYearsController,
                        decoration: const InputDecoration(
                          labelText: 'Increment Interval (Years)',
                          hintText: 'e.g., 2 for every 2 years',
                          suffixText: 'years',
                          border: OutlineInputBorder(),
                          helperText: 'How often should the rent increase?',
                        ),
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly,
                        ],
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter interval years';
                          }
                          final numValue = int.tryParse(value);
                          if (numValue == null || numValue <= 0) {
                            return 'Please enter a valid positive number';
                          }
                          if (numValue > 10) {
                            return 'Interval cannot exceed 10 years';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 24),

                      // Preview Card
                      if (_incrementValueController.text.isNotEmpty &&
                          _intervalYearsController.text.isNotEmpty)
                        Card(
                          color: Colors.green.shade50,
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Icon(
                                      Icons.preview,
                                      color: Colors.green.shade700,
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      'Preview',
                                      style: TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.green.shade900,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  _getPreviewText(),
                                  style: TextStyle(
                                    color: Colors.green.shade900,
                                    fontSize: 14,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      const SizedBox(height: 24),

                      // Submit Button
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _handleSubmit,
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text(
                                  'Save Rent Policy',
                                  style: TextStyle(fontSize: 16),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
      );

  Widget _buildInfoRow(String label, String value) => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 14,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ],
      );

  String _formatDate(DateTime date) => '${date.day}/${date.month}/${date.year}';

  String _getPreviewText() {
    final incrementValue = double.tryParse(_incrementValueController.text) ?? 0;
    final intervalYears = int.tryParse(_intervalYearsController.text) ?? 0;

    if (incrementValue == 0 || intervalYears == 0) {
      return '';
    }

    final currentRent = widget.tenant.monthlyRent;
    double newRent;

    if (_incrementType == 'percentage') {
      newRent = currentRent * (1 + incrementValue / 100);
    } else {
      newRent = currentRent + incrementValue;
    }

    final nextIncrementDate = widget.tenant.moveInDate.add(
      Duration(days: 365 * intervalYears),
    );

    return 'Every $intervalYears year(s), the rent will increase from '
        '\$${currentRent.toStringAsFixed(2)} to \$${newRent.toStringAsFixed(2)}. '
        'Next increment scheduled: ${_formatDate(nextIncrementDate)}.';
  }
}
