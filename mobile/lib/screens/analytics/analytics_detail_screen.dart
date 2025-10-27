import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Analytics detail drill-down screen
/// Implements T108 from tasks.md
class AnalyticsDetailScreen extends StatelessWidget {
  final String reportType;
  final String? propertyId;
  final DateTime? startDate;
  final DateTime? endDate;

  const AnalyticsDetailScreen({
    Key? key,
    required this.reportType,
    this.propertyId,
    this.startDate,
    this.endDate,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_getTitle()),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDateRangeInfo(),
            const SizedBox(height: 16),
            const Expanded(
              child: Center(
                child: Text(
                  'Detailed view will be populated with specific data based on report type',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getTitle() {
    switch (reportType) {
      case 'rent-trends':
        return 'Rent Collection Details';
      case 'payment-status':
        return 'Payment Status Details';
      case 'expense-breakdown':
        return 'Expense Details';
      case 'revenue-expenses':
        return 'Revenue & Expenses Details';
      case 'property-performance':
        return 'Property Performance Details';
      default:
        return 'Analytics Details';
    }
  }

  Widget _buildDateRangeInfo() {
    if (startDate == null || endDate == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(12.0),
          child: Text('Date range: All time'),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          children: [
            const Icon(Icons.calendar_today, size: 16),
            const SizedBox(width: 8),
            Text(
              '${DateFormat('MMM dd, yyyy').format(startDate!)} - ${DateFormat('MMM dd, yyyy').format(endDate!)}',
            ),
          ],
        ),
      ),
    );
  }
}
