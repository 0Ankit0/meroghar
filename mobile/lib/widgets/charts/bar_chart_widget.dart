import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../models/analytics.dart';

/// Bar chart widget for displaying revenue vs expenses comparison
/// Implements T106 from tasks.md
class RevenueExpensesBarChart extends StatelessWidget {
  const RevenueExpensesBarChart({
    Key? key,
    required this.comparison,
    this.height = 300,
  }) : super(key: key);
  final RevenueExpensesComparison? comparison;
  final double height;

  @override
  Widget build(BuildContext context) {
    if (comparison == null) {
      return SizedBox(
        height: height,
        child: const Center(
          child: Text('No data available'),
        ),
      );
    }

    final revenueAmount = comparison!.revenue.total;
    final expensesAmount = comparison!.expenses.total;
    final maxValue =
        [revenueAmount, expensesAmount].reduce((a, b) => a > b ? a : b);

    return SizedBox(
      height: height,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: maxValue * 1.2,
                  barTouchData: BarTouchData(
                    enabled: true,
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        String label;
                        if (group.x == 0) {
                          label = 'Revenue\n${_formatCurrency(rod.toY)}';
                        } else {
                          label = 'Expenses\n${_formatCurrency(rod.toY)}';
                        }
                        return BarTooltipItem(
                          label,
                          const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        );
                      },
                    ),
                  ),
                  titlesData: FlTitlesData(
                    show: true,
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          switch (value.toInt()) {
                            case 0:
                              return const Padding(
                                padding: EdgeInsets.only(top: 8.0),
                                child: Text(
                                  'Revenue',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              );
                            case 1:
                              return const Padding(
                                padding: EdgeInsets.only(top: 8.0),
                                child: Text(
                                  'Expenses',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              );
                            default:
                              return const Text('');
                          }
                        },
                        reservedSize: 38,
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 50,
                        interval: maxValue / 5,
                        getTitlesWidget: (value, meta) => Text(
                          _formatCurrencyShort(value),
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ),
                  borderData: FlBorderData(
                    show: true,
                    border: Border.all(color: Colors.grey.withOpacity(0.3)),
                  ),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: maxValue / 5,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: Colors.grey.withOpacity(0.2),
                      strokeWidth: 1,
                    ),
                  ),
                  barGroups: [
                    BarChartGroupData(
                      x: 0,
                      barRods: [
                        BarChartRodData(
                          toY: revenueAmount,
                          color: Colors.green,
                          width: 40,
                          borderRadius: const BorderRadius.only(
                            topLeft: Radius.circular(6),
                            topRight: Radius.circular(6),
                          ),
                        ),
                      ],
                    ),
                    BarChartGroupData(
                      x: 1,
                      barRods: [
                        BarChartRodData(
                          toY: expensesAmount,
                          color: Colors.red,
                          width: 40,
                          borderRadius: const BorderRadius.only(
                            topLeft: Radius.circular(6),
                            topRight: Radius.circular(6),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            _buildSummary(),
          ],
        ),
      ),
    );
  }

  Widget _buildSummary() {
    final netProfit = comparison!.netProfit;
    final profitMargin = comparison!.profitMargin;
    final isProfitable = netProfit >= 0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _buildSummaryItem(
              'Net Profit',
              _formatCurrency(netProfit.abs()),
              isProfitable ? Colors.green : Colors.red,
              isProfitable ? Icons.trending_up : Icons.trending_down,
            ),
            _buildSummaryItem(
              'Margin',
              '${profitMargin.toStringAsFixed(1)}%',
              isProfitable ? Colors.green : Colors.red,
              isProfitable ? Icons.check_circle : Icons.warning,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(
          String label, String value, Color color, IconData icon) =>
      Column(
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 16),
              const SizedBox(width: 4),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      );

  String _formatCurrency(double value) {
    final formatter = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return formatter.format(value);
  }

  String _formatCurrencyShort(double value) {
    if (value >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}K';
    }
    return value.toStringAsFixed(0);
  }
}
