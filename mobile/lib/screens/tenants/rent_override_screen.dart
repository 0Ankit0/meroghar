/// Manual rent override screen for property owners.
///
/// Implements T202 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../models/tenant.dart';
import '../../services/api_service.dart';

class RentOverrideScreen extends StatefulWidget {
  const RentOverrideScreen({
    super.key,
    required this.tenant,
  });
  final Tenant tenant;

  @override
  State<RentOverrideScreen> createState() => _RentOverrideScreenState();
}

class _RentOverrideScreenState extends State<RentOverrideScreen> {
  final _formKey = GlobalKey<FormState>();
  final _newRentController = TextEditingController();
  final _reasonController = TextEditingController();

  bool _isLoading = false;

  @override
  void dispose() {
    _newRentController.dispose();
    _reasonController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    // Show confirmation dialog
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Rent Override'),
        content: Text(
          'Are you sure you want to change the rent from '
          '\$${widget.tenant.monthlyRent.toStringAsFixed(2)} to '
          '\$${_newRentController.text}?\n\n'
          'This will override any automatic rent increment policy.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
            ),
            child: const Text('Confirm Override'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isLoading = true);

    try {
      final apiService = ApiService.instance;
      final response = await apiService.post(
        '/api/v1/tenants/${widget.tenant.id}/rent-override',
        queryParameters: {
          'new_rent': double.parse(_newRentController.text),
          'reason': _reasonController.text.trim(),
        },
      );

      if (!mounted) return;

      if (response.isSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Rent overridden successfully'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop(true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response.message ?? 'Failed to override rent'),
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
          title: const Text('Override Rent'),
          elevation: 0,
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Warning Card
                Card(
                  color: Colors.orange.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: Colors.orange.shade700,
                          size: 32,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Manual Override',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                  color: Colors.orange.shade900,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'This will manually change the tenant\'s rent amount and override any automatic increment policy. Use this carefully.',
                                style: TextStyle(
                                  color: Colors.orange.shade900,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Current Rent Info
                Text(
                  'Current Information',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 12),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        _buildInfoRow(
                          'Current Monthly Rent',
                          '\$${widget.tenant.monthlyRent.toStringAsFixed(2)}',
                          isHighlighted: true,
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

                // New Rent Input
                Text(
                  'New Rent Amount',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _newRentController,
                  decoration: const InputDecoration(
                    labelText: 'New Monthly Rent',
                    hintText: 'Enter new rent amount',
                    prefixText: '\$ ',
                    border: OutlineInputBorder(),
                    helperText: 'Enter the new monthly rent for this tenant',
                  ),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(
                        RegExp(r'^\d+\.?\d{0,2}')),
                  ],
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter new rent amount';
                    }
                    final numValue = double.tryParse(value);
                    if (numValue == null || numValue <= 0) {
                      return 'Please enter a valid positive amount';
                    }
                    if (numValue == widget.tenant.monthlyRent) {
                      return 'New rent must be different from current rent';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Reason Input
                Text(
                  'Reason for Override',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _reasonController,
                  decoration: const InputDecoration(
                    labelText: 'Reason',
                    hintText:
                        'e.g., Requested by tenant, Market adjustment, etc.',
                    border: OutlineInputBorder(),
                    helperText: 'Explain why the rent is being changed',
                  ),
                  maxLines: 3,
                  maxLength: 200,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please provide a reason for the override';
                    }
                    if (value.trim().length < 10) {
                      return 'Please provide a more detailed reason (at least 10 characters)';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Comparison Preview
                if (_newRentController.text.isNotEmpty)
                  Card(
                    color: Colors.blue.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                Icons.compare_arrows,
                                color: Colors.blue.shade700,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Comparison',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue.shade900,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          _buildComparisonRow(),
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
                      backgroundColor: Colors.orange,
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
                            'Override Rent',
                            style: TextStyle(fontSize: 16),
                          ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );

  Widget _buildInfoRow(String label, String value,
          {bool isHighlighted = false}) =>
      Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: isHighlighted ? Colors.black : Colors.grey,
              fontSize: 14,
              fontWeight: isHighlighted ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: isHighlighted ? 18 : 14,
              color: isHighlighted ? Colors.blue : Colors.black,
            ),
          ),
        ],
      );

  Widget _buildComparisonRow() {
    final newRent = double.tryParse(_newRentController.text);
    if (newRent == null) return const SizedBox.shrink();

    final currentRent = widget.tenant.monthlyRent;
    final difference = newRent - currentRent;
    final percentageChange = (difference / currentRent * 100).abs();
    final isIncrease = difference > 0;

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Current Rent:',
              style: TextStyle(color: Colors.blue.shade900),
            ),
            Text(
              '\$${currentRent.toStringAsFixed(2)}',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.blue.shade900,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'New Rent:',
              style: TextStyle(color: Colors.blue.shade900),
            ),
            Text(
              '\$${newRent.toStringAsFixed(2)}',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.blue.shade900,
              ),
            ),
          ],
        ),
        const Divider(height: 24),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Change:',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.blue.shade900,
              ),
            ),
            Row(
              children: [
                Icon(
                  isIncrease ? Icons.arrow_upward : Icons.arrow_downward,
                  color: isIncrease ? Colors.green : Colors.red,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  '${isIncrease ? '+' : ''}\$${difference.abs().toStringAsFixed(2)} (${percentageChange.toStringAsFixed(1)}%)',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: isIncrease ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ],
        ),
      ],
    );
  }

  String _formatDate(DateTime date) => '${date.day}/${date.month}/${date.year}';
}
