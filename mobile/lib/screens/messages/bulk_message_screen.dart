/// Bulk message sending screen with tenant multi-select.
///
/// Implements T170 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/message.dart';
import '../../providers/message_provider.dart';
import '../../providers/tenant_provider.dart';
import '../../widgets/message_template_picker.dart';

/// Simplified tenant representation for selection
class TenantInfo {
  TenantInfo({
    required this.id,
    required this.fullName,
    required this.propertyName,
    this.unitNumber,
  });

  factory TenantInfo.fromJson(Map<String, dynamic> json) => TenantInfo(
        id: json['id'] as int,
        fullName: json['full_name'] as String,
        propertyName: json['property_name'] as String,
        unitNumber: json['unit_number'] as String?,
      );
  final int id;
  final String fullName;
  final String propertyName;
  final String? unitNumber;
}

class BulkMessageScreen extends StatefulWidget {
  const BulkMessageScreen({super.key});

  @override
  State<BulkMessageScreen> createState() => _BulkMessageScreenState();
}

class _BulkMessageScreenState extends State<BulkMessageScreen> {
  final Set<int> _selectedTenantIds = {};
  final List<TenantInfo> _tenants = [];
  bool _isLoadingTenants = false;
  String? _tenantError;

  MessageTemplate _selectedTemplate = MessageTemplate.paymentReminder;
  MessageChannel _selectedChannel = MessageChannel.sms;
  bool _isScheduled = false;
  DateTime? _scheduledDateTime;
  final TextEditingController _customContentController =
      TextEditingController();

  @override
  void initState() {
    super.initState();
    // Load tenants on init
    _loadTenants();
  }

  @override
  void dispose() {
    _customContentController.dispose();
    super.dispose();
  }

  /// Load tenants using TenantProvider
  Future<void> _loadTenants() async {
    setState(() {
      _isLoadingTenants = true;
      _tenantError = null;
    });

    try {
      final tenantProvider = context.read<TenantProvider>();
      await tenantProvider.loadTenants();

      setState(() {
        _isLoadingTenants = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingTenants = false;
        _tenantError = 'Failed to load tenants: ${e.toString()}';
      });
    }
  }

  Future<void> _selectScheduleDateTime() async {
    final now = DateTime.now();

    final date = await showDatePicker(
      context: context,
      initialDate: now.add(const Duration(hours: 1)),
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
    );

    if (date == null) return;

    if (!mounted) return;

    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(now.add(const Duration(hours: 1))),
    );

    if (time == null) return;

    setState(() {
      _scheduledDateTime = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
  }

  Future<void> _sendMessages() async {
    if (_selectedTenantIds.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select at least one tenant'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    if (_isScheduled && _scheduledDateTime == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a schedule time'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Send'),
        content: Text(
          _isScheduled
              ? 'Schedule ${_selectedTenantIds.length} messages for ${_formatDateTime(_scheduledDateTime!)}?'
              : 'Send ${_selectedTenantIds.length} messages immediately?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(_isScheduled ? 'Schedule' : 'Send'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    final messageProvider = context.read<MessageProvider>();

    final result = await messageProvider.sendBulkMessages(
      tenantIds: _selectedTenantIds.toList(),
      template: _selectedTemplate,
      channel: _selectedChannel,
      content: _selectedTemplate == MessageTemplate.custom
          ? _customContentController.text
          : null,
      scheduledAt: _isScheduled ? _scheduledDateTime : null,
    );

    if (!mounted) return;

    if (result['success'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _isScheduled
                ? '${result['successful']} messages scheduled'
                : '${result['successful']} messages sent',
          ),
          backgroundColor: Colors.green,
        ),
      );

      // Clear selection and go back
      Navigator.pop(context);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result['error'] ?? 'Failed to send messages'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  String _formatDateTime(DateTime dt) =>
      '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Send Bulk Messages'),
          actions: [
            IconButton(
              icon: const Icon(Icons.send),
              onPressed: _sendMessages,
            ),
          ],
        ),
        body: Consumer<MessageProvider>(
          builder: (context, messageProvider, child) => Column(
            children: [
              // Configuration section
              Expanded(
                flex: 2,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Template selector
                      const Text(
                        'Message Template',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      MessageTemplatePicker(
                        selectedTemplate: _selectedTemplate,
                        onTemplateSelected: (template) {
                          setState(() {
                            _selectedTemplate = template;
                          });
                        },
                      ),
                      const SizedBox(height: 16),

                      // Custom content for custom template
                      if (_selectedTemplate == MessageTemplate.custom) ...[
                        TextField(
                          controller: _customContentController,
                          decoration: const InputDecoration(
                            labelText: 'Custom Message Content',
                            hintText: 'Enter your custom message...',
                            border: OutlineInputBorder(),
                          ),
                          maxLines: 3,
                          maxLength: 1000,
                        ),
                        const SizedBox(height: 16),
                      ],

                      // Channel selector
                      const Text(
                        'Channel',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      SegmentedButton<MessageChannel>(
                        segments: const [
                          ButtonSegment(
                            value: MessageChannel.sms,
                            label: Text('SMS'),
                            icon: Icon(Icons.sms),
                          ),
                          ButtonSegment(
                            value: MessageChannel.whatsapp,
                            label: Text('WhatsApp'),
                            icon: Icon(Icons.chat),
                          ),
                          ButtonSegment(
                            value: MessageChannel.email,
                            label: Text('Email'),
                            icon: Icon(Icons.email),
                          ),
                        ],
                        selected: {_selectedChannel},
                        onSelectionChanged: (Set<MessageChannel> newSelection) {
                          setState(() {
                            _selectedChannel = newSelection.first;
                          });
                        },
                      ),
                      const SizedBox(height: 16),

                      // Schedule toggle
                      SwitchListTile(
                        title: const Text('Schedule for Later'),
                        subtitle: _scheduledDateTime != null
                            ? Text(_formatDateTime(_scheduledDateTime!))
                            : const Text('Send immediately'),
                        value: _isScheduled,
                        onChanged: (value) {
                          setState(() {
                            _isScheduled = value;
                            if (value && _scheduledDateTime == null) {
                              _selectScheduleDateTime();
                            }
                          });
                        },
                      ),

                      if (_isScheduled) ...[
                        const SizedBox(height: 8),
                        OutlinedButton.icon(
                          onPressed: _selectScheduleDateTime,
                          icon: const Icon(Icons.calendar_today),
                          label: Text(
                            _scheduledDateTime != null
                                ? 'Change Time: ${_formatDateTime(_scheduledDateTime!)}'
                                : 'Select Date & Time',
                          ),
                        ),
                      ],

                      const SizedBox(height: 16),
                      const Divider(),
                      const SizedBox(height: 8),

                      // Selected count
                      Text(
                        '${_selectedTenantIds.length} tenant(s) selected',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const Divider(height: 1),

              // Tenant list section
              Expanded(
                flex: 3,
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Select Tenants',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          if (_tenants.isNotEmpty)
                            TextButton(
                              onPressed: () {
                                setState(() {
                                  if (_selectedTenantIds.length ==
                                      _tenants.length) {
                                    _selectedTenantIds.clear();
                                  } else {
                                    _selectedTenantIds.addAll(
                                      _tenants.map((t) => t.id),
                                    );
                                  }
                                });
                              },
                              child: Text(
                                _selectedTenantIds.length == _tenants.length
                                    ? 'Deselect All'
                                    : 'Select All',
                              ),
                            ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: _buildTenantList(),
                    ),
                  ],
                ),
              ),

              // Loading overlay
              if (messageProvider.isLoading)
                Container(
                  color: Colors.black54,
                  child: const Center(
                    child: CircularProgressIndicator(),
                  ),
                ),
            ],
          ),
        ),
      );

  Widget _buildTenantList() {
    if (_isLoadingTenants) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_tenantError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              _tenantError!,
              style: const TextStyle(color: Colors.red),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadTenants,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_tenants.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.info_outline,
              size: 64,
              color: Colors.grey,
            ),
            SizedBox(height: 16),
            Text(
              'No tenants found',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            SizedBox(height: 8),
            Text(
              'Add tenants to send messages',
              style: TextStyle(fontSize: 14, color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: _tenants.length,
      itemBuilder: (context, index) {
        final tenant = _tenants[index];
        final isSelected = _selectedTenantIds.contains(tenant.id);

        return CheckboxListTile(
          title: Text(tenant.fullName),
          subtitle: Text(
            '${tenant.propertyName} - Unit ${tenant.unitNumber ?? 'N/A'}',
          ),
          secondary: CircleAvatar(
            child: Text(tenant.fullName[0].toUpperCase()),
          ),
          value: isSelected,
          onChanged: (value) {
            setState(() {
              if (value == true) {
                _selectedTenantIds.add(tenant.id);
              } else {
                _selectedTenantIds.remove(tenant.id);
              }
            });
          },
        );
      },
    );
  }
}
