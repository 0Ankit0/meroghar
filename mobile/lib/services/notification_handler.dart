/// Notification handler for deep linking and notification tap handling.
///
/// Implements T248 from tasks.md.
library;

import 'package:flutter/material.dart';

/// Notification handler for processing deep links
class NotificationHandler {
  /// Handle deep link navigation
  void handleDeepLink(BuildContext context, String deepLink) {
    if (!deepLink.startsWith('meroghar://')) {
      debugPrint('Invalid deep link format: $deepLink');
      return;
    }

    // Remove scheme
    final path = deepLink.replaceFirst('meroghar://', '');
    final segments = path.split('/');

    if (segments.isEmpty) {
      return;
    }

    final route = segments[0];
    final id = segments.length > 1 ? segments[1] : null;

    try {
      switch (route) {
        case 'payments':
          if (id != null) {
            Navigator.pushNamed(
              context,
              '/payment-details',
              arguments: {'paymentId': id},
            );
          } else {
            Navigator.pushNamed(context, '/payments');
          }
          break;

        case 'bills':
          if (id != null) {
            Navigator.pushNamed(
              context,
              '/bill-details',
              arguments: {'billId': id},
            );
          } else {
            Navigator.pushNamed(context, '/bills');
          }
          break;

        case 'documents':
          if (id != null) {
            Navigator.pushNamed(
              context,
              '/document-viewer',
              arguments: {'documentId': int.parse(id)},
            );
          } else {
            Navigator.pushNamed(context, '/documents');
          }
          break;

        case 'tenants':
          if (id != null) {
            Navigator.pushNamed(
              context,
              '/tenant-details',
              arguments: {'tenantId': id},
            );
          } else {
            Navigator.pushNamed(context, '/tenants');
          }
          break;

        case 'expenses':
          if (id != null) {
            Navigator.pushNamed(
              context,
              '/expense-details',
              arguments: {'expenseId': id},
            );
          } else {
            Navigator.pushNamed(context, '/expenses');
          }
          break;

        case 'messages':
          Navigator.pushNamed(context, '/messages');
          break;

        case 'properties':
          if (id != null) {
            Navigator.pushNamed(
              context,
              '/property-details',
              arguments: {'propertyId': id},
            );
          } else {
            Navigator.pushNamed(context, '/properties');
          }
          break;

        case 'settings':
          Navigator.pushNamed(context, '/settings');
          break;

        default:
          debugPrint('Unknown deep link route: $route');
          Navigator.pushNamed(context, '/home');
      }
    } catch (e) {
      debugPrint('Error handling deep link: $e');
      // Show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to open: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  /// Parse notification data from FCM message
  Map<String, dynamic> parseNotificationData(Map<String, dynamic> data) => {
        'notification_id': data['notification_id'],
        'type': data['type'],
        'priority': data['priority'],
        'deep_link': data['deep_link'],
        'metadata': data['metadata'],
      };
}
