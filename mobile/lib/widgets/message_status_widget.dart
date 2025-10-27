/// Message delivery status widget with visual indicators.
///
/// Implements T173 from tasks.md.
library;

import 'package:flutter/material.dart';

import '../models/message.dart';

class MessageStatusWidget extends StatelessWidget {
  final Message message;
  final bool showLabel;
  final double iconSize;

  const MessageStatusWidget({
    Key? key,
    required this.message,
    this.showLabel = false,
    this.iconSize = 24,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final statusInfo = _getStatusInfo();

    if (showLabel) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            statusInfo['icon'] as IconData,
            color: statusInfo['color'] as Color,
            size: iconSize,
          ),
          const SizedBox(width: 8),
          Text(
            statusInfo['label'] as String,
            style: TextStyle(
              color: statusInfo['color'] as Color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      );
    }

    return Tooltip(
      message: statusInfo['label'] as String,
      child: CircleAvatar(
        backgroundColor: (statusInfo['color'] as Color).withOpacity(0.1),
        child: Icon(
          statusInfo['icon'] as IconData,
          color: statusInfo['color'] as Color,
          size: iconSize * 0.7,
        ),
      ),
    );
  }

  Map<String, dynamic> _getStatusInfo() {
    switch (message.status) {
      case MessageStatus.pending:
        return {
          'icon': Icons.schedule,
          'color': Colors.orange,
          'label': 'Pending',
        };
      case MessageStatus.scheduled:
        return {
          'icon': Icons.event_available,
          'color': Colors.blue,
          'label': 'Scheduled',
        };
      case MessageStatus.sending:
        return {
          'icon': Icons.send,
          'color': Colors.blue,
          'label': 'Sending',
        };
      case MessageStatus.sent:
        return {
          'icon': Icons.done,
          'color': Colors.green,
          'label': 'Sent',
        };
      case MessageStatus.delivered:
        return {
          'icon': Icons.done_all,
          'color': Colors.green,
          'label': 'Delivered',
        };
      case MessageStatus.failed:
        return {
          'icon': Icons.error,
          'color': Colors.red,
          'label': 'Failed',
        };
      case MessageStatus.cancelled:
        return {
          'icon': Icons.cancel,
          'color': Colors.grey,
          'label': 'Cancelled',
        };
    }
  }
}
