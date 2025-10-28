/// Tax report screen with year selector and report type options.
///
/// Implements T232 from tasks.md.
///
/// Allows property owners to generate tax reports for filing including:
/// - Annual income statements
/// - Tax-deductible expenses
/// - GST/VAT quarterly reports
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../services/api_service.dart';
import 'report_viewer_screen.dart';

/// Tax report types available for generation
enum TaxReportType {
  income('Annual Income Statement', 'Total rental income for tax filing'),
  deductions('Tax Deductions Report', 'Deductible expenses breakdown'),
  gst('GST/VAT Report', 'Quarterly GST calculations');

  const TaxReportType(this.title, this.description);
  final String title;
  final String description;
}

/// Tax report screen with year and report type selection
class TaxReportScreen extends StatefulWidget {
  const TaxReportScreen({super.key});

  @override
  State<TaxReportScreen> createState() => _TaxReportScreenState();
}

class _TaxReportScreenState extends State<TaxReportScreen> {
  int _selectedYear = DateTime.now().year;
  TaxReportType _selectedReportType = TaxReportType.income;
  int? _selectedQuarter; // For GST reports only
  bool _isLoading = false;

  // Generate list of available years (current year and 10 years back)
  List<int> get availableYears {
    final currentYear = DateTime.now().year;
    return List.generate(11, (index) => currentYear - index);
  }

  // Generate quarters for GST reports
  List<int> get quarters => [1, 2, 3, 4];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tax Reports'),
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
                    color: theme.colorScheme.primaryContainer,
                    child: Row(
                      children: [
                        Icon(
                          Icons.info_outline,
                          color: theme.colorScheme.onPrimaryContainer,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Generate tax reports for filing with your accountant or tax authority',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onPrimaryContainer,
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
                        ...TaxReportType.values.map((type) {
                          final isSelected = _selectedReportType == type;
                          return Card(
                            elevation: isSelected ? 4 : 1,
                            color: isSelected
                                ? theme.colorScheme.primaryContainer
                                : null,
                            margin: const EdgeInsets.only(bottom: 8),
                            child: InkWell(
                              onTap: () {
                                setState(() {
                                  _selectedReportType = type;
                                  if (type != TaxReportType.gst) {
                                    _selectedQuarter = null;
                                  }
                                });
                              },
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Row(
                                  children: [
                                    Radio<TaxReportType>(
                                      value: type,
                                      groupValue: _selectedReportType,
                                      onChanged: (value) {
                                        setState(() {
                                          _selectedReportType = value!;
                                          if (value != TaxReportType.gst) {
                                            _selectedQuarter = null;
                                          }
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
                                        color: theme.colorScheme.primary,
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

                  // Year selection
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Tax Year',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<int>(
                          value: _selectedYear,
                          decoration: InputDecoration(
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            prefixIcon: const Icon(Icons.calendar_today),
                          ),
                          items: availableYears
                              .map((year) => DropdownMenuItem(
                                    value: year,
                                    child: Text(year.toString()),
                                  ))
                              .toList(),
                          onChanged: (value) {
                            setState(() {
                              _selectedYear = value!;
                            });
                          },
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Quarter selection (for GST reports only)
                  if (_selectedReportType == TaxReportType.gst)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Quarter',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: quarters.map((quarter) {
                              final isSelected = _selectedQuarter == quarter;
                              return Expanded(
                                child: Padding(
                                  padding:
                                      const EdgeInsets.symmetric(horizontal: 4),
                                  child: ChoiceChip(
                                    label: Text('Q$quarter'),
                                    selected: isSelected,
                                    onSelected: (selected) {
                                      setState(() {
                                        _selectedQuarter = quarter;
                                      });
                                    },
                                  ),
                                ),
                              );
                            }).toList(),
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
                        icon: const Icon(Icons.description),
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

                  // Help text
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
                                  Icons.lightbulb_outline,
                                  size: 20,
                                  color: theme.colorScheme.onSurfaceVariant,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Report Information',
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
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
    if (_selectedReportType == TaxReportType.gst) {
      return _selectedQuarter != null;
    }
    return true;
  }

  String _getReportHelp() {
    switch (_selectedReportType) {
      case TaxReportType.income:
        return 'This report includes all rental income received during the tax year, '
            'broken down by property and payment method. Use this for annual tax filing.';
      case TaxReportType.deductions:
        return 'This report lists all tax-deductible expenses including maintenance, '
            'repairs, insurance, and administrative costs. Keep receipts for audit purposes.';
      case TaxReportType.gst:
        return 'GST/VAT report shows taxable income, output GST collected, input GST paid, '
            'and net GST payable for the selected quarter. File this with your tax authority.';
    }
  }

  Future<void> _generateReport() async {
    // Validate GST report has quarter selected
    if (_selectedReportType == TaxReportType.gst && _selectedQuarter == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a quarter for GST report'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Call API to generate tax report
      final apiService = context.read<ApiService>();
      final response = await apiService.post('/api/v1/reports/tax', data: {
        'report_type': _selectedReportType,
        'year': _selectedYear,
        'quarter': _selectedQuarter,
      });

      if (!mounted) return;

      if (response.statusCode == 200) {
        // Show success and navigate to report viewer
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Report generated successfully'),
            backgroundColor: Colors.green,
          ),
        );

        // Navigate to report viewer or download
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => ReportViewerScreen(
            reportData: response.data,
            reportTitle: 'Tax Report ${_selectedYear}',
          ),
        ));
      } else {
        throw Exception('Failed to generate report: ${response.statusCode}');
      }
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
}
