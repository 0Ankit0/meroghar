import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/analytics_provider.dart';
import '../../widgets/date_range_picker.dart';
import '../../widgets/charts/line_chart_widget.dart';
import '../../widgets/charts/pie_chart_widget.dart';
import '../../widgets/charts/bar_chart_widget.dart';
import 'analytics_detail_screen.dart';

/// Analytics dashboard screen with multiple chart widgets
/// Implements T103 from tasks.md
class AnalyticsDashboardScreen extends StatefulWidget {
  const AnalyticsDashboardScreen({Key? key}) : super(key: key);

  @override
  State<AnalyticsDashboardScreen> createState() =>
      _AnalyticsDashboardScreenState();
}

class _AnalyticsDashboardScreenState extends State<AnalyticsDashboardScreen> {
  DateTime? _startDate;
  DateTime? _endDate;
  String? _selectedPropertyId;

  @override
  void initState() {
    super.initState();
    // Default to last 6 months
    _endDate = DateTime.now();
    _startDate = DateTime(_endDate!.year, _endDate!.month - 6, _endDate!.day);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadAnalytics();
    });
  }

  Future<void> _loadAnalytics() async {
    final analyticsProvider = context.read<AnalyticsProvider>();
    await analyticsProvider.fetchAllAnalytics(
      propertyId: _selectedPropertyId,
      startDate: _startDate,
      endDate: _endDate,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analytics Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.download),
            tooltip: 'Export',
            onPressed: () => _showExportDialog(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadAnalytics,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildPropertySelector(),
              const SizedBox(height: 16),
              DateRangePicker(
                startDate: _startDate,
                endDate: _endDate,
                onDateRangeSelected: (start, end) {
                  setState(() {
                    _startDate = start;
                    _endDate = end;
                  });
                  _loadAnalytics();
                },
              ),
              const SizedBox(height: 8),
              QuickDateRangeSelector(
                onDateRangeSelected: (start, end) {
                  setState(() {
                    _startDate = start;
                    _endDate = end;
                  });
                  _loadAnalytics();
                },
              ),
              const SizedBox(height: 24),
              Consumer<AnalyticsProvider>(
                builder: (context, provider, child) {
                  if (provider.isLoading) {
                    return const Center(
                      child: Padding(
                        padding: EdgeInsets.all(32.0),
                        child: CircularProgressIndicator(),
                      ),
                    );
                  }

                  if (provider.error != null) {
                    return Center(
                      child: Column(
                        children: [
                          Text(
                            'Error: ${provider.error}',
                            style: const TextStyle(color: Colors.red),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: _loadAnalytics,
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    );
                  }

                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSectionHeader(
                        'Rent Collection Trends',
                        () => _navigateToDetail('rent-trends'),
                      ),
                      RentTrendsLineChart(trends: provider.rentTrends),
                      const SizedBox(height: 32),
                      _buildSectionHeader(
                        'Payment Status',
                        () => _navigateToDetail('payment-status'),
                      ),
                      _buildPaymentStatusCard(provider),
                      const SizedBox(height: 32),
                      _buildSectionHeader(
                        'Expense Breakdown',
                        () => _navigateToDetail('expense-breakdown'),
                      ),
                      ExpenseBreakdownPieChart(
                          expenses: provider.expenseBreakdown),
                      const SizedBox(height: 32),
                      _buildSectionHeader(
                        'Revenue vs Expenses',
                        () => _navigateToDetail('revenue-expenses'),
                      ),
                      RevenueExpensesBarChart(
                          comparison: provider.revenueExpenses),
                      const SizedBox(height: 32),
                      if (_selectedPropertyId == null) ...[
                        _buildSectionHeader(
                          'Property Performance',
                          () => _navigateToDetail('property-performance'),
                        ),
                        _buildPropertyPerformanceList(provider),
                      ],
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPropertySelector() {
    // TODO: Implement property selector when PropertyProvider is available
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Property Filter',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String?>(
              value: _selectedPropertyId,
              decoration: const InputDecoration(
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                border: OutlineInputBorder(),
              ),
              hint: const Text('All Properties'),
              items: const [
                DropdownMenuItem<String?>(
                  value: null,
                  child: Text('All Properties'),
                ),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedPropertyId = value;
                });
                _loadAnalytics();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, VoidCallback onViewDetails) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          TextButton.icon(
            onPressed: onViewDetails,
            icon: const Icon(Icons.arrow_forward, size: 16),
            label: const Text('Details'),
          ),
        ],
      ),
    );
  }

  Widget _buildPaymentStatusCard(AnalyticsProvider provider) {
    final status = provider.paymentStatus;
    if (status == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text('No payment status data'),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            _buildStatusRow(
              'Completed',
              status.completed.count,
              status.completed.amount,
              Colors.green,
            ),
            const Divider(),
            _buildStatusRow(
              'Pending',
              status.pending.count,
              status.pending.amount,
              Colors.orange,
            ),
            const Divider(),
            _buildStatusRow(
              'Failed',
              status.failed.count,
              status.failed.amount,
              Colors.red,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusRow(String label, int count, double amount, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ],
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '\$${amount.toStringAsFixed(0)}',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              '$count payments',
              style: const TextStyle(
                fontSize: 12,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPropertyPerformanceList(AnalyticsProvider provider) {
    final properties = provider.propertyPerformance;

    if (properties.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text('No property performance data'),
        ),
      );
    }

    return Column(
      children: properties.map((property) {
        final isProfitable = property.netProfit >= 0;

        return Card(
          child: ListTile(
            title: Text(property.propertyName),
            subtitle: Text('${property.tenantCount} tenants'),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '\$${property.netProfit.toStringAsFixed(0)}',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: isProfitable ? Colors.green : Colors.red,
                  ),
                ),
                Text(
                  isProfitable ? 'Profit' : 'Loss',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
            onTap: () {
              setState(() {
                _selectedPropertyId = property.propertyId;
              });
              _loadAnalytics();
            },
          ),
        );
      }).toList(),
    );
  }

  void _navigateToDetail(String reportType) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AnalyticsDetailScreen(
          reportType: reportType,
          propertyId: _selectedPropertyId,
          startDate: _startDate,
          endDate: _endDate,
        ),
      ),
    );
  }

  void _showExportDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Export Analytics'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.table_chart),
              title: const Text('Export as Excel'),
              onTap: () {
                Navigator.pop(context);
                _exportAnalytics('excel');
              },
            ),
            ListTile(
              leading: const Icon(Icons.picture_as_pdf),
              title: const Text('Export as PDF'),
              onTap: () {
                Navigator.pop(context);
                _exportAnalytics('pdf');
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _exportAnalytics(String format) async {
    final provider = context.read<AnalyticsProvider>();

    final result = await provider.exportAnalytics(
      reportType: 'revenue-expenses',
      format: format,
      propertyId: _selectedPropertyId,
      startDate: _startDate,
      endDate: _endDate,
    );

    if (!mounted) return;

    if (result != null && result['success'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Analytics exported as $format (${result['message']})'),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to export analytics'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
