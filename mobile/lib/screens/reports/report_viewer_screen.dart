import 'package:flutter/material.dart';

/// Screen to view generated report data
class ReportViewerScreen extends StatelessWidget {
  const ReportViewerScreen({
    super.key,
    required this.reportData,
    required this.reportTitle,
  });
  final Map<String, dynamic> reportData;
  final String reportTitle;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Text(reportTitle),
          actions: [
            IconButton(
              icon: const Icon(Icons.download),
              onPressed: () {
                // Download functionality
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Download functionality coming soon'),
                  ),
                );
              },
            ),
            IconButton(
              icon: const Icon(Icons.share),
              onPressed: () {
                // Share functionality
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Share functionality coming soon'),
                  ),
                );
              },
            ),
          ],
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Report summary
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Report Summary',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      _buildReportData(context),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      );

  Widget _buildReportData(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: reportData.entries
            .map((entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _formatKey(entry.key),
                        style: const TextStyle(fontWeight: FontWeight.w500),
                      ),
                      Text(_formatValue(entry.value)),
                    ],
                  ),
                ))
            .toList(),
      );

  String _formatKey(String key) => key
      .replaceAll('_', ' ')
      .split(' ')
      .map((word) =>
          word.isNotEmpty ? '${word[0].toUpperCase()}${word.substring(1)}' : '')
      .join(' ');

  String _formatValue(dynamic value) {
    if (value is num) {
      return value.toStringAsFixed(2);
    }
    return value.toString();
  }
}
