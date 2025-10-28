/// Notification preferences screen with quiet hours configuration.
///
/// Implements T249 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  State<NotificationSettingsScreen> createState() =>
      _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState
    extends State<NotificationSettingsScreen> {
  bool _paymentNotifications = true;
  bool _billNotifications = true;
  bool _documentNotifications = true;
  bool _messageNotifications = true;
  bool _reminderNotifications = true;
  bool _quietHoursEnabled = false;
  TimeOfDay _quietHoursStart = const TimeOfDay(hour: 22, minute: 0);
  TimeOfDay _quietHoursEnd = const TimeOfDay(hour: 8, minute: 0);
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    setState(() => _isLoading = true);

    try {
      final prefs = await SharedPreferences.getInstance();

      setState(() {
        _paymentNotifications = prefs.getBool('notif_payment') ?? true;
        _billNotifications = prefs.getBool('notif_bill') ?? true;
        _documentNotifications = prefs.getBool('notif_document') ?? true;
        _messageNotifications = prefs.getBool('notif_message') ?? true;
        _reminderNotifications = prefs.getBool('notif_reminder') ?? true;
        _quietHoursEnabled =
            prefs.getBool('notif_quiet_hours_enabled') ?? false;

        final startHour = prefs.getInt('notif_quiet_start_hour') ?? 22;
        final startMinute = prefs.getInt('notif_quiet_start_minute') ?? 0;
        _quietHoursStart = TimeOfDay(hour: startHour, minute: startMinute);

        final endHour = prefs.getInt('notif_quiet_end_hour') ?? 8;
        final endMinute = prefs.getInt('notif_quiet_end_minute') ?? 0;
        _quietHoursEnd = TimeOfDay(hour: endHour, minute: endMinute);

        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading preferences: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _savePreferences() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      await prefs.setBool('notif_payment', _paymentNotifications);
      await prefs.setBool('notif_bill', _billNotifications);
      await prefs.setBool('notif_document', _documentNotifications);
      await prefs.setBool('notif_message', _messageNotifications);
      await prefs.setBool('notif_reminder', _reminderNotifications);
      await prefs.setBool('notif_quiet_hours_enabled', _quietHoursEnabled);
      await prefs.setInt('notif_quiet_start_hour', _quietHoursStart.hour);
      await prefs.setInt('notif_quiet_start_minute', _quietHoursStart.minute);
      await prefs.setInt('notif_quiet_end_hour', _quietHoursEnd.hour);
      await prefs.setInt('notif_quiet_end_minute', _quietHoursEnd.minute);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Notification preferences saved'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error saving preferences: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _selectQuietHoursStart() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _quietHoursStart,
    );

    if (picked != null) {
      setState(() => _quietHoursStart = picked);
      await _savePreferences();
    }
  }

  Future<void> _selectQuietHoursEnd() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _quietHoursEnd,
    );

    if (picked != null) {
      setState(() => _quietHoursEnd = picked);
      await _savePreferences();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Notification Settings'),
          elevation: 0,
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Info Card
                  Card(
                    color: Colors.blue.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(
                            Icons.info_outline,
                            color: Colors.blue.shade700,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Manage which notifications you want to receive and when.',
                              style: TextStyle(
                                color: Colors.blue.shade900,
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Notification Types
                  Text(
                    'Notification Types',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Card(
                    child: Column(
                      children: [
                        SwitchListTile(
                          title: const Text('Payment Notifications'),
                          subtitle: const Text(
                            'Receive alerts for payment confirmations and updates',
                          ),
                          value: _paymentNotifications,
                          onChanged: (value) {
                            setState(() => _paymentNotifications = value);
                            _savePreferences();
                          },
                          secondary: const Icon(Icons.payment),
                        ),
                        const Divider(height: 1),
                        SwitchListTile(
                          title: const Text('Bill Notifications'),
                          subtitle: const Text(
                            'Get notified about new bills and bill allocations',
                          ),
                          value: _billNotifications,
                          onChanged: (value) {
                            setState(() => _billNotifications = value);
                            _savePreferences();
                          },
                          secondary: const Icon(Icons.receipt_long),
                        ),
                        const Divider(height: 1),
                        SwitchListTile(
                          title: const Text('Document Notifications'),
                          subtitle: const Text(
                            'Receive alerts for document uploads and expirations',
                          ),
                          value: _documentNotifications,
                          onChanged: (value) {
                            setState(() => _documentNotifications = value);
                            _savePreferences();
                          },
                          secondary: const Icon(Icons.description),
                        ),
                        const Divider(height: 1),
                        SwitchListTile(
                          title: const Text('Message Notifications'),
                          subtitle: const Text(
                            'Get notified about new messages from owners/intermediaries',
                          ),
                          value: _messageNotifications,
                          onChanged: (value) {
                            setState(() => _messageNotifications = value);
                            _savePreferences();
                          },
                          secondary: const Icon(Icons.message),
                        ),
                        const Divider(height: 1),
                        SwitchListTile(
                          title: const Text('Reminder Notifications'),
                          subtitle: const Text(
                            'Receive reminders for due dates and deadlines',
                          ),
                          value: _reminderNotifications,
                          onChanged: (value) {
                            setState(() => _reminderNotifications = value);
                            _savePreferences();
                          },
                          secondary: const Icon(Icons.alarm),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Quiet Hours
                  Text(
                    'Quiet Hours',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Card(
                    child: Column(
                      children: [
                        SwitchListTile(
                          title: const Text('Enable Quiet Hours'),
                          subtitle: const Text(
                            'Mute notifications during specified hours',
                          ),
                          value: _quietHoursEnabled,
                          onChanged: (value) {
                            setState(() => _quietHoursEnabled = value);
                            _savePreferences();
                          },
                          secondary: const Icon(Icons.bedtime),
                        ),
                        if (_quietHoursEnabled) ...[
                          const Divider(height: 1),
                          ListTile(
                            leading: const Icon(Icons.nights_stay),
                            title: const Text('Start Time'),
                            subtitle: Text(_formatTimeOfDay(_quietHoursStart)),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: _selectQuietHoursStart,
                          ),
                          const Divider(height: 1),
                          ListTile(
                            leading: const Icon(Icons.wb_sunny),
                            title: const Text('End Time'),
                            subtitle: Text(_formatTimeOfDay(_quietHoursEnd)),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: _selectQuietHoursEnd,
                          ),
                          const Divider(height: 1),
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.grey.shade100,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                children: [
                                  const Icon(Icons.info_outline, size: 16),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      'Notifications will be muted from ${_formatTimeOfDay(_quietHoursStart)} to ${_formatTimeOfDay(_quietHoursEnd)}',
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Additional Options
                  Text(
                    'Additional Options',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 12),
                  Card(
                    child: Column(
                      children: [
                        ListTile(
                          leading: const Icon(Icons.notifications_active),
                          title: const Text('Test Notification'),
                          subtitle: const Text('Send a test notification'),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Test notification sent!'),
                                backgroundColor: Colors.green,
                              ),
                            );
                          },
                        ),
                        const Divider(height: 1),
                        ListTile(
                          leading: const Icon(Icons.settings),
                          title: const Text('System Notification Settings'),
                          subtitle:
                              const Text('Open device notification settings'),
                          trailing: const Icon(Icons.open_in_new),
                          onTap: () {
                            // This would open system settings in a real app
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'This would open your device notification settings',
                                ),
                              ),
                            );
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Reset Button
                  OutlinedButton.icon(
                    onPressed: () async {
                      final confirmed = await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Reset to Defaults'),
                          content: const Text(
                            'Are you sure you want to reset all notification preferences to default values?',
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(false),
                              child: const Text('Cancel'),
                            ),
                            ElevatedButton(
                              onPressed: () => Navigator.of(context).pop(true),
                              child: const Text('Reset'),
                            ),
                          ],
                        ),
                      );

                      if (confirmed == true) {
                        setState(() {
                          _paymentNotifications = true;
                          _billNotifications = true;
                          _documentNotifications = true;
                          _messageNotifications = true;
                          _reminderNotifications = true;
                          _quietHoursEnabled = false;
                          _quietHoursStart =
                              const TimeOfDay(hour: 22, minute: 0);
                          _quietHoursEnd = const TimeOfDay(hour: 8, minute: 0);
                        });
                        await _savePreferences();
                      }
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Reset to Defaults'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ],
              ),
      );

  String _formatTimeOfDay(TimeOfDay time) {
    final hour = time.hour.toString().padLeft(2, '0');
    final minute = time.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}
