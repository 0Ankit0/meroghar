/// Financial report screen with report type selector and date range.
///
/// Implements T233 from tasks.md.
///
/// Allows property owners to generate financial reports including:
/// - Profit & Loss statements
/// - Cash flow analysis
/// - Balance sheets
library;

import 'package:flutter/material.dart';

/// Financial report types available for generation
enum FinancialReportType {
  profitLoss('Profit & Loss Statement', 'Revenue, expenses, and net profit'),
  cashFlow('Cash Flow Statement', 'Cash inflows and outflows'),
  balanceSheet('Balance Sheet', 'Assets, liabilities, and equity');

  const FinancialReportType(this.title, this.description);
  final String title;
  final String description;
}

/// Period options for financial reports
enum ReportPeriod {
  month('This Month'),
  quarter('This Quarter'),
  year('This Year'),
  custom('Custom Range');

  const ReportPeriod(this.label);
  final String label;
}

/// Financial report screen with type and period selection
class FinancialReportScreen extends StatefulWidget {
  const FinancialReportScreen({super.key});

  @override
  State<FinancialReportScreen> createState() => _FinancialReportScreenState();
}

class _FinancialReportScreenState extends State<FinancialReportScreen> {
  FinancialReportType _selectedReportType = FinancialReportType.profitLoss;
  ReportPeriod _selectedPeriod = ReportPeriod.month;
  DateTime? _customStartDate;
  DateTime? _customEndDate;
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Financial Reports'),
        elevation: 0,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Info banner
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    color: theme.colorScheme.secondaryContainer,
                    child: Row(
                      children: [
                        Icon(
                          Icons.analytics_outlined,
                          color: theme.colorScheme.onSecondaryContainer,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Analyze your rental property financial performance',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSecondaryContainer,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Report type selection
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Report Type',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        ...FinancialReportType.values.map((type) {
                          final isSelected = _selectedReportType == type;
                          return Card(
                            elevation: isSelected ? 4 : 1,
                            color: isSelected
                                ? theme.colorScheme.secondaryContainer
                                : null,
                            margin: const EdgeInsets.only(bottom: 8),
                            child: InkWell(
                              onTap: () {
                                setState(() {
                                  _selectedReportType = type;
                                });
                              },
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Row(
                                  children: [
                                    Radio<FinancialReportType>(
                                      value: type,
                                      groupValue: _selectedReportType,
                                      onChanged: (value) {
                                        setState(() {
                                          _selectedReportType = value!;
                                        });
                                      },
                                    ),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            type.title,
                                            style: theme.textTheme.titleSmall
                                                ?.copyWith(
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            type.description,
                                            style: theme.textTheme.bodySmall,
                                          ),
                                        ],
                                      ),
                                    ),
                                    if (isSelected)
                                      Icon(
                                        Icons.check_circle,
                                        color: theme.colorScheme.secondary,
                                      ),
                                  ],
                                ),
                              ),
                            ),
                          );
                        }),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Period selection
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Period',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: ReportPeriod.values.map((period) {
                            final isSelected = _selectedPeriod == period;
                            return ChoiceChip(
                              label: Text(period.label),
                              selected: isSelected,
                              onSelected: (selected) {
                                setState(() {
                                  _selectedPeriod = period;
                                  if (period != ReportPeriod.custom) {
                                    _customStartDate = null;
                                    _customEndDate = null;
                                  }
                                });
                              },
                            );
                          }).toList(),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Custom date range (if custom period selected)
                  if (_selectedPeriod == ReportPeriod.custom)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Custom Date Range',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: () => _selectDate(context, true),
                                  icon: const Icon(Icons.calendar_today),
                                  label: Text(
                                    _customStartDate != null
                                        ? _formatDate(_customStartDate!)
                                        : 'Start Date',
                                  ),
                                  style: OutlinedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(
                                        vertical: 16),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              const Icon(Icons.arrow_forward),
                              const SizedBox(width: 12),
                              Expanded(
                                child: OutlinedButton.icon(
                                  onPressed: () => _selectDate(context, false),
                                  icon: const Icon(Icons.calendar_today),
                                  label: Text(
                                    _customEndDate != null
                                        ? _formatDate(_customEndDate!)
                                        : 'End Date',
                                  ),
                                  style: OutlinedButton.styleFrom(
                                    padding: const EdgeInsets.symmetric(
                                        vertical: 16),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                  const SizedBox(height: 32),

                  // Generate button
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton.icon(
                        onPressed:
                            _canGenerateReport() ? _generateReport : null,
                        icon: const Icon(Icons.assessment),
                        label: const Text('Generate Report'),
                        style: ElevatedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Summary card showing date range
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Card(
                      color: theme.colorScheme.surfaceVariant,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.date_range,
                                  size: 20,
                                  color: theme.colorScheme.onSurfaceVariant,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Report Period',
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              _getDateRangeText(),
                              style: theme.textTheme.bodyMedium?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                            const Divider(height: 24),
                            Text(
                              _getReportHelp(),
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),
                ],
              ),
            ),
    );
  }

  bool _canGenerateReport() {
    if (_selectedPeriod == ReportPeriod.custom) {
      return _customStartDate != null && _customEndDate != null;
    }
    return true;
  }

  String _getDateRangeText() {
    final now = DateTime.now();
    switch (_selectedPeriod) {
      case ReportPeriod.month:
        return '${_formatMonthYear(now)} (current month)';
      case ReportPeriod.quarter:
        final quarter = (now.month - 1) ~/ 3 + 1;
        return 'Q$quarter ${now.year} (current quarter)';
      case ReportPeriod.year:
        return '${now.year} (current year)';
      case ReportPeriod.custom:
        if (_customStartDate != null && _customEndDate != null) {
          return '${_formatDate(_customStartDate!)} to ${_formatDate(_customEndDate!)}';
        }
        return 'Please select start and end dates';
    }
  }

  String _getReportHelp() {
    switch (_selectedReportType) {
      case FinancialReportType.profitLoss:
        return 'Shows total revenue from rent and utilities minus all expenses. '
            'Helps you understand profitability of your rental properties.';
      case FinancialReportType.cashFlow:
        return 'Tracks actual cash received and paid out. '
            'Essential for understanding liquidity and managing cash reserves.';
      case FinancialReportType.balanceSheet:
        return 'Snapshot of assets (properties, deposits held) and liabilities. '
            'Provides overall financial position at end of period.';
    }
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }

  String _formatMonthYear(DateTime date) {
    const months = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December'
    ];
    return '${months[date.month - 1]} ${date.year}';
  }

  Future<void> _selectDate(BuildContext context, bool isStartDate) async {
    final initialDate = isStartDate
        ? (_customStartDate ?? DateTime.now())
        : (_customEndDate ?? DateTime.now());

    final pickedDate = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(2000),
      lastDate: DateTime.now(),
    );

    if (pickedDate != null) {
      setState(() {
        if (isStartDate) {
          _customStartDate = pickedDate;
          // Reset end date if it's before start date
          if (_customEndDate != null && _customEndDate!.isBefore(pickedDate)) {
            _customEndDate = null;
          }
        } else {
          // Only allow end date after start date
          if (_customStartDate == null ||
              !pickedDate.isBefore(_customStartDate!)) {
            _customEndDate = pickedDate;
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('End date must be after start date'),
                backgroundColor: Colors.orange,
              ),
            );
          }
        }
      });
    }
  }

  Future<void> _generateReport() async {
    // Validate custom dates if custom period
    if (_selectedPeriod == ReportPeriod.custom) {
      if (_customStartDate == null || _customEndDate == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please select both start and end dates'),
            backgroundColor: Colors.orange,
          ),
        );
        return;
      }
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Calculate date range based on period
      // TODO: Use dateRange in API call below
      // final dateRange = _calculateDateRange();

      // TODO: Call API to generate report
      // final apiService = context.read<ApiService>();
      // final report = await apiService.generateFinancialReport(
      //   type: _selectedReportType,
      //   startDate: dateRange.start,
      //   endDate: dateRange.end,
      // );

      // Simulate API call
      await Future.delayed(const Duration(seconds: 2));

      if (!mounted) return;

      // Show success and navigate to report viewer
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Report generated successfully'),
          backgroundColor: Colors.green,
        ),
      );

      // TODO: Navigate to report viewer or download
      // Navigator.of(context).push(MaterialPageRoute(
      //   builder: (_) => ReportViewerScreen(report: report),
      // ));
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to generate report: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  // ignore: unused_element
  ({DateTime start, DateTime end}) _calculateDateRange() {
    final now = DateTime.now();

    switch (_selectedPeriod) {
      case ReportPeriod.month:
        // Current month
        return (
          start: DateTime(now.year, now.month, 1),
          end: DateTime(now.year, now.month + 1, 0), // Last day of month
        );

      case ReportPeriod.quarter:
        // Current quarter
        final quarter = (now.month - 1) ~/ 3 + 1;
        final startMonth = (quarter - 1) * 3 + 1;
        return (
          start: DateTime(now.year, startMonth, 1),
          end: DateTime(now.year, startMonth + 3, 0), // Last day of quarter
        );

      case ReportPeriod.year:
        // Current year
        return (
          start: DateTime(now.year, 1, 1),
          end: DateTime(now.year, 12, 31),
        );

      case ReportPeriod.custom:
        // Custom range
        return (
          start: _customStartDate ?? now,
          end: _customEndDate ?? now,
        );
    }
  }
}
