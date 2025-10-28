/// Notification center screen displaying all notifications.
///
/// Implements T247 and T251 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../../models/notification.dart';
import '../../providers/notification_provider.dart';
import '../../services/notification_handler.dart';

class NotificationCenterScreen extends StatefulWidget {
  const NotificationCenterScreen({super.key});

  @override
  State<NotificationCenterScreen> createState() =>
      _NotificationCenterScreenState();
}

class _NotificationCenterScreenState extends State<NotificationCenterScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _showGrouped = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    // Fetch notifications on load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<NotificationProvider>().refresh();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Notifications'),
          actions: [
            IconButton(
              icon: Icon(_showGrouped ? Icons.list : Icons.category),
              onPressed: () {
                setState(() {
                  _showGrouped = !_showGrouped;
                });
              },
              tooltip: _showGrouped ? 'Show List' : 'Group by Type',
            ),
            IconButton(
              icon: const Icon(Icons.done_all),
              onPressed: () async {
                final provider = context.read<NotificationProvider>();
                await provider.markAllAsRead();
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('All notifications marked as read'),
                    ),
                  );
                }
              },
              tooltip: 'Mark all as read',
            ),
          ],
          bottom: TabBar(
            controller: _tabController,
            tabs: const [
              Tab(text: 'All'),
              Tab(text: 'Unread'),
            ],
          ),
        ),
        body: TabBarView(
          controller: _tabController,
          children: [
            _buildNotificationList(showUnreadOnly: false),
            _buildNotificationList(showUnreadOnly: true),
          ],
        ),
      );

  Widget _buildNotificationList({required bool showUnreadOnly}) =>
      Consumer<NotificationProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.notifications.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(provider.error!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.refresh(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final notifications = showUnreadOnly
              ? provider.unreadNotifications
              : provider.notifications;

          if (notifications.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    showUnreadOnly ? Icons.notifications_none : Icons.inbox,
                    size: 64,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    showUnreadOnly
                        ? 'No unread notifications'
                        : 'No notifications yet',
                    style: const TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: provider.refresh,
            child: _showGrouped
                ? _buildGroupedList(notifications)
                : _buildFlatList(notifications),
          );
        },
      );

  Widget _buildFlatList(List<AppNotification> notifications) {
    // Group by date
    final grouped = <String, List<AppNotification>>{};
    for (final notification in notifications) {
      final dateKey = _getDateKey(notification.createdAt);
      grouped.putIfAbsent(dateKey, () => []).add(notification);
    }

    return ListView.builder(
      itemCount: grouped.length,
      itemBuilder: (context, index) {
        final dateKey = grouped.keys.elementAt(index);
        final dateNotifications = grouped[dateKey]!;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                dateKey,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.grey,
                ),
              ),
            ),
            ...dateNotifications.map(_buildNotificationTile).toList(),
          ],
        );
      },
    );
  }

  Widget _buildGroupedList(List<AppNotification> notifications) {
    // Group by type
    final grouped = <NotificationType, List<AppNotification>>{};
    for (final notification in notifications) {
      grouped
          .putIfAbsent(notification.notificationType, () => [])
          .add(notification);
    }

    return ListView.builder(
      itemCount: grouped.length,
      itemBuilder: (context, index) {
        final type = grouped.keys.elementAt(index);
        final typeNotifications = grouped[type]!;

        return ExpansionTile(
          leading: _getTypeIcon(type),
          title: Text(type.displayName),
          subtitle: Text('${typeNotifications.length} notifications'),
          children: typeNotifications.map(_buildNotificationTile).toList(),
        );
      },
    );
  }

  Widget _buildNotificationTile(AppNotification notification) {
    final handler = NotificationHandler();

    return Dismissible(
      key: Key('notification_${notification.id}'),
      direction: DismissDirection.endToStart,
      background: Container(
        color: Colors.green,
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        child: const Icon(Icons.done, color: Colors.white),
      ),
      confirmDismiss: (direction) async {
        // Mark as read when swiped
        final provider = context.read<NotificationProvider>();
        return await provider.markAsRead([notification.id]);
      },
      child: ListTile(
        leading: _getTypeIcon(notification.notificationType),
        title: Text(
          notification.title,
          style: TextStyle(
            fontWeight:
                notification.isRead ? FontWeight.normal : FontWeight.bold,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(notification.body),
            const SizedBox(height: 4),
            Text(
              _formatTimestamp(notification.createdAt),
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        trailing: notification.isRead
            ? null
            : Container(
                width: 12,
                height: 12,
                decoration: const BoxDecoration(
                  color: Colors.blue,
                  shape: BoxShape.circle,
                ),
              ),
        onTap: () async {
          // Mark as read
          final provider = context.read<NotificationProvider>();
          await provider.markAsRead([notification.id]);

          // Handle deep link
          if (notification.deepLink != null && mounted) {
            handler.handleDeepLink(context, notification.deepLink!);
          }
        },
      ),
    );
  }

  Icon _getTypeIcon(NotificationType type) {
    IconData iconData;
    Color color;

    switch (type) {
      case NotificationType.paymentReceived:
        iconData = Icons.payments;
        color = Colors.green;
        break;
      case NotificationType.paymentOverdue:
        iconData = Icons.warning;
        color = Colors.red;
        break;
      case NotificationType.billCreated:
        iconData = Icons.receipt_long;
        color = Colors.orange;
        break;
      case NotificationType.billAllocated:
        iconData = Icons.receipt;
        color = Colors.blue;
        break;
      case NotificationType.documentUploaded:
        iconData = Icons.upload_file;
        color = Colors.purple;
        break;
      case NotificationType.documentExpiring:
        iconData = Icons.event_busy;
        color = Colors.orange;
        break;
      case NotificationType.rentIncrement:
        iconData = Icons.trending_up;
        color = Colors.amber;
        break;
      case NotificationType.messageReceived:
        iconData = Icons.message;
        color = Colors.blue;
        break;
      case NotificationType.expenseSubmitted:
        iconData = Icons.request_quote;
        color = Colors.teal;
        break;
      case NotificationType.expenseApproved:
        iconData = Icons.check_circle;
        color = Colors.green;
        break;
      case NotificationType.leaseExpiring:
        iconData = Icons.event_note;
        color = Colors.red;
        break;
      case NotificationType.maintenanceScheduled:
        iconData = Icons.build;
        color = Colors.indigo;
        break;
      case NotificationType.systemAnnouncement:
        iconData = Icons.campaign;
        color = Colors.grey;
        break;
    }

    return Icon(iconData, color: color);
  }

  String _getDateKey(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final notificationDate = DateTime(date.year, date.month, date.day);

    if (notificationDate == today) {
      return 'Today';
    } else if (notificationDate == yesterday) {
      return 'Yesterday';
    } else if (now.difference(notificationDate).inDays < 7) {
      return 'This Week';
    } else if (now.difference(notificationDate).inDays < 30) {
      return 'This Month';
    } else {
      return 'Earlier';
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return DateFormat('MMM d, y').format(timestamp);
    }
  }
}
