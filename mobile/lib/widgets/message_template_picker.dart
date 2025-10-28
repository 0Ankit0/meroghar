/// Message template picker widget.
///
/// Implements T171 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../models/message.dart';

class MessageTemplatePicker extends StatelessWidget {
  const MessageTemplatePicker({
    super.key,
    required this.selectedTemplate,
    required this.onTemplateSelected,
  });
  final MessageTemplate selectedTemplate;
  final Function(MessageTemplate) onTemplateSelected;

  String _getTemplateTitle(MessageTemplate template) {
    switch (template) {
      case MessageTemplate.paymentReminder:
        return 'Payment Reminder';
      case MessageTemplate.paymentOverdue:
        return 'Payment Overdue';
      case MessageTemplate.paymentReceived:
        return 'Payment Received';
      case MessageTemplate.leaseExpiring:
        return 'Lease Expiring';
      case MessageTemplate.maintenanceNotice:
        return 'Maintenance Notice';
      case MessageTemplate.custom:
        return 'Custom Message';
    }
  }

  String _getTemplateDescription(MessageTemplate template) {
    switch (template) {
      case MessageTemplate.paymentReminder:
        return 'Friendly reminder for upcoming rent payment';
      case MessageTemplate.paymentOverdue:
        return 'Urgent notice for overdue payment';
      case MessageTemplate.paymentReceived:
        return 'Thank you confirmation for payment received';
      case MessageTemplate.leaseExpiring:
        return 'Renewal notice for expiring lease';
      case MessageTemplate.maintenanceNotice:
        return 'Information about maintenance activities';
      case MessageTemplate.custom:
        return 'Write your own custom message';
    }
  }

  IconData _getTemplateIcon(MessageTemplate template) {
    switch (template) {
      case MessageTemplate.paymentReminder:
        return Icons.notifications;
      case MessageTemplate.paymentOverdue:
        return Icons.warning;
      case MessageTemplate.paymentReceived:
        return Icons.check_circle;
      case MessageTemplate.leaseExpiring:
        return Icons.calendar_today;
      case MessageTemplate.maintenanceNotice:
        return Icons.build;
      case MessageTemplate.custom:
        return Icons.edit;
    }
  }

  Color _getTemplateColor(MessageTemplate template) {
    switch (template) {
      case MessageTemplate.paymentReminder:
        return Colors.blue;
      case MessageTemplate.paymentOverdue:
        return Colors.red;
      case MessageTemplate.paymentReceived:
        return Colors.green;
      case MessageTemplate.leaseExpiring:
        return Colors.orange;
      case MessageTemplate.maintenanceNotice:
        return Colors.purple;
      case MessageTemplate.custom:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) => Card(
        elevation: 2,
        child: ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: MessageTemplate.values.length,
          itemBuilder: (context, index) {
            final template = MessageTemplate.values[index];
            final isSelected = template == selectedTemplate;

            return ListTile(
              leading: CircleAvatar(
                backgroundColor: _getTemplateColor(template).withOpacity(0.1),
                child: Icon(
                  _getTemplateIcon(template),
                  color: _getTemplateColor(template),
                ),
              ),
              title: Text(
                _getTemplateTitle(template),
                style: TextStyle(
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
              subtitle: Text(_getTemplateDescription(template)),
              trailing: isSelected
                  ? Icon(
                      Icons.check_circle,
                      color: _getTemplateColor(template),
                    )
                  : null,
              selected: isSelected,
              onTap: () => onTemplateSelected(template),
            );
          },
        ),
      );
}
