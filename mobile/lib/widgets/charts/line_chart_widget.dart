import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../models/analytics.dart';

/// Line chart widget for displaying rent collection trends
/// Implements T104 from tasks.md
class RentTrendsLineChart extends StatelessWidget {
  const RentTrendsLineChart({
    Key? key,
    required this.trends,
    this.height = 300,
  }) : super(key: key);
  final List<RentCollectionTrend> trends;
  final double height;

  @override
  Widget build(BuildContext context) {
    if (trends.isEmpty) {
      return SizedBox(
        height: height,
        child: const Center(
          child: Text('No data available'),
        ),
      );
    }

    return SizedBox(
      height: height,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: LineChart(
          LineChartData(
            gridData: FlGridData(
              show: true,
              drawVerticalLine: true,
              horizontalInterval: _calculateInterval(trends),
              getDrawingHorizontalLine: (value) => FlLine(
                color: Colors.grey.withOpacity(0.2),
                strokeWidth: 1,
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
                  reservedSize: 30,
                  interval: 1,
                  getTitlesWidget: (value, meta) {
                    final index = value.toInt();
                    if (index < 0 || index >= trends.length) {
                      return const Text('');
                    }
                    final month = trends[index].month;
                    return Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Text(
                        DateFormat('MMM').format(month),
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    );
                  },
                ),
              ),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 50,
                  interval: _calculateInterval(trends),
                  getTitlesWidget: (value, meta) => Text(
                    _formatCurrency(value),
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
            minX: 0,
            maxX: (trends.length - 1).toDouble(),
            minY: 0,
            maxY: _getMaxY(trends),
            lineBarsData: [
              // Total collected line
              LineChartBarData(
                spots: trends
                    .asMap()
                    .entries
                    .map((entry) => FlSpot(
                          entry.key.toDouble(),
                          entry.value.totalCollected,
                        ))
                    .toList(),
                isCurved: true,
                color: Colors.blue,
                barWidth: 3,
                isStrokeCapRound: true,
                dotData: const FlDotData(show: true),
                belowBarData: BarAreaData(
                  show: true,
                  color: Colors.blue.withOpacity(0.1),
                ),
              ),
              // Completed amount line
              LineChartBarData(
                spots: trends
                    .asMap()
                    .entries
                    .map((entry) => FlSpot(
                          entry.key.toDouble(),
                          entry.value.completedAmount,
                        ))
                    .toList(),
                isCurved: true,
                color: Colors.green,
                barWidth: 2,
                isStrokeCapRound: true,
                dotData: const FlDotData(show: false),
              ),
              // Pending amount line
              LineChartBarData(
                spots: trends
                    .asMap()
                    .entries
                    .map((entry) => FlSpot(
                          entry.key.toDouble(),
                          entry.value.pendingAmount,
                        ))
                    .toList(),
                isCurved: true,
                color: Colors.orange,
                barWidth: 2,
                isStrokeCapRound: true,
                dotData: const FlDotData(show: false),
              ),
            ],
            lineTouchData: LineTouchData(
              enabled: true,
              touchTooltipData: LineTouchTooltipData(
                getTooltipItems: (touchedSpots) =>
                    touchedSpots.map((LineBarSpot touchedSpot) {
                  final index = touchedSpot.x.toInt();
                  if (index < 0 || index >= trends.length) {
                    return null;
                  }
                  final trend = trends[index];
                  final month = DateFormat('MMM yyyy').format(trend.month);

                  String label;
                  Color color;
                  if (touchedSpot.barIndex == 0) {
                    label = 'Total: ${_formatCurrency(touchedSpot.y)}';
                    color = Colors.blue;
                  } else if (touchedSpot.barIndex == 1) {
                    label = 'Completed: ${_formatCurrency(touchedSpot.y)}';
                    color = Colors.green;
                  } else {
                    label = 'Pending: ${_formatCurrency(touchedSpot.y)}';
                    color = Colors.orange;
                  }

                  return LineTooltipItem(
                    '$month\n$label',
                    TextStyle(
                      color: color,
                      fontWeight: FontWeight.bold,
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
        ),
      ),
    );
  }

  double _getMaxY(List<RentCollectionTrend> trends) {
    double max = 0;
    for (final trend in trends) {
      if (trend.totalCollected > max) {
        max = trend.totalCollected;
      }
    }
    return max * 1.2; // Add 20% padding
  }

  double _calculateInterval(List<RentCollectionTrend> trends) {
    final maxY = _getMaxY(trends);
    return maxY / 5; // 5 intervals
  }

  String _formatCurrency(double value) {
    if (value >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(1)}M';
    } else if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}K';
    }
    return value.toStringAsFixed(0);
  }
}
