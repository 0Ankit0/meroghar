import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../models/analytics.dart';

/// Pie chart widget for displaying expense breakdown by bill type
/// Implements T105 from tasks.md
class ExpenseBreakdownPieChart extends StatefulWidget {
  final List<ExpenseBreakdown> expenses;
  final double size;

  const ExpenseBreakdownPieChart({
    Key? key,
    required this.expenses,
    this.size = 250,
  }) : super(key: key);

  @override
  State<ExpenseBreakdownPieChart> createState() =>
      _ExpenseBreakdownPieChartState();
}

class _ExpenseBreakdownPieChartState extends State<ExpenseBreakdownPieChart> {
  int touchedIndex = -1;

  @override
  Widget build(BuildContext context) {
    if (widget.expenses.isEmpty) {
      return SizedBox(
        height: widget.size,
        child: const Center(
          child: Text('No expense data available'),
        ),
      );
    }

    return Column(
      children: [
        SizedBox(
          height: widget.size,
          child: PieChart(
            PieChartData(
              pieTouchData: PieTouchData(
                touchCallback: (FlTouchEvent event, pieTouchResponse) {
                  setState(() {
                    if (!event.isInterestedForInteractions ||
                        pieTouchResponse == null ||
                        pieTouchResponse.touchedSection == null) {
                      touchedIndex = -1;
                      return;
                    }
                    touchedIndex =
                        pieTouchResponse.touchedSection!.touchedSectionIndex;
                  });
                },
              ),
              borderData: FlBorderData(show: false),
              sectionsSpace: 2,
              centerSpaceRadius: 40,
              sections: _getSections(),
            ),
          ),
        ),
        const SizedBox(height: 16),
        _buildLegend(),
      ],
    );
  }

  List<PieChartSectionData> _getSections() {
    return widget.expenses.asMap().entries.map((entry) {
      final index = entry.key;
      final expense = entry.value;
      final isTouched = index == touchedIndex;
      final fontSize = isTouched ? 16.0 : 12.0;
      final radius = isTouched ? 80.0 : 70.0;

      return PieChartSectionData(
        color: _getColor(index),
        value: expense.totalAmount,
        title: '${expense.percentage.toStringAsFixed(1)}%',
        radius: radius,
        titleStyle: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      );
    }).toList();
  }

  Widget _buildLegend() {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      alignment: WrapAlignment.center,
      children: widget.expenses.asMap().entries.map((entry) {
        final index = entry.key;
        final expense = entry.value;
        final color = _getColor(index);

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 16,
              height: 16,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 4),
            Text(
              '${_formatBillType(expense.billType)} (${_formatCurrency(expense.totalAmount)})',
              style: const TextStyle(fontSize: 12),
            ),
          ],
        );
      }).toList(),
    );
  }

  Color _getColor(int index) {
    final colors = [
      Colors.blue,
      Colors.green,
      Colors.orange,
      Colors.purple,
      Colors.red,
      Colors.teal,
      Colors.amber,
      Colors.indigo,
    ];
    return colors[index % colors.length];
  }

  String _formatBillType(String type) {
    return type.split('_').map((word) {
      return word[0].toUpperCase() + word.substring(1).toLowerCase();
    }).join(' ');
  }

  String _formatCurrency(double value) {
    final formatter = NumberFormat.currency(symbol: '\$', decimalDigits: 0);
    return formatter.format(value);
  }
}
