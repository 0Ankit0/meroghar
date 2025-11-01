import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Date range picker widget for analytics filtering
/// Implements T107 from tasks.md
class DateRangePicker extends StatelessWidget {
  const DateRangePicker({
    super.key,
    required this.startDate,
    required this.endDate,
    required this.onDateRangeSelected,
  });
  final DateTime? startDate;
  final DateTime? endDate;
  final Function(DateTime?, DateTime?) onDateRangeSelected;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: _buildDateButton(
                  context: context,
                  label: 'Start Date',
                  date: startDate,
                  onDateSelected: (date) {
                    onDateRangeSelected(date, endDate);
                  },
                ),
              ),
              const SizedBox(width: 12),
              const Icon(Icons.arrow_forward, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: _buildDateButton(
                  context: context,
                  label: 'End Date',
                  date: endDate,
                  onDateSelected: (date) {
                    onDateRangeSelected(startDate, date);
                  },
                ),
              ),
              IconButton(
                icon: const Icon(Icons.clear),
                tooltip: 'Clear dates',
                onPressed: () {
                  onDateRangeSelected(null, null);
                },
              ),
            ],
          ),
        ),
      );

  Widget _buildDateButton({
    required BuildContext context,
    required String label,
    required DateTime? date,
    required Function(DateTime?) onDateSelected,
  }) =>
      InkWell(
        onTap: () async {
          final selectedDate = await showDatePicker(
            context: context,
            initialDate: date ?? DateTime.now(),
            firstDate: DateTime(2020),
            lastDate: DateTime.now(),
          );
          onDateSelected(selectedDate);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                date != null
                    ? DateFormat('MMM dd, yyyy').format(date)
                    : 'Select',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      );
}

/// Quick date range selector with preset options
class QuickDateRangeSelector extends StatelessWidget {
  const QuickDateRangeSelector({
    super.key,
    required this.onDateRangeSelected,
  });
  final Function(DateTime?, DateTime?) onDateRangeSelected;

  @override
  Widget build(BuildContext context) => Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          _buildQuickButton(
            context: context,
            label: 'This Month',
            onTap: () {
              final now = DateTime.now();
              final start = DateTime(now.year, now.month);
              final end = DateTime.now();
              onDateRangeSelected(start, end);
            },
          ),
          _buildQuickButton(
            context: context,
            label: 'Last Month',
            onTap: () {
              final now = DateTime.now();
              final lastMonth = DateTime(now.year, now.month - 1);
              final start = DateTime(lastMonth.year, lastMonth.month);
              final end = DateTime(now.year, now.month, 0);
              onDateRangeSelected(start, end);
            },
          ),
          _buildQuickButton(
            context: context,
            label: 'Last 3 Months',
            onTap: () {
              final end = DateTime.now();
              final start = DateTime(end.year, end.month - 3, end.day);
              onDateRangeSelected(start, end);
            },
          ),
          _buildQuickButton(
            context: context,
            label: 'Last 6 Months',
            onTap: () {
              final end = DateTime.now();
              final start = DateTime(end.year, end.month - 6, end.day);
              onDateRangeSelected(start, end);
            },
          ),
          _buildQuickButton(
            context: context,
            label: 'This Year',
            onTap: () {
              final now = DateTime.now();
              final start = DateTime(now.year);
              final end = DateTime.now();
              onDateRangeSelected(start, end);
            },
          ),
          _buildQuickButton(
            context: context,
            label: 'Last Year',
            onTap: () {
              final now = DateTime.now();
              final start = DateTime(now.year - 1);
              final end = DateTime(now.year - 1, 12, 31);
              onDateRangeSelected(start, end);
            },
          ),
        ],
      );

  Widget _buildQuickButton({
    required BuildContext context,
    required String label,
    required VoidCallback onTap,
  }) =>
      OutlinedButton(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
        child: Text(label),
      );
}
